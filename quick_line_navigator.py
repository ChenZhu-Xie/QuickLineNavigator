import sublime
import sublime_plugin
import os
import re
import json
import time
import subprocess
import platform
import unicodedata
from collections import defaultdict

SETTINGS_FILE = "QuickLineNavigator.sublime-settings"
SUPPORTED_ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'utf-16', 'latin1', 'cp1252', 'shift_jis']
DEFAULT_BLACKLIST = ['.exe', '.dll', '.so', '.dylib', '.a', '.lib', '.obj', '.o', '.bin',
                     '.class', '.jar', '.war', '.ear', '.pyc', '.pyo', '.pyd',
                     '.db', '.sqlite', '.sqlite3', '.dat',
                     '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.ico', '.webp', '.svg',
                     '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm', '.wav', '.m4a',
                     '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                     '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz',
                     '.iso', '.img', '.dmg', '.deb', '.rpm', '.msi',
                     '.ttf', '.otf', '.woff', '.woff2', '.eot',
                     '.sublime-workspace', '.sublime-project',
                     '.git', '.svn', '.hg',
                     '.tmp', '.cache', '.log', '.swp', '.swo', '.swn', '.bak', '~']

HIGHLIGHT_SCOPES = ['region.redish', 'region.bluish', 'region.yellowish', 'region.greenish',
                    'region.purplish', 'region.orangish', 'selection']
HIGHLIGHT_ICONS = ['dot', 'circle', 'cross', 'bookmark', 'dot', 'circle', 'bookmark']
KEYWORD_EMOJIS = ['🟥', '🟦', '🟨', '🟩', '🟪', '🟧', '⬜']

# 简化的全局状态管理
class GlobalState:
    def __init__(self):
        self.active_panel = None
        self.stored_keywords = ""
        self.debug_enabled = True
        # Add the missing attributes
        self.is_esc_clearing = False
        self.is_programmatic_close = False
        self.is_switching = False
        self.is_panel_switching = False  # 添加这个新标记
    
    def handle_esc_clear(self):
        """处理 ESC 清空操作 - 简化版本"""
        self.debug_print("handle_esc_clear(): ESC pressed, clearing stored_keywords")
        self.stored_keywords = ""
        self.clear_active_panel()
    
    def reset_esc_flag(self):
        """重置 ESC 标记"""
        if self.is_esc_clearing:
            self.debug_print("reset_esc_flag(): Resetting ESC clearing flag")
            self.is_esc_clearing = False
        self.is_programmatic_close = False
        self.is_panel_switching = False  # 重置面板切换标记

    def debug_print(self, message):
        """调试输出函数"""
        if self.debug_enabled:
            print("🔍 [GlobalState Debug] {0}".format(message))
    
    def has_active_panel(self):
        """检查是否有活动的输入面板"""
        result = self.active_panel is not None
        self.debug_print("has_active_panel() -> {0}, active_panel: {1}".format(
            result, 
            self.active_panel.get('scope', 'None') if self.active_panel else 'None'
        ))
        return result
    
    def get_active_panel_text(self):
        """获取当前活动面板的文本"""
        if not self.active_panel or not self.active_panel.get('input_view'):
            self.debug_print("get_active_panel_text() -> '' (no active panel or input_view)")
            return ""
        
        input_view = self.active_panel['input_view']
        if input_view and input_view.is_valid():
            text = input_view.substr(sublime.Region(0, input_view.size()))
            self.debug_print("get_active_panel_text() -> '{0}'".format(text))
            return text
        
        self.debug_print("get_active_panel_text() -> '' (invalid input_view)")
        return ""
    
    def set_active_panel(self, panel_info):
        """设置活动面板"""
        old_scope = self.active_panel.get('scope', 'None') if self.active_panel else 'None'
        new_scope = panel_info.get('scope', 'None')
        
        self.active_panel = panel_info
        self.is_esc_clearing = False
        
        self.debug_print("set_active_panel(): {0} -> {1}".format(old_scope, new_scope))
    
    def clear_active_panel(self):
        """清除活动面板"""
        old_scope = self.active_panel.get('scope', 'None') if self.active_panel else 'None'
        self.active_panel = None
        self.debug_print("clear_active_panel(): {0} -> None".format(old_scope))
    
    def get_initial_text_for_new_panel(self, selected_text="", target_scope=""):
        """为新面板获取初始文本 - 简化版本"""
        self.debug_print("get_initial_text_for_new_panel(): selected_text='{0}', target_scope='{1}'".format(
            selected_text, target_scope
        ))
        
        # 有选中文本时，优先使用选中文本
        if selected_text:
            formatted_selected = TextUtils.format_keyword_for_input(selected_text)
            result = self.format_text_with_space(formatted_selected)
            self.debug_print("Using selected text: '{0}'".format(result))
            return result
        
        # 没有选中文本时，使用存储的关键词
        result = self.format_text_with_space(self.stored_keywords)
        self.debug_print("Using stored keywords: '{0}'".format(result))
        return result

    
    def save_current_keywords(self, text):
        """保存当前关键词 - 简化版本"""
        if text:
            old_keywords = self.stored_keywords
            self.stored_keywords = text
            self.debug_print("save_current_keywords(): '{0}' -> '{1}'".format(old_keywords, text))
        else:
            self.debug_print("save_current_keywords(): Not saving empty text")
    
    def should_append_space(self, text):
        """判断是否需要在末尾添加空格 - 规则 2.d"""
        if not text:
            self.debug_print("should_append_space(): No text -> False")
            return False
        
        # 如果已经以空格结尾，不需要添加
        if text.endswith(' '):
            self.debug_print("should_append_space(): Already ends with space -> False")
            return False
        
        # 如果没有关键词，不需要添加
        keywords = TextUtils.parse_keywords(text)
        if not keywords:
            self.debug_print("should_append_space(): No keywords found -> False")
            return False
        
        self.debug_print("should_append_space(): Has keywords and no trailing space -> True")
        return True
    
    def format_text_with_space(self, text):
        """格式化文本，根据规则 2.d 添加空格"""
        if self.should_append_space(text):
            result = text + ' '
            self.debug_print("format_text_with_space(): '{0}' -> '{1}' (space added)".format(text, result))
            return result
        
        self.debug_print("format_text_with_space(): '{0}' -> '{1}' (no space needed)".format(text, text))
        return text
    
    def handle_panel_append_selection(self, selected_text):
        """处理面板中追加选中文本 - 优先级 3.a"""
        if not self.has_active_panel():
            self.debug_print("handle_panel_append_selection(): No active panel")
            return None
        
        current_text = self.get_active_panel_text()
        formatted_selected = TextUtils.format_keyword_for_input(selected_text)
        
        # 检查是否已存在该关键词
        current_keywords = TextUtils.parse_keywords(current_text)
        if formatted_selected in current_keywords or selected_text in current_keywords:
            self.debug_print("handle_panel_append_selection(): Keyword already exists, not appending")
            return current_text
        
        # 构建新文本
        if current_text and not current_text.endswith(' '):
            new_text = "{0} {1}".format(current_text, formatted_selected)
        else:
            new_text = "{0}{1}".format(current_text, formatted_selected)
        
        result = self.format_text_with_space(new_text)
        self.debug_print("handle_panel_append_selection(): '{0}' + '{1}' -> '{2}'".format(
            current_text, selected_text, result
        ))
        return result

# 全局状态实例
global_state = GlobalState()


class Settings:
    def __init__(self):
        self._settings = sublime.load_settings(SETTINGS_FILE)
        self._cache = {}
    
    def get(self, key, default=None):
        if key not in self._cache:
            self._cache[key] = self._settings.get(key, default)
        return self._cache[key]
    
    def set(self, key, value):
        self._cache[key] = value
        self._settings.set(key, value)
        sublime.save_settings(SETTINGS_FILE)
    
    def update_user_settings(self, key, value):
        user_path = os.path.join(sublime.packages_path(), "User", SETTINGS_FILE)
        settings_data = {}
        
        if os.path.exists(user_path):
            try:
                with open(user_path, 'r', encoding='utf-8') as f:
                    settings_data = json.load(f)
            except:
                pass
        
        settings_data[key] = value
        
        os.makedirs(os.path.dirname(user_path), exist_ok=True)
        with open(user_path, 'w', encoding='utf-8') as f:
            json.dump(settings_data, f, indent=4, ensure_ascii=False)
        
        self.set(key, value)


class FileFilter:
    def __init__(self, settings, scope, window=None):
        self.settings = settings
        self.scope = scope
        self.window = window
        self.enabled = self._get_filter_enabled()
        self.whitelist = settings.get("file_extensions", [])
        self.blacklist = settings.get("file_extensions_blacklist", [])
    
    def _get_filter_enabled(self):
        if self.window and hasattr(self.window, 'extension_filters_temp_override'):
            return self.window.extension_filters_temp_override
        
        scope_map = {
            'file': 'extension_filters_file',
            'folder': 'extension_filters_folder',
            'project': 'extension_filters_project',
            'open_files': 'extension_filters_open_files'
        }
        
        if self.scope in scope_map:
            scope_setting = self.settings.get(scope_map[self.scope])
            if scope_setting is not None:
                return scope_setting
        
        return self.settings.get("extension_filters", True)
    
    def should_process(self, filename):
        if not filename:
            return False
        
        basename = os.path.basename(filename)
        _, ext = os.path.splitext(filename.lower())
        
        if ext in {'.git', '.svn', '.hg', '.sublime-workspace', '.sublime-project'} or basename.startswith('.'):
            return False
        
        if ext in DEFAULT_BLACKLIST:
            return False
        
        if not self.enabled:
            return True
        
        if self.blacklist:
            blacklist_set = {('.' + e.lstrip('.').lower() if e and e != '.' else e) for e in self.blacklist}
            if ext in blacklist_set:
                return False
        
        if not self.whitelist:
            return True
        
        allow_all = False
        allow_no_ext = False
        whitelist_set = set()
        
        for e in self.whitelist:
            e = e.strip().lower()
            if e == ".":
                allow_all = True
                break
            elif e == "":
                allow_no_ext = True
            else:
                whitelist_set.add('.' + e.lstrip('.'))
        
        if allow_all:
            return True
        
        if ext == "" and allow_no_ext:
            return True
        
        return ext in whitelist_set


class TextUtils:
    @staticmethod
    def display_width(s):
        width = 0
        for ch in s:
            if ('\U0001F300' <= ch <= '\U0001F9FF' or
                '\U0001F000' <= ch <= '\U0001F0FF' or
                '\U0001F100' <= ch <= '\U0001F1FF' or
                '\U0001F200' <= ch <= '\U0001F2FF' or
                '\U0001F600' <= ch <= '\U0001F64F' or
                '\U0001F680' <= ch <= '\U0001F6FF' or
                '\U0001F700' <= ch <= '\U0001F77F' or
                '\U00002600' <= ch <= '\U000027BF' or
                '\U0001FA00' <= ch <= '\U0001FA6F' or
                '\U0001FA70' <= ch <= '\U0001FAFF'):
                width += 2
            else:
                ea_width = unicodedata.east_asian_width(ch)
                width += 2 if ea_width in ('F', 'W', 'A') else 1
        return width
    
    @staticmethod
    def parse_keywords(input_text):
        """解析关键词，只有反引号是分界符，其他引号都是普通字符"""
        if not input_text:
            return []
        
        keywords = []
        current = ""
        in_backticks = False
        
        i = 0
        while i < len(input_text):
            char = input_text[i]
            
            if char == '`' and not in_backticks:
                if current.strip():
                    keywords.append(current.strip())
                    current = ""
                
                in_backticks = True
                i += 1
                continue
                
            elif char == '`' and in_backticks:
                in_backticks = False
                if current.strip():
                    keywords.append(current.strip())
                current = ""
                i += 1
                continue
            
            elif char == ' ' and not in_backticks:
                if current.strip():
                    keywords.append(current.strip())
                current = ""
                i += 1
                continue
            
            else:
                current += char
                i += 1
        
        if current.strip():
            keywords.append(current.strip())
        
        final_keywords = []
        for kw in keywords:
            if kw and ('\r' in kw or '\n' in kw):
                lines = kw.replace('\r\n', '\n').replace('\r', '\n').split('\n')
                for line in lines:
                    line = line.strip()
                    if line:  
                        final_keywords.append(line)
            elif kw:
                final_keywords.append(kw)
        
        return final_keywords
    
    @staticmethod
    def format_keyword_for_input(keyword):
        """格式化关键词以便在输入框中使用"""
        if '`' in keyword:
            return '"{}"'.format(keyword)
        elif ' ' in keyword or "'" in keyword:
            return '`{}`'.format(keyword)
        return keyword


class UgrepExecutor:
    def __init__(self):
        self.path = self._find_executable()
        self.output_pattern = re.compile(r'^([^:]+):(\d+):(.*)$')
        self.windows_pattern = re.compile(r'^([A-Za-z]:[^:]+):(\d+):(.*)$')
    
    def _find_executable(self):
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        system = platform.system().lower()
        
        if system == "windows":
            paths = [
                os.path.join(plugin_dir, "bin", "ugrep.exe"),
                os.path.join(plugin_dir, "ugrep.exe"),
                "ugrep.exe"
            ]
        elif system == "darwin":
            paths = [
                os.path.join(plugin_dir, "bin", "ugrep_mac"),
                os.path.join(plugin_dir, "bin", "ugrep"),
                os.path.join(plugin_dir, "ugrep_mac"),
                os.path.join(plugin_dir, "ugrep"),
                "ugrep"
            ]
        else:
            paths = [
                os.path.join(plugin_dir, "bin", "ugrep"),
                os.path.join(plugin_dir, "ugrep"),
                "ugrep"
            ]
        
        for path in paths:
            try:
                if os.path.sep not in path and not os.path.isabs(path):
                    import shutil
                    found = shutil.which(path)
                    if found:
                        return found
                elif os.path.exists(path) and os.path.isfile(path):
                    if system != "windows" and not os.access(path, os.X_OK):
                        try:
                            os.chmod(path, 0o755)
                        except:
                            continue
                    return path
            except:
                continue
        return None
    
    def search(self, paths, keywords, file_filter):
        if not self.path:
            return []
        
        cmd = [self.path, "-n", "-H", "--color=never", "-r", "-I", "-i", "-F"]
        
        if not file_filter.enabled:
            critical_blacklist = ["*.sublime-workspace", "*.sublime-project", "*.git", "*.svn", "*.hg",
                                "*.exe", "*.dll", "*.so", "*.dylib", "*.bin"]
            for pattern in critical_blacklist:
                cmd.extend(["--exclude", pattern])
        else:
            self._apply_filters(cmd, file_filter)
        
        if not keywords:
            cmd.remove("-F")
            cmd.extend(["-e", r"^\s*\S"])
        else:
            self._add_keywords(cmd, keywords)
        
        cmd.extend(paths if isinstance(paths, list) else [paths])
        
        print("  🔧 Ugrep: {0}".format(" ".join(str(arg) for arg in cmd)))
        
        output, error = self._execute(cmd)
        if error:
            print("  ❌ Ugrep error: {0}".format(error))
        
        results = self._parse_output(output)
        print("  ✅ Ugrep found {0} lines".format(len(results)))
        
        if file_filter.enabled and self._needs_post_filter(file_filter):
            results = self._post_filter(results, file_filter)
            print("  🔧 Post-filtered to {0} lines".format(len(results)))
        
        return results

    def _add_keywords(self, cmd, keywords):
        keywords = [kw for kw in keywords if kw]
        if len(keywords) == 1:
            cmd.append(keywords[0])
        else:
            for kw in keywords:
                cmd.extend(["--and", "-e", kw])
    
    def _apply_filters(self, cmd, file_filter):
        applied_whitelist = False
        
        if file_filter.whitelist:
            allow_all = False
            allow_no_ext = False
            valid_exts = []
            
            for ext in file_filter.whitelist:
                ext = ext.strip().lower()
                if ext == ".":
                    allow_all = True
                    break
                elif ext == "":
                    allow_no_ext = True
                else:
                    valid_exts.append("*{0}".format('.' + ext.lstrip('.')))
            
            if not allow_all and valid_exts and not allow_no_ext:
                for pattern in valid_exts:
                    cmd.extend(["--include", pattern])
                applied_whitelist = True
        
        blacklist = set()
        if not applied_whitelist:
            blacklist.update(["*{0}".format(ext) for ext in DEFAULT_BLACKLIST])
        
        if file_filter.blacklist:
            for ext in file_filter.blacklist:
                ext = ext.strip().lower()
                if ext and ext != ".":
                    blacklist.add("*{0}".format('.' + ext.lstrip('.')))
        
        for pattern in blacklist:
            cmd.extend(["--exclude", pattern])
    
    def _execute(self, cmd):
        try:
            kwargs = {}
            if platform.system() == "Windows":
                if hasattr(subprocess, 'CREATE_NO_WINDOW'):
                    kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                else:
                    kwargs['creationflags'] = 0x08000000
            
            if hasattr(subprocess, 'run'):
                result = subprocess.run(cmd, capture_output=True, text=True, 
                                      encoding='utf-8', errors='ignore', timeout=30, **kwargs)
                return result.stdout, result.stderr
            else:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                         universal_newlines=True, **kwargs)
                stdout, stderr = process.communicate(timeout=30)
                
                if isinstance(stdout, bytes):
                    stdout = stdout.decode('utf-8', errors='ignore')
                if isinstance(stderr, bytes):
                    stderr = stderr.decode('utf-8', errors='ignore')
                
                return stdout, stderr
                
        except subprocess.TimeoutExpired:
            if 'process' in locals():
                process.kill()
                process.communicate()
            return "", "Timeout after 30 seconds"
        except OSError as e:
            if e.errno == 2:
                return "", "ugrep not found"
            elif e.errno == 13:
                return "", "Permission denied"
            else:
                return "", "System error: {0}".format(str(e))
        except Exception as e:
            return "", "Error: {0}".format(str(e))

    def _parse_output(self, output):
        results = []
        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue
            
            match = self.output_pattern.match(line) or self.windows_pattern.match(line)
            if match:
                results.append({
                    'file': match.group(1),
                    'line_number': int(match.group(2)),
                    'line': match.group(3),
                    'display': match.group(3).strip(),
                    'point': int(match.group(2))
                })
        return results
    
    def _needs_post_filter(self, file_filter):
        if file_filter.whitelist:
            has_empty = any(ext.strip() == "" for ext in file_filter.whitelist)
            has_others = any(ext.strip() != "" and ext.strip() != "." for ext in file_filter.whitelist)
            return has_empty and has_others
        return False
    
    def _post_filter(self, results, file_filter):
        filtered = []
        for item in results:
            filename = item.get('file', '')
            _, ext = os.path.splitext(filename)
            if ext == "" or file_filter.should_process(filename):
                filtered.append(item)
        return filtered


class SearchEngine:
    def __init__(self, settings, scope, window=None):
        self.settings = settings
        self.scope = scope
        self.window = window
        self.file_filter = FileFilter(settings, scope, window)
        self.ugrep = UgrepExecutor()
    
    def search(self, paths, keywords, original_keywords=""):
        if not paths:
            return []
        
        start_time = time.time()
        
        if self.ugrep.path:
            results = self.ugrep.search(paths, keywords, self.file_filter)
        else:
            results = self._python_search(paths, keywords)
        
        duration = time.time() - start_time
        self._print_stats(len(results), paths, keywords, original_keywords, duration)
        
        return results
    
    def _python_search(self, paths, keywords):
        if self.scope == "file":
            return self._search_file(paths[0], keywords)
        elif self.scope == "open_files":
            return self._search_open_files(paths, keywords)
        else:
            return self._search_folders(paths, keywords)
    
    def _search_file(self, file_path, keywords):
        if not self.window:
            return []
        
        view = None
        for v in self.window.views():
            if v.file_name() == file_path:
                view = v
                break
        
        if not view:
            return []
        
        results = []
        for region in view.lines(sublime.Region(0, view.size())):
            line_text = view.substr(region)
            display_text = line_text.strip()
            if not display_text:
                continue
            
            if keywords:
                if not all(re.search(re.escape(kw), display_text, re.IGNORECASE) for kw in keywords):
                    continue
            
            line_num = view.rowcol(region.begin())[0] + 1
            results.append({
                'file': file_path,
                'line_number': line_num,
                'line': line_text,
                'display': display_text,
                'point': region.begin()
            })
        
        return results
    
    def _search_open_files(self, file_paths, keywords):
        if not self.window:
            return []
        
        results = []
        for file_path in file_paths:
            results.extend(self._search_file(file_path, keywords))
        
        return results
    
    def _search_folders(self, folders, keywords):
        all_files = []
        for folder in folders:
            try:
                for root, dirs, files in os.walk(folder):
                    for fname in files:
                        fpath = os.path.join(root, fname)
                        if os.path.isfile(fpath) and self.file_filter.should_process(fpath):
                            all_files.append(fpath)
            except:
                continue
        
        results = []
        for file_path in all_files:
            try:
                if os.path.getsize(file_path) > 10 * 1024 * 1024:
                    continue
                
                lines = []
                with open(file_path, 'rb') as f:
                    raw_content = f.read(10 * 1024 * 1024)
                
                for encoding in SUPPORTED_ENCODINGS:
                    try:
                        text = raw_content.decode(encoding)
                        lines = text.splitlines()
                        break
                    except:
                        continue
                
                for line_num, line in enumerate(lines[:10000], 1):
                    display_text = line.strip()
                    if not display_text:
                        continue
                    
                    if keywords:
                        if not all(re.search(re.escape(kw), display_text, re.IGNORECASE) for kw in keywords):
                            continue
                    
                    results.append({
                        'file': file_path,
                        'line_number': line_num,
                        'line': line,
                        'display': display_text,
                        'point': line_num
                    })
            except:
                continue
        
        return results
    
    def _print_stats(self, results_count, paths, keywords, original, duration):
        scope_name = UIText.get_scope_display_name(self.scope)
        print("🎯 {0} Search Complete".format(scope_name))
        
        if keywords:
            keyword_display = []
            for i, kw in enumerate(keywords):
                emoji = KEYWORD_EMOJIS[i % len(KEYWORD_EMOJIS)]
                keyword_display.append("{0}{1}".format(emoji, kw))
            print("  📍 Keywords: {0}".format(" ".join(keyword_display)))
        else:
            print("  📍 Keywords: {0}".format(original or "All lines"))
        
        if self.scope in ["folder", "project"]:
            print("  📁 Folders: {0}".format(len(paths)))
        elif self.scope == "file":
            print("  📄 File: {0}".format(os.path.basename(paths[0]) if paths else "Unknown"))
        elif self.scope == "open_files":
            print("  📊 Files: {0}".format(len(paths)))
        
        print("  📝 Results: {0} lines".format(results_count))
        print("  ⏱️ Time: {0:.3f}s".format(duration))


class Highlighter:
    def __init__(self):
        self.keys = set()
        self.key_base = "QuickLineNavKeyword"
        self.views = set()
        self.cache = {}
    
    def highlight(self, view, keywords):
        if not view or not view.is_valid():
            return
        
        keywords = [kw for kw in keywords if kw and kw.strip()]
        if not keywords:
            self.clear(view)
            return
        
        view_id = view.id()
        
        cache_key = tuple(keywords)
        if self.cache.get(view_id) == cache_key:
            return
        
        if view.is_loading() or view.size() == 0:
            sublime.set_timeout(lambda: self.highlight(view, keywords), 100)
            return
        
        self.clear(view)
        
        for i, keyword in enumerate(keywords):
            if not keyword:
                continue
            
            try:
                regions = view.find_all(keyword, sublime.IGNORECASE | sublime.LITERAL)
                
                if regions:
                    key = "{0}_{1}_{2}".format(self.key_base, view_id, i)
                    self.keys.add(key)
                    
                    scope = HIGHLIGHT_SCOPES[i % len(HIGHLIGHT_SCOPES)]
                    icon = HIGHLIGHT_ICONS[i % len(HIGHLIGHT_ICONS)]
                    
                    view.add_regions(key, regions, scope, icon, sublime.PERSISTENT | sublime.DRAW_NO_OUTLINE)
            except Exception as e:
                print("Error highlighting keyword '{}': {}".format(keyword, e))
                continue
        
        if self.keys:
            self.views.add(view_id)
            self.cache[view_id] = cache_key

    
    def highlight_scope(self, scope, keywords, window, results=None):
        if not keywords:
            return
        
        if scope in ['file', 'current_file']:
            view = window.active_view()
            if view:
                self.highlight(view, keywords)
        
        elif scope == 'open_files':
            for view in window.views():
                if view and view.is_valid():
                    self.highlight(view, keywords)
        
        elif scope in ['folder', 'project'] and results:
            files = {item['file'] for item in results if 'file' in item}
            for file_path in files:
                view = None
                for v in window.views():
                    if v.file_name() == file_path:
                        view = v
                        break
                
                if not view:
                    view = window.open_file(file_path, sublime.TRANSIENT)
                
                if view:
                    def highlight_when_ready():
                        if view.is_loading():
                            sublime.set_timeout(highlight_when_ready, 50)
                        else:
                            self.highlight(view, keywords)
                    
                    highlight_when_ready()
    
    def clear(self, view):
        if not view or not view.is_valid():
            return
        
        view_id = view.id()
        self.cache.pop(view_id, None)
        
        keys_to_remove = {key for key in self.keys if "_{0}_".format(view_id) in key}
        
        for key in keys_to_remove:
            try:
                view.erase_regions(key)
            except:
                pass
        
        self.keys.difference_update(keys_to_remove)
        self.views.discard(view_id)
    
    def clear_all(self):
        for window in sublime.windows():
            for view in window.views():
                if view.id() in self.views:
                    self.clear(view)
        
        self.keys.clear()
        self.views.clear()
        self.cache.clear()


class DisplayFormatter:
    def __init__(self, settings):
        self.settings = settings
        self.show_line_numbers = settings.get("show_line_numbers", True)
        self.max_length = settings.get("max_display_length", 120)
    
    def format_results(self, results, keywords, scope):
        formatted = []
        expanded_results = []
        
        for i, item in enumerate(results):
            full_line_with_emojis = self._format_main_line(item['line'], keywords)
            segments = self._split_into_segments(full_line_with_emojis, item['line'], keywords)
            
            for seg_index, segment in enumerate(segments):
                main_line = segment['display']
                sub_line = self._format_sub_line(item, i, scope, seg_index, len(segments))
                formatted.append([main_line, sub_line])
                expanded_item = item.copy()
                expanded_item['segment_start'] = segment['start']
                expanded_item['segment_end'] = segment['end']
                expanded_item['segment_index'] = seg_index
                expanded_item['total_segments'] = len(segments)
                expanded_results.append(expanded_item)
        
        return formatted, expanded_results
    
    def _format_main_line(self, line, keywords):
        if not keywords:
            return line.strip()
        line_stripped = line.strip()
        line_lower = line_stripped.lower()
        keyword_emoji_map = {}
        for i, keyword in enumerate(keywords):
            keyword_emoji_map[keyword.lower()] = KEYWORD_EMOJIS[i % len(KEYWORD_EMOJIS)]
        all_positions = []
        for keyword in keywords:
            keyword_lower = keyword.lower()
            emoji = keyword_emoji_map[keyword_lower]
            pos = 0
            while True:
                index = line_lower.find(keyword_lower, pos)
                if index == -1:
                    break
                all_positions.append((index, len(keyword), emoji))
                pos = index + 1
        if not all_positions:
            return line_stripped
        all_positions.sort(key=lambda x: x[0], reverse=True)
        result = line_stripped
        for pos, length, emoji in all_positions:
            result = result[:pos] + emoji + result[pos:]
        
        return result
    
    def _split_into_segments(self, line_with_emojis, original_line, keywords):
        segments = []
        original_stripped = original_line.strip()
        if TextUtils.display_width(line_with_emojis) <= self.max_length:
            segments.append({
                'display': line_with_emojis,
                'start': 0,
                'end': len(original_stripped)
            })
            return segments
        emoji_keyword_ranges = self._find_emoji_keyword_ranges(line_with_emojis, keywords)
        current_pos = 0
        while current_pos < len(line_with_emojis):
            segment_end = self._find_safe_cut_position(
                line_with_emojis, current_pos, self.max_length, emoji_keyword_ranges
            )
            
            if segment_end <= current_pos:
                segment_end = current_pos + 1
            
            segment_text = line_with_emojis[current_pos:segment_end]
            orig_start = self._map_to_original_position(current_pos, line_with_emojis, original_stripped, keywords)
            orig_end = self._map_to_original_position(segment_end, line_with_emojis, original_stripped, keywords)
            
            segments.append({
                'display': segment_text,
                'start': orig_start,
                'end': orig_end
            })
            
            current_pos = segment_end
        
        return segments

    def _find_emoji_keyword_ranges(self, line_with_emojis, keywords):
        ranges = []
        line_lower = line_with_emojis.lower()
        keyword_emoji_map = {}
        for i, keyword in enumerate(keywords):
            keyword_emoji_map[keyword.lower()] = KEYWORD_EMOJIS[i % len(KEYWORD_EMOJIS)]
        for keyword in keywords:
            keyword_lower = keyword.lower()
            emoji = keyword_emoji_map[keyword_lower]
            pattern = emoji + keyword_lower
            
            pos = 0
            while True:
                found_pos = line_lower.find(pattern.lower(), pos)
                if found_pos == -1:
                    break
                ranges.append((found_pos, found_pos + len(pattern)))
                pos = found_pos + 1
        ranges.sort()
        return ranges

    def _find_safe_cut_position(self, text, start_pos, max_width, emoji_keyword_ranges):
        if start_pos >= len(text):
            return len(text)
        ideal_end = start_pos
        current_width = 0
        
        while ideal_end < len(text) and current_width < max_width:
            char = text[ideal_end]
            char_width = TextUtils.display_width(char)
            if current_width + char_width > max_width:
                break
            current_width += char_width
            ideal_end += 1
        safe_end = ideal_end
        for range_start, range_end in emoji_keyword_ranges:
            if range_start < ideal_end < range_end:
                if range_start >= start_pos:
                    safe_end = min(safe_end, range_start)
                else:
                    safe_end = range_end
                    break
        if safe_end <= start_pos:
            for range_start, range_end in emoji_keyword_ranges:
                if range_start > start_pos:
                    safe_end = range_end
                    break
            if safe_end <= start_pos and emoji_keyword_ranges:
                next_safe = start_pos + 1
                for range_start, range_end in emoji_keyword_ranges:
                    if range_start >= start_pos:
                        next_safe = range_end
                        break
                safe_end = min(next_safe, len(text))
            elif safe_end <= start_pos:
                safe_end = min(start_pos + 10, len(text))
        
        return min(safe_end, len(text))

    def _map_to_original_position(self, pos_in_modified, line_with_emojis, original_line, keywords):
        if pos_in_modified <= 0:
            return 0
        if pos_in_modified >= len(line_with_emojis):
            return len(original_line.strip())
        emoji_count = 0
        modified_pos = 0
        original_lower = original_line.strip().lower()
        keyword_emoji_map = {}
        for i, keyword in enumerate(keywords):
            keyword_emoji_map[keyword.lower()] = KEYWORD_EMOJIS[i % len(KEYWORD_EMOJIS)]
        original_pos = 0
        while original_pos < len(original_lower) and modified_pos < pos_in_modified:
            emoji_inserted = False
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if (original_pos + len(keyword_lower) <= len(original_lower) and
                    original_lower[original_pos:original_pos + len(keyword_lower)] == keyword_lower):
                    if modified_pos < pos_in_modified:
                        emoji_count += 1
                        modified_pos += 1
                        emoji_inserted = True
                    break
            if modified_pos < pos_in_modified:
                modified_pos += 1
            original_pos += 1
            
            if emoji_inserted:
                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    if (original_pos <= len(original_lower) - len(keyword_lower) and
                        original_lower[original_pos:original_pos + len(keyword_lower)] == keyword_lower):
                        original_pos += len(keyword_lower) - 1
                        modified_pos += len(keyword_lower) - 1
                        break
        result = max(0, min(pos_in_modified - emoji_count, len(original_line.strip())))
        return result
    
    def _format_sub_line(self, item, index, scope, segment_index=0, total_segments=1):
        parts = []
        
        if self.show_line_numbers and 'line_number' in item:
            parts.append(str(item['line_number']))
        
        parts.append("⚡ {0}".format(index + 1))
        if total_segments > 1:
            parts.append("📍 {0}/{1}".format(segment_index + 1, total_segments))
        
        if 'file' in item and scope != 'file':
            filename = os.path.basename(item['file'])
            if len(filename) > 50:
                filename = filename[:47] + "..."
            parts.append("📄 {0}".format(filename))
        
        return "☲ " + " ".join(parts)


class BaseQuickLineNavigatorCommand(sublime_plugin.WindowCommand):
    """基础搜索命令类，处理共同的搜索逻辑"""
    
    def __init__(self, window):
        super().__init__(window)
        self.current_segment_key = None
        self.highlighted_view_id = None
        self.input_view = None
        self.settings = Settings()
        self.original_keywords = ""
        self.scope = None
        self._border_timer_id = 0
    
    def get_initial_text(self):
        """获取初始文本 - 使用重构后的逻辑"""
        selected_text = self.get_selected_text()
        return global_state.get_initial_text_for_new_panel(selected_text, self.scope)
    
    def get_selected_text(self):
        """获取选中文本"""
        view = self.window.active_view()
        if view:
            for sel in view.sel():
                if not sel.empty():
                    return view.substr(sel)
        return ""
    
    def setup_input_panel(self, initial_text):
        """设置输入面板"""
        global_state.debug_print("setup_input_panel(): scope='{0}', initial_text='{1}'".format(
            self.scope, initial_text
        ))
        
        # 创建输入面板
        self.input_view = self.window.show_input_panel(
            UIText.get_search_prompt(self.scope),
            initial_text,
            self.on_done,
            self.on_change,
            self.on_cancel
        )
        
        # 设置活动面板信息
        global_state.set_active_panel({
            'scope': self.scope,
            'input_view': self.input_view,
            'command_instance': self
        })
        
        # 将光标移到末尾 - 规则 2.e
        if self.input_view:
            self.input_view.sel().clear()
            end_point = self.input_view.size()
            self.input_view.sel().add(sublime.Region(end_point, end_point))
            global_state.debug_print("setup_input_panel(): Cursor moved to end position {0}".format(end_point))
    
    def handle_selection_append(self):
        """处理选中文本追加到输入框 - 优先级 3.a"""
        if not self.input_view or not self.input_view.is_valid():
            global_state.debug_print("handle_selection_append(): Invalid input view")
            return
        
        selected_text = self.get_selected_text()
        if not selected_text:
            global_state.debug_print("handle_selection_append(): No selected text")
            return
        
        new_text = global_state.handle_panel_append_selection(selected_text)
        if new_text is None:
            return
        
        # 更新输入框
        self.input_view.run_command("select_all")
        self.input_view.run_command("insert", {"characters": new_text})
        
        # 将光标移到末尾 - 规则 2.e
        self.input_view.sel().clear()
        end_point = self.input_view.size()
        self.input_view.sel().add(sublime.Region(end_point, end_point))
        
        # 确保输入框获得焦点 - 规则 2.c
        self.window.focus_view(self.input_view)
        global_state.debug_print("handle_selection_append(): Focus set to input panel")
    
    def on_cancel(self):
        """取消时的处理 - 支持面板切换检测"""
        global_state.debug_print("on_cancel(): Called, is_panel_switching={0}".format(
            global_state.is_panel_switching
        ))
        
        # 如果是面板切换导致的取消，不清空关键词
        if global_state.is_panel_switching:
            global_state.debug_print("on_cancel(): Panel switching detected, not clearing keywords")
            self.clear_highlights()
            return
        
        # 只有当前确实有活动面板时才清空关键词（真正的 ESC）
        if global_state.has_active_panel():
            global_state.debug_print("on_cancel(): ESC pressed with active panel, clearing keywords")
            global_state.handle_esc_clear()
        else:
            global_state.debug_print("on_cancel(): No active panel, likely from automatic panel closure")
        
        self.clear_highlights()


    
    def on_change(self, input_text):
        """输入改变时的处理 - 简化版本"""
        global_state.debug_print("on_change(): input_text='{0}'".format(input_text))
        
        # 总是保存当前输入
        global_state.save_current_keywords(input_text)
        
        if self.settings.get("preview_on_highlight", True):
            if not input_text or not input_text.strip():
                self.clear_highlights()
                return
            
            keywords = TextUtils.parse_keywords(input_text)
            if keywords:
                self.highlight_keywords(keywords)
            else:
                self.clear_highlights()

    
    def on_done(self, input_text):
        """完成时的处理 - 子类必须实现并调用 process_search_done"""
        raise NotImplementedError
    
    def process_search_done(self, input_text, results):
        """处理搜索完成的通用逻辑 - 简化版本"""
        keywords = TextUtils.parse_keywords(input_text) if input_text else []
        
        # 保存关键词
        global_state.save_current_keywords(input_text)
        
        # 清除活动面板
        global_state.clear_active_panel()
        
        if not results:
            # 无结果时重新显示输入框
            sublime.status_message(UIText.get_status_message('no_results_in_scope', scope=self.scope))
            self.setup_input_panel(input_text)
            return False
        
        # 有结果时复制关键词到剪贴板
        if keywords:
            formatted_keywords = []
            for kw in keywords:
                formatted_keywords.append(TextUtils.format_keyword_for_input(kw))
            keywords_text = ' '.join(formatted_keywords)
            sublime.set_clipboard(keywords_text)
        
        return True


    
    def _show_results(self, results, keywords):
        """显示搜索结果"""
        ResultsDisplayHandler.show_results(
            self.window, results, keywords, self.scope,
            self.on_done, self.on_change, self.on_cancel,
            self._highlight_segment,
            command_instance=self
        )
    
    def _highlight_segment(self, view, item, line_number):
        """高亮显示段落"""
        if 'segment_start' not in item or 'segment_end' not in item:
            return
        
        current_file = item.get('file', '')
        current_line_number = item.get('line_number', -1)
        new_line_key = (current_file, current_line_number)
        
        if not hasattr(self, '_last_highlighted_line'):
            self._last_highlighted_line = None
        
        is_new_line = self._last_highlighted_line != new_line_key
        
        if self.current_segment_key and self.highlighted_view_id:
            for window in sublime.windows():
                for v in window.views():
                    if v.id() == self.highlighted_view_id:
                        v.erase_regions(self.current_segment_key)
                        if is_new_line:
                            v.erase_regions(self.current_segment_key + "_border")
                        break
        
        line_region = view.line(view.text_point(line_number, 0))
        line_start = line_region.begin()
        line_text = view.substr(line_region)
        indent_amount = len(line_text) - len(line_text.lstrip())
        
        segment_start = line_start + indent_amount + item['segment_start']
        segment_end = line_start + indent_amount + item['segment_end']
        segment_region = sublime.Region(segment_start, segment_end)
        
        key = "QuickLineNavSegment_{0}".format(view.id())
        self.current_segment_key = key
        self.highlighted_view_id = view.id()
        
        view.add_regions(
            key,
            [segment_region],
            "region.whitish",
            "",
            sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE | sublime.DRAW_SOLID_UNDERLINE
        )
        
        total_segments = item.get('total_segments', 1)
        if total_segments > 1 and is_new_line:
            self._last_highlighted_line = new_line_key
            
            border_key = key + "_border"
            
            self._border_timer_id += 1
            current_timer_id = self._border_timer_id
            
            view.add_regions(
                border_key,
                [line_region],
                "region.grayish",
                "",
                sublime.DRAW_NO_FILL | sublime.DRAW_EMPTY
            )
            
            def clear_border():
                if current_timer_id == self._border_timer_id and view and view.is_valid():
                    try:
                        view.erase_regions(border_key)
                    except:
                        pass
            
            sublime.set_timeout(clear_border, 1000)
        
        if is_new_line:
            self._last_highlighted_line = new_line_key
        
        view.show(segment_region, True)
    
    def handle_quick_panel_cancel(self, formatted_keywords):
        """处理 quick panel 取消的情况"""
        # 保存格式化的关键词
        global_state.save_current_keywords(formatted_keywords)
        
        # 标记为切换（防止清除关键词）
        global_state.is_switching = True
        
        # 重新显示输入面板
        self.setup_input_panel(formatted_keywords)
        
        sublime.set_timeout(lambda: setattr(global_state, 'is_switching', False), 100)
    
    def clear_highlights(self):
        """清除高亮 - 子类实现"""
        raise NotImplementedError
    
    def highlight_keywords(self, keywords):
        """高亮关键词 - 子类实现"""
        raise NotImplementedError


class ResultsDisplayHandler:
    """处理搜索结果显示的通用类"""
    
    @staticmethod
    def show_results(window, results, keywords, scope, on_done_callback, on_change_callback, 
        on_cancel_callback, highlight_segment_callback, command_instance=None):
        """显示搜索结果"""
        formatter = DisplayFormatter(Settings())
        items, expanded_results = formatter.format_results(results, keywords, scope)
        
        formatted_keywords = ResultsDisplayHandler._format_keywords(keywords)
        placeholder_text = ResultsDisplayHandler._get_placeholder_text(keywords, len(results))
        
        def on_select(index):
            if index == -1:
                if command_instance and hasattr(command_instance, 'handle_quick_panel_cancel'):
                    command_instance.handle_quick_panel_cancel(formatted_keywords)
                else:
                    window.show_input_panel(
                        UIText.get_search_prompt(scope),
                        formatted_keywords,
                        on_done_callback,
                        on_change_callback,
                        on_cancel_callback
                    )
            else:
                ResultsDisplayHandler._handle_selection(
                    window, expanded_results[index], keywords, scope, highlight_segment_callback
                )
        
        def on_highlight(index):
            if index != -1:
                ResultsDisplayHandler._handle_preview(
                    window, expanded_results[index], keywords, scope, highlight_segment_callback
                )
        
        window.show_quick_panel(
            items,
            on_select,
            sublime.MONOSPACE_FONT,
            0,
            on_highlight,
            placeholder_text
        )
    
    @staticmethod
    def _format_keywords(keywords):
        """格式化关键词"""
        formatted = []
        for kw in keywords:
            formatted.append(TextUtils.format_keyword_for_input(kw))
        return ' '.join(formatted)
    
    @staticmethod
    def _get_placeholder_text(keywords, results_count):
        """获取占位符文本"""
        if keywords:
            placeholder_keywords = []
            for i, kw in enumerate(keywords):
                emoji = KEYWORD_EMOJIS[i % len(KEYWORD_EMOJIS)]
                formatted = TextUtils.format_keyword_for_input(kw)
                placeholder_keywords.append('{0}{1}'.format(emoji, formatted))
            return "Keywords: {} - {} lines found".format(' '.join(placeholder_keywords), results_count)
        else:
            return "All lines - {} lines found".format(results_count)
    
    @staticmethod
    def _handle_selection(window, item, keywords, scope, highlight_segment_callback):
        """处理选中项"""
        file_path = item['file']
        line_number = item.get('line_number', 1) - 1
        
        if scope == 'open_files':
            target_view = None
            for view in window.views():
                if view.file_name() == file_path:
                    target_view = view
                    break
            
            if target_view:
                window.focus_view(target_view)
                target_view.run_command("goto_line", {"line": line_number + 1})
                highlighter.highlight(target_view, keywords)
                highlight_segment_callback(target_view, item, line_number)
                return
        
        view = window.open_file(
            "{0}:{1}:0".format(file_path, line_number + 1),
            sublime.ENCODED_POSITION
        )
        
        def highlight_when_ready():
            if view.is_loading():
                sublime.set_timeout(highlight_when_ready, 50)
            else:
                highlighter.highlight(view, keywords)
                highlight_segment_callback(view, item, line_number)
        
        highlight_when_ready()
    
    @staticmethod
    def _handle_preview(window, item, keywords, scope, highlight_segment_callback):
        """处理预览"""
        file_path = item['file']
        line_number = item.get('line_number', 1) - 1
        
        if scope == 'open_files':
            for view in window.views():
                if view.file_name() == file_path:
                    window.focus_view(view)
                    view.run_command("goto_line", {"line": line_number + 1})
                    highlighter.highlight(view, keywords)
                    highlight_segment_callback(view, item, line_number)
                    return
        
        view = window.open_file(file_path, sublime.TRANSIENT)
        
        def goto_line():
            if view.is_loading():
                sublime.set_timeout(goto_line, 50)
            else:
                view.run_command("goto_line", {"line": line_number + 1})
                highlighter.highlight(view, keywords)
                highlight_segment_callback(view, item, line_number)
        
        goto_line()


class InputPanelHandlerMixin:
    """处理输入面板生命周期的 Mixin"""
    
    def run_with_input_handling(self):
        """统一的运行流程 - 无 clear_active_panel() 版本"""
        selected_text = self.get_selected_text()
        
        global_state.debug_print("run_with_input_handling(): scope='{0}', selected_text='{1}', has_active_panel={2}".format(
            self.scope, selected_text, global_state.has_active_panel()
        ))
        
        # 重置标记
        global_state.reset_esc_flag()
        
        # 检查相同scope的重复调用 - 直接聚焦现有面板
        if global_state.has_active_panel():
            active_scope = global_state.active_panel.get('scope', '')
            active_input_view = global_state.active_panel.get('input_view')
            
            if (active_scope == self.scope and 
                active_input_view and active_input_view.is_valid()):
                
                global_state.debug_print("Same scope ({0}) repeat call - focusing existing panel".format(self.scope))
                
                # 如果有选中文本，追加到现有面板
                if selected_text:
                    sublime.set_timeout(lambda: self.handle_selection_append(), 50)
                    return
                
                # 没有选中文本，只是聚焦现有面板
                self.window.focus_view(active_input_view)
                active_input_view.sel().clear()
                end_point = active_input_view.size()
                active_input_view.sel().add(sublime.Region(end_point, end_point))
                return
        
        # 有选中文本且有活动面板 - 追加到现有面板（不同scope）
        if selected_text and global_state.has_active_panel():
            global_state.debug_print("Appending selected text to existing panel")
            sublime.set_timeout(lambda: self.handle_selection_append(), 50)
            return
        
        # 准备切换面板
        if global_state.has_active_panel():
            # 保存当前面板文本
            current_text = global_state.get_active_panel_text()
            if current_text:
                global_state.stored_keywords = current_text
                global_state.debug_print("Saved current panel text: '{0}'".format(current_text))
            
            # 标记为面板切换状态 - 这是关键！
            global_state.is_panel_switching = True
            global_state.debug_print("Marking panel switch: True")
        
        # 准备新面板的初始文本
        initial_text = self.get_initial_text()
        
        # 直接创建新面板，让 Sublime 自动处理旧面板的关闭
        global_state.debug_print("Creating new panel with initial_text: '{0}'".format(initial_text))
        self.setup_input_panel(initial_text)
        
        # 延迟重置切换标记
        sublime.set_timeout(lambda: setattr(global_state, 'is_panel_switching', False), 100)


class QuickLineNavigatorCommand(BaseQuickLineNavigatorCommand, InputPanelHandlerMixin):
    def run(self, scope="file"):
        self.scope = scope
        
        # Initialize the necessary attributes based on scope
        if scope == "file":
            view = self.window.active_view()
            if not view or not view.file_name():
                sublime.status_message(UIText.get_status_message('no_file'))
                return
            self.file_path = view.file_name()
        elif scope in ["folder", "project"]:
            if scope == "folder":
                settings = Settings()
                custom_folder = settings.get("search_folder_path", "")
                if custom_folder and os.path.exists(custom_folder):
                    self.folders = [custom_folder]
                else:
                    self.folders = self.window.folders()
            else:  # project
                self.folders = self.window.folders()
            
            if not self.folders:
                sublime.status_message(UIText.get_status_message('no_folder' if scope == "folder" else 'no_project'))
                return
        
        self.run_with_input_handling()
    
    def on_done(self, input_text):
        self.original_keywords = input_text
        keywords = TextUtils.parse_keywords(input_text) if input_text else []
        
        if keywords:
            highlighter.highlight(self.window.active_view(), keywords)
        
        if self.scope == "file":
            results = self._search_file(keywords)
        elif self.scope in ["folder", "project"]:
            results = self._search_folders(keywords)
        else:
            results = []
        
        if self.process_search_done(input_text, results):
            self._show_results(results, keywords)
    
    def _search_file(self, keywords):
        search = SearchEngine(self.settings, "file", self.window)
        return search.search([self.file_path], keywords, self.original_keywords)
    
    def _search_folders(self, keywords):
        search = SearchEngine(self.settings, self.scope, self.window)
        return search.search(self.folders, keywords, self.original_keywords)
    
    def clear_highlights(self):
        highlighter.clear(self.window.active_view())
    
    def highlight_keywords(self, keywords):
        highlighter.highlight(self.window.active_view(), keywords)


class QuickLineNavigatorOpenFilesCommand(BaseQuickLineNavigatorCommand, InputPanelHandlerMixin):
    def run(self):
        self.scope = 'open_files'
        
        self.open_files = self._get_open_files()
        
        if not self.open_files:
            sublime.status_message(UIText.get_status_message('no_open_files'))
            return
        
        self.run_with_input_handling()
    
    def _get_open_files(self):
        """获取所有打开的文件路径"""
        open_files = []
        for view in self.window.views():
            if view.file_name():
                open_files.append(view.file_name())
        return open_files
    
    def on_done(self, input_text):
        self.original_keywords = input_text
        keywords = TextUtils.parse_keywords(input_text) if input_text else []
        
        if keywords:
            for view in self.window.views():
                if view and view.is_valid():
                    highlighter.highlight(view, keywords)
        
        search = SearchEngine(self.settings, "open_files", self.window)
        results = search.search(self.open_files, keywords, self.original_keywords)
        
        if self.process_search_done(input_text, results):
            self._show_results(results, keywords)
    
    def clear_highlights(self):
        for view in self.window.views():
            if view:
                highlighter.clear(view)
    
    def highlight_keywords(self, keywords):
        view = self.window.active_view()
        if view:
            highlighter.highlight(view, keywords)


class QuickLineNavigatorMenuCommand(sublime_plugin.WindowCommand):
    def run(self):
        menu_items = [
            ["📄 Search in Current File　　　　　　　1 🔍 Search Commands"],
            ["📁 Search in Project　　　　　　　　　2 🔍 Search Commands"],
            ["📂 Search in Folder　　　　　　　　　 3 🔍 Search Commands"],
            ["📑 Search in Open Files　　　　　　　 4 🔍 Search Commands"],
            
            ["🔄 Toggle Filters (Permanent)　　　　  5 🎛️ Filter Controls"],
            ["⏱️ Toggle Filters (Temporary)　　　　  6 🎛️ Filter Controls"],
            ["📊 Show Filter Status　　　　　　　　 7 🎛️ Filter Controls"],
            
            ["📍 Set Search Folder　　　　　　　　  8 📁 Folder Settings"],
            ["🗑️ Clear Search Folder　　　　　　　  9 📁 Folder Settings"],
            
            ["🧹 Clear All Highlights　　　　　　　  0 ✨ Highlight Management"],
            ["🔦 Clear Current View Highlights　　　- ✨ Highlight Management"]
        ]
        command_map = {
            0: ("quick_line_navigator", {"scope": "file"}),
            1: ("quick_line_navigator", {"scope": "project"}),
            2: ("quick_line_navigator", {"scope": "folder"}),
            3: ("quick_line_navigator_open_files", {}),
            
            4: ("toggle_extension_filters", {}),
            5: ("toggle_extension_filters_temporary", {}),
            6: ("show_filter_status", {}),
            
            7: ("set_search_folder", {}),
            8: ("clear_search_folder", {}),
            
            9: ("clear_keyword_highlights", {}),
            10: ("clear_current_view_highlights", {})
        }
        
        def on_select(index):
            if index == -1:
                return
            
            if index in command_map:
                command, args = command_map[index]
                self.window.run_command(command, args)
        
        self.window.show_quick_panel(
            menu_items,
            on_select,
            sublime.KEEP_OPEN_ON_FOCUS_LOST,
            0,
            None
        )


class ToggleExtensionFiltersCommand(sublime_plugin.WindowCommand):
    def run(self):
        settings = Settings()
        current = settings.get("extension_filters", True)
        new_value = not current
        
        settings.update_user_settings("extension_filters", new_value)
        
        status = "enabled ✓" if new_value else "disabled ✗"
        sublime.status_message(UIText.get_status_message('filter_enabled', status=status, mode='permanently'))
        
        if hasattr(self.window, 'extension_filters_temp_override'):
            delattr(self.window, 'extension_filters_temp_override')


class ToggleExtensionFiltersTemporaryCommand(sublime_plugin.WindowCommand):
    def run(self):
        settings = Settings()
        
        if hasattr(self.window, 'extension_filters_temp_override'):
            current = self.window.extension_filters_temp_override
        else:
            current = settings.get("extension_filters", True)
        
        self.window.extension_filters_temp_override = not current
        
        status = "enabled ✓" if not current else "disabled ✗"
        sublime.status_message(UIText.get_status_message('filter_enabled', status=status, mode='temporarily'))


class ShowFilterStatusCommand(sublime_plugin.WindowCommand):
    def run(self):
        settings = Settings()
        
        global_enabled = settings.get("extension_filters", True)
        file_scope = settings.get("extension_filters_file", None)
        folder_scope = settings.get("extension_filters_folder", None)
        project_scope = settings.get("extension_filters_project", None)
        open_files_scope = settings.get("extension_filters_open_files", None)
        
        has_temp_override = hasattr(self.window, 'extension_filters_temp_override')
        temp_value = self.window.extension_filters_temp_override if has_temp_override else None
        
        whitelist = settings.get("file_extensions", [])
        blacklist = settings.get("file_extensions_blacklist", [])
        
        status_lines = ["QuickLineNavigator Filter Status:"]
        status_lines.append("-" * 40)
        
        status_lines.append("Global Setting: {0}".format("Enabled" if global_enabled else "Disabled"))
        
        if has_temp_override:
            status_lines.append("Temporary Override: {0} (this session)".format(
                "Enabled" if temp_value else "Disabled"))
        
        status_lines.append("\nScope Settings:")
        status_lines.append("  File Search: {0}".format(
            self._format_scope_status(file_scope, global_enabled)))
        status_lines.append("  Folder Search: {0}".format(
            self._format_scope_status(folder_scope, global_enabled)))
        status_lines.append("  Project Search: {0}".format(
            self._format_scope_status(project_scope, global_enabled)))
        status_lines.append("  Open Files Search: {0}".format(
            self._format_scope_status(open_files_scope, global_enabled)))
        
        if whitelist:
            status_lines.append("\nWhitelist Extensions:")
            for ext in whitelist[:10]:
                status_lines.append("  - {0}".format(ext))
            if len(whitelist) > 10:
                status_lines.append("  ... and {0} more".format(len(whitelist) - 10))
        else:
            status_lines.append("\nWhitelist: Empty (all non-blacklisted files)")
        
        if blacklist:
            status_lines.append("\nBlacklist Extensions: {0} items".format(len(blacklist)))
        
        output_view = self.window.create_output_panel("filter_status")
        output_view.run_command("append", {"characters": "\n".join(status_lines)})
        self.window.run_command("show_panel", {"panel": "output.filter_status"})
    
    def _format_scope_status(self, scope_value, global_value):
        if scope_value is None:
            return "Inherit (currently {0})".format("Enabled" if global_value else "Disabled")
        return "Enabled" if scope_value else "Disabled"


class SetSearchFolderCommand(sublime_plugin.WindowCommand):
    def run(self):
        settings = Settings()
        current_folder = settings.get("search_folder_path", "")
        
        suggestions = []
        
        if current_folder:
            suggestions.append(["User config - {0}".format(os.path.basename(current_folder)), current_folder])
        
        for folder in self.window.folders():
            suggestions.append(["Project dir - " + os.path.basename(folder), folder])
        
        view = self.window.active_view()
        if view and view.file_name():
            file_dir = os.path.dirname(view.file_name())
            suggestions.append(["Current file's folder - " + os.path.basename(file_dir), file_dir])
        
        suggestions.append(["Enter path manually...", "__choose_me_to_modify__"])
        
        def on_select(index):
            if index == -1:
                return
            
            _, path = suggestions[index]
            
            if path == "__choose_me_to_modify__":
                self.window.show_input_panel(
                    "Enter folder path:",
                    current_folder,
                    self._set_folder,
                    None,
                    None
                )
            else:
                self._set_folder(path)
        
        self.window.show_quick_panel(suggestions, on_select)
    
    def _set_folder(self, path):
        if not path:
            return
        
        path = os.path.expanduser(path)
        path = os.path.expandvars(path)
        
        if not os.path.exists(path):
            sublime.error_message("Folder does not exist: {0}".format(path))
            return
        
        if not os.path.isdir(path):
            sublime.error_message("Path is not a folder: {0}".format(path))
            return
        
        settings = Settings()
        settings.update_user_settings("search_folder_path", path)
        sublime.status_message("Search folder set to: {0}".format(path))


class ClearSearchFolderCommand(sublime_plugin.WindowCommand):
    def run(self):
        settings = Settings()
        current_folder = settings.get("search_folder_path", "")
        
        if not current_folder:
            sublime.status_message(UIText.get_status_message('search_folder_set', path="None"))
            return
        
        if sublime.ok_cancel_dialog(
            "Clear search folder?\n\nCurrent: {0}".format(current_folder),
            "Clear"
        ):
            settings.update_user_settings("search_folder_path", "")
            sublime.status_message(UIText.get_status_message('search_folder_cleared'))


class ClearKeywordHighlightsCommand(sublime_plugin.WindowCommand):
    def run(self):
        highlighter.clear_all()
        sublime.status_message(UIText.get_status_message('highlights_cleared'))


class ClearCurrentViewHighlightsCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = self.window.active_view()
        if view:
            highlighter.clear(view)
            sublime.status_message(UIText.get_status_message('view_highlights_cleared'))


class ClearStoredKeywordsCommand(sublime_plugin.WindowCommand):
    """清理所有储存的关键词"""
    def run(self):
        global_state.clear_active_panel()
        sublime.status_message("All stored keywords cleared")


class QuickLineNavigatorEventListener(sublime_plugin.EventListener):
    def __init__(self):
        super().__init__()
        self.last_row = {}
        self.border_timers = {}
    
    def on_selection_modified(self, view):
        if not view or not view.is_valid():
            return
        
        # 检查是否有活动的搜索面板
        if global_state.has_active_panel():
            return
        
        view_id = view.id()
        try:
            current_row = view.rowcol(view.sel()[0].begin())[0] if view.sel() else -1
        except:
            current_row = -1
        
        last_row = self.last_row.get(view_id, -1)
        
        if current_row != last_row and last_row != -1:
            if view_id in self.border_timers:
                self.border_timers[view_id] = None
                
            segment_key = "QuickLineNavSegment_{0}".format(view_id)
            border_key = segment_key + "_border"
            try:
                view.erase_regions(segment_key)
                view.erase_regions(border_key)
            except:
                pass
            
            highlighter.clear_all()
        
        self.last_row[view_id] = current_row

    def on_window_command(self, window, command_name, args):
        """监听窗口命令 - 简化版本"""
        if command_name == "hide_overlay" or command_name == "hide_panel":
            highlighter.clear_all()



def plugin_loaded():
    settings_path = os.path.join(sublime.packages_path(), "User", SETTINGS_FILE)
    if not os.path.exists(settings_path):
        default_settings = {
            "default_search_scope": "file",
            "show_line_numbers": True,
            "preview_on_highlight": True,
            "search_folder_path": "",
            "extension_filters": True,
            "extension_filters_file": False,
            "extension_filters_folder": True,
            "extension_filters_project": None,
            "extension_filters_open_files": False,
            "max_display_length": 120,
            "file_extensions": [],
            "file_extensions_blacklist": [ext.lstrip('.') for ext in DEFAULT_BLACKLIST]
        }
        
        try:
            os.makedirs(os.path.dirname(settings_path), exist_ok=True)
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(default_settings, f, indent=4, ensure_ascii=False)
        except:
            pass


def plugin_unloaded():
    highlighter.clear_all()


# 全局实例
settings = Settings()
ugrep = UgrepExecutor()
highlighter = Highlighter()
import sublime
import sublime_plugin
import os
import re
import json
import time
import threading
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

HIGHLIGHT_SCOPES = ['region.redish', 'region.bluish', 'region.yellowish', 'region.greenish', # region.bluish → region.cyanish
                    'region.purplish', 'region.orangish', 'region.grayish']  # no region.grayish in mariana's default color scheme
                    # region.pinkish too similar to region.purplish
HIGHLIGHT_ICONS = ['dot', 'circle', 'cross', 'bookmark', 'dot', 'circle', 'bookmark']
KEYWORD_EMOJIS = ['🟥', '🟦', '🟨', '🟩', '🟪', '🟧', '⬜']


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
    def truncate_by_width(text, max_width):
        result = ""
        width = 0
        for ch in text:
            ch_width = TextUtils.display_width(ch)
            if width + ch_width > max_width:
                break
            result += ch
            width += ch_width
        return result
    
    @staticmethod
    def parse_keywords(input_text):
        keywords = []
        current = ""
        in_quotes = False
        quote_char = None
        quote_pairs = {
            '"': '"',    # 英文双引号
            "'": "'",    # 英文单引号
            '“': '”',    # 中文双引号
            '‘': '’'     # 中文单引号
        }
        
        for char in input_text:
            if char in quote_pairs and not in_quotes:
                in_quotes = True
                quote_char = quote_pairs[char]
            elif char == quote_char and in_quotes:
                in_quotes = False
                if current.strip():
                    keywords.append(current.strip())
                current = ""
                quote_char = None
            elif char == ' ' and not in_quotes:
                if current.strip():
                    keywords.append(current.strip())
                current = ""
            else:
                current += char
        
        if current.strip():
            keywords.append(current.strip())
        
        return [kw for kw in keywords if kw]

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
        
        cmd = [self.path, "-n", "-H", "--color=never", "-r", "-I", "-i"]
        
        if not file_filter.enabled:
            critical_blacklist = ["*.sublime-workspace", "*.sublime-project", "*.git", "*.svn", "*.hg",
                                "*.exe", "*.dll", "*.so", "*.dylib", "*.bin"]
            for pattern in critical_blacklist:
                cmd.extend(["--exclude", pattern])
        else:
            self._apply_filters(cmd, file_filter)
        
        if not keywords:
            cmd.extend(["-e", r"^\s*\S"])  # cmd.append(".")
        else:
            self._add_keywords(cmd, keywords)
        
        cmd.extend(paths if isinstance(paths, list) else [paths])
        
        print("  🔧 Ugrep: {0}".format(" ".join(self._format_arg(arg, i == 0) for i, arg in enumerate(cmd))))
        
        output, error = self._execute(cmd)
        if error:
            print("  ❌ Ugrep error: {0}".format(error))
        
        results = self._parse_output(output)
        print("  ✅ Ugrep found {0} lines".format(len(results)))
        
        if file_filter.enabled and self._needs_post_filter(file_filter):
            results = self._post_filter(results, file_filter)
            print("  🔧 Post-filtered to {0} lines".format(len(results)))
        
        return results
    
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
    
    def _add_keywords(self, cmd, keywords):
        keywords = [self._escape_keyword(kw) for kw in keywords if kw]
        if len(keywords) == 1:
            cmd.append(keywords[0])
        else:
            for kw in keywords:
                cmd.extend(["--and", "-e", kw])
    
    def _escape_keyword(self, keyword):
        special = r'\.^$*+?{}[]|()'
        return ''.join('\\' + ch if ch in special else ch for ch in keyword)
    
    def _format_arg(self, arg, is_first=False):
        if is_first:
            return str(arg)
        arg_str = str(arg)
        if (arg_str.startswith('"') and arg_str.endswith('"')) or \
           (arg_str.startswith("'") and arg_str.endswith("'")) or \
           (arg_str.startswith("“") and arg_str.endswith("”")) or \
           (arg_str.startswith("‘") and arg_str.endswith("’")):
            return arg_str
        
        needs_quotes = ' ' in arg_str or any(c in arg_str for c in '"\'\\()[]{}*?|^$&;') or arg_str != arg_str.strip()
        if needs_quotes:
            return '"{0}"'.format(arg_str.replace('\\', '\\\\').replace('"', '\\"'))
        return arg_str
    
    def _execute(self, cmd):
        try:
            kwargs = {}
            if platform.system() == "Windows":
                if hasattr(subprocess, 'CREATE_NO_WINDOW'):
                    kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                else:
                    kwargs['creationflags'] = 0x08000000  # CREATE_NO_WINDOW constant
            
            if hasattr(subprocess, 'run'):
                # Python 3.5+ with subprocess.run
                result = subprocess.run(cmd, capture_output=True, text=True, 
                                      encoding='utf-8', errors='ignore', timeout=30, **kwargs)
                return result.stdout, result.stderr
            else:
                # Older Python versions with subprocess.Popen
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                         universal_newlines=True, **kwargs)
                # Note: timeout parameter is passed to communicate(), not to Popen constructor
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
        print("  📍 Keywords: {0}".format(original or keywords))
        
        if self.scope in ["folder", "project"]:
            print("  📁 Folders: {0}".format(len(paths)))
        elif self.scope == "file":
            # paths is a list, so check if it has items
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
        
        if self.cache.get(view_id) == keywords:
            return
        
        if view.is_loading() or view.size() == 0:
            sublime.set_timeout(lambda: self.highlight(view, keywords), 100)
            return
        
        self.clear(view)
        
        for i, keyword in enumerate(keywords):
            if not keyword:
                continue
            
            try:
                regions = view.find_all(re.escape(keyword), sublime.IGNORECASE)
                if regions:
                    key = "{0}_{1}_{2}".format(self.key_base, view_id, i)
                    self.keys.add(key)
                    
                    scope = HIGHLIGHT_SCOPES[i % len(HIGHLIGHT_SCOPES)]
                    icon = HIGHLIGHT_ICONS[i % len(HIGHLIGHT_ICONS)]
                    
                    view.add_regions(key, regions, scope, icon, sublime.PERSISTENT)
            except:
                continue
        
        if self.keys:
            self.views.add(view_id)
            self.cache[view_id] = keywords[:]
    
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
        
        for i, item in enumerate(results):
            main_line = self._format_main_line(item['line'], keywords)
            sub_line = self._format_sub_line(item, i, scope)
            formatted.append([main_line, sub_line])
        
        return formatted
    
    def _format_main_line(self, line, keywords):
        if not keywords:
            return TextUtils.truncate_by_width(line.strip(), self.max_length)
        
        return self._format_with_emojis(line, keywords)
    
    def _format_with_emojis(self, line, keywords):
        emojis = [KEYWORD_EMOJIS[i % len(KEYWORD_EMOJIS)] for i in range(len(keywords))]
        emoji_width = 2 * len(emojis)
        
        if emoji_width > self.max_length:
            return self._show_emojis_only(emojis, self.max_length)
        
        return self._distribute_content(line, keywords, emojis, self.max_length)
    
    def _show_emojis_only(self, emojis, max_length):
        result = ""
        used = 0
        for emoji in emojis:
            if used + 2 <= max_length:
                result += emoji
                used += 2
            else:
                break
        return result
    
    def _distribute_content(self, line, keywords, emojis, max_length):
        safety_buffer = len(keywords)
        available = max_length - (2 * len(emojis)) - safety_buffer
        
        if available <= 0:
            return self._show_emojis_only(emojis, max_length)
        
        contexts = []
        line_lower = line.lower()
        
        for keyword in keywords:
            pos = line_lower.find(keyword.lower())
            if pos == -1:
                contexts.append({'found': False, 'keyword': keyword})
            else:
                contexts.append({
                    'found': True,
                    'keyword': keyword,
                    'pos': pos,
                    'left': line[:pos],
                    'right': line[pos + len(keyword):]
                })
        
        per_keyword = available // len(keywords) if keywords else 0
        
        result = ""
        for i, (emoji, ctx) in enumerate(zip(emojis, contexts)):
            result += emoji
            
            if ctx['found'] and per_keyword > 0:
                keyword_width = TextUtils.display_width(ctx['keyword'])
                if keyword_width <= per_keyword:
                    result += ctx['keyword']
                    remaining = per_keyword - keyword_width
                    if remaining > 0 and ctx['right']:
                        result += TextUtils.truncate_by_width(ctx['right'], remaining)
                else:
                    result += TextUtils.truncate_by_width(ctx['keyword'], per_keyword)
            elif per_keyword > 0:
                result += TextUtils.truncate_by_width(ctx['keyword'], per_keyword)
            
            if i < len(keywords) - 1:
                result += " "
        
        return result
    
    def _format_sub_line(self, item, index, scope):
        parts = []
        
        if self.show_line_numbers and 'line_number' in item:
            parts.append(str(item['line_number']))
        
        parts.append("⚡ {0}".format(index + 1))
        
        if 'file' in item and scope != 'file':
            filename = os.path.basename(item['file'])
            if len(filename) > 50:
                filename = filename[:47] + "..."
            parts.append("📄 {0}".format(filename))
        
        return "☲ " + " ".join(parts)


class CleanupManager:
    def __init__(self):
        self.active = True
        self.cleanup_thread = None
        self.last_cleanup = 0
    
    def set_active(self, active):
        """Set whether the cleanup manager is active"""
        self.active = active
    
    def cleanup_all(self):
        """清理所有视图中的无效区域"""
        if not self.active:
            return
        
        current_time = time.time()
        if current_time - self.last_cleanup < 60:  # 每分钟最多清理一次
            return
        
        self.last_cleanup = current_time
        
        def do_cleanup():
            try:
                for window in sublime.windows():
                    for view in window.views():
                        if view and view.is_valid():
                            self.cleanup_view(view)
            except:
                pass
        
        self.cleanup_thread = threading.Thread(target=do_cleanup)
        self.cleanup_thread.daemon = True  # Make thread daemon so it doesn't prevent shutdown
        self.cleanup_thread.start()
    
    def cleanup_view(self, view):
        """清理单个视图中的无效区域"""
        if not view or not view.is_valid() or not self.active:
            return
        
        try:
            # 获取所有相关的区域键
            all_keys = []
            for key in list(view.settings().to_dict().keys()):
                if key.startswith("QuickLineNav"):
                    all_keys.append(key)
            
            # 清理无效区域
            for key in all_keys:
                try:
                    regions = view.get_regions(key)
                    if not regions:
                        view.erase_regions(key)
                except:
                    view.erase_regions(key)
        except:
            pass


class UIText:
    SCOPE_NAMES = {
        'file': 'current file',
        'folder': 'folder',
        'project': 'project',
        'open_files': 'open files',
        'current_file': 'current file'
    }
    
    @classmethod
    def get_search_prompt(cls, scope):
        scope_text = cls.SCOPE_NAMES.get(scope, scope)
        return 'Pre-precision search in {0} with space-separated keywords or "key phrases":'.format(scope_text)
    
    @classmethod
    def get_status_message(cls, message_type, **kwargs):
        messages = {
            'no_folder': "No folder open",
            'no_project': "No project open", 
            'no_file': "No file open",
            'no_open_files': "No files open",
            'no_results': "No results found",
            'no_results_in_scope': "No results found in {scope}",
            'filter_enabled': "Extension filters {status} ({mode})",
            'search_folder_set': "Search folder set to: {path}",
            'search_folder_cleared': "Search folder cleared",
            'highlights_cleared': "QuickLineNavigator: All highlights cleared",
            'view_highlights_cleared': "QuickLineNavigator: Current view highlights cleared"
        }
        
        template = messages.get(message_type, message_type)
        return template.format(**kwargs)
    
    @classmethod
    def get_scope_display_name(cls, scope):
        return cls.SCOPE_NAMES.get(scope, scope).title()


class QuickLineNavigatorMenuCommand(sublime_plugin.WindowCommand):
    def run(self):
        menu_items = [
            # 分组标题和命令
            ["—"*10 + " 🔍 Search Commands  " + "—"*10, "-"*29 + "  Search in different scopes  " + "-"*30],
            ["📄 Search in Current File", "Search keywords in the active file"],
            ["📁 Search in Project", "Search keywords in all project folders"],
            ["📂 Search in Folder", "Search keywords in specific folder"],
            ["📑 Search in Open Files", "Search keywords in all open files"],
            
            ["—"*10 + " 🎛️ Filter Controls " + "—"*12, "-"*29 + "  Manage file extension filters  " + "-"*26],
            ["🔄 Toggle Filters (Permanent)", "Enable/disable extension filters permanently"],
            ["⏱️ Toggle Filters (Temporary)", "Enable/disable extension filters for this session"],
            ["📊 Show Filter Status", "Display current filter settings"],
            
            ["—"*10 + " 📁 Folder Settings " + "—"*12, "-"*29 + "  Configure search folders  " + "-"*31],
            ["📍 Set Search Folder", "Choose a specific folder for searches"],
            ["🗑️ Clear Search Folder", "Remove custom search folder"],
            
            ["—"*10 + " ✨ Highlight Management " + "—"*8, "-"*29 + "  Control keyword highlighting  " + "-"*25],
            ["🧹 Clear All Highlights", "Remove highlights from all views"],
            ["🔦 Clear Current View Highlights", "Remove highlights from current view"]
        ]
        
        # 对应的命令映射
        command_map = {
            1: ("quick_line_navigator", {"scope": "file"}),      # 📄 Search in Current File
            2: ("quick_line_navigator", {"scope": "project"}),   # 📁 Search in Project
            3: ("quick_line_navigator", {"scope": "folder"}),    # 📂 Search in Folder
            4: ("quick_line_navigator_open_files", {}),          # 📑 Search in Open Files
            
            6: ("toggle_extension_filters", {}),                 # 🔄 Toggle Filters (Permanent)
            7: ("toggle_extension_filters_temporary", {}),       # ⏱️ Toggle Filters (Temporary)
            8: ("show_filter_status", {}),                       # 📊 Show Filter Status
            
            10: ("set_search_folder", {}),                       # 📍 Set Search Folder
            11: ("clear_search_folder", {}),                     # 🗑️ Clear Search Folder
            
            13: ("clear_keyword_highlights", {}),                # 🧹 Clear All Highlights
            14: ("clear_current_view_highlights", {})           # 🔦 Clear Current View Highlights
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
            sublime.KEEP_OPEN_ON_FOCUS_LOST
        )


class QuickLineNavigatorCommand(sublime_plugin.WindowCommand):
    def run(self, scope="file"):
        self.scope = scope
        self.settings = Settings()
        self.original_keywords = ""
        
        if scope == "folder":
            search_folder = self.settings.get("search_folder_path", "")
            if search_folder and os.path.exists(search_folder):
                self.folders = [search_folder]
            else:
                self.folders = self.window.folders()
                if not self.folders:
                    sublime.status_message(UIText.get_status_message('no_folder'))
                    return
        elif scope == "project":
            self.folders = self.window.folders()
            if not self.folders:
                sublime.status_message(UIText.get_status_message('no_project'))
                return
        elif scope == "file":
            view = self.window.active_view()
            if not view or not view.file_name():
                sublime.status_message(UIText.get_status_message('no_file'))
                return
            self.file_path = view.file_name()
        
        initial_text = ""
        view = self.window.active_view()
        if view:
            for sel in view.sel():
                if not sel.empty():
                    initial_text = view.substr(sel)
                    break
        
        self.window.show_input_panel(
            UIText.get_search_prompt(scope),
            initial_text,
            self.on_done,
            self.on_change,
            self.on_cancel
        )
    
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
        
        if not results:
            sublime.status_message(UIText.get_status_message('no_results'))
            return
        
        self._show_results(results, keywords)
    
    def on_change(self, input_text):
        if self.settings.get("preview_on_highlight", True):
            if not input_text or not input_text.strip():
                highlighter.clear(self.window.active_view())
                return
            
            keywords = TextUtils.parse_keywords(input_text)
            if keywords:
                highlighter.highlight(self.window.active_view(), keywords)
            else:
                highlighter.clear(self.window.active_view())
    
    def on_cancel(self):
        highlighter.clear(self.window.active_view())
    
    def _search_file(self, keywords):
        search = SearchEngine(self.settings, "file", self.window)
        return search.search([self.file_path], keywords, self.original_keywords)
    
    def _search_folders(self, keywords):
        search = SearchEngine(self.settings, self.scope, self.window)
        return search.search(self.folders, keywords, self.original_keywords)
    
    def _show_results(self, results, keywords):
        formatter = DisplayFormatter(self.settings)
        items = formatter.format_results(results, keywords, self.scope)
        
        def on_select(index):
            if index != -1:
                item = results[index]
                file_path = item['file']
                line_number = item.get('line_number', 1) - 1
                
                view = self.window.open_file(
                    "{0}:{1}:0".format(file_path, line_number + 1),
                    sublime.ENCODED_POSITION
                )
                
                def highlight_when_ready():
                    if view.is_loading():
                        sublime.set_timeout(highlight_when_ready, 50)
                    else:
                        highlighter.highlight(view, keywords)
                
                highlight_when_ready()
        
        def on_highlight(index):
            if index != -1:
                item = results[index]
                file_path = item['file']
                line_number = item.get('line_number', 1) - 1
                
                view = self.window.open_file(file_path, sublime.TRANSIENT)
                
                def goto_line():
                    if view.is_loading():
                        sublime.set_timeout(goto_line, 50)
                    else:
                        view.run_command("goto_line", {"line": line_number + 1})
                        highlighter.highlight(view, keywords)
                
                goto_line()
        
        self.window.show_quick_panel(
            items,
            on_select,
            sublime.MONOSPACE_FONT,
            0,
            on_highlight
        )


class QuickLineNavigatorOpenFilesCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.settings = Settings()
        self.original_keywords = ""
        
        self.open_files = []
        for view in self.window.views():
            if view.file_name():
                self.open_files.append(view.file_name())
        
        if not self.open_files:
            sublime.status_message(UIText.get_status_message('no_open_files'))
            return
        
        initial_text = ""
        view = self.window.active_view()
        if view:
            for sel in view.sel():
                if not sel.empty():
                    initial_text = view.substr(sel)
                    break
        
        self.window.show_input_panel(
            UIText.get_search_prompt('open_files'),  # 使用统一的提示文字
            initial_text,
            self.on_done,
            self.on_change,
            self.on_cancel
        )
    
    def on_done(self, input_text):
        self.original_keywords = input_text
        keywords = TextUtils.parse_keywords(input_text) if input_text else []
        
        if keywords:
            for view in self.window.views():
                if view and view.is_valid():
                    highlighter.highlight(view, keywords)
        
        search = SearchEngine(self.settings, "open_files", self.window)
        results = search.search(self.open_files, keywords, self.original_keywords)
        
        if not results:
            sublime.status_message(UIText.get_status_message('no_results_in_scope', scope='open files'))
            return
        
        self._show_results(results, keywords)
    
    def on_change(self, input_text):
        if self.settings.get("preview_on_highlight", True):
            if not input_text or not input_text.strip():
                for view in self.window.views():
                    if view:
                        highlighter.clear(view)
                return
            
            keywords = TextUtils.parse_keywords(input_text)
            if keywords:
                view = self.window.active_view()
                if view:
                    highlighter.highlight(view, keywords)
            else:
                for view in self.window.views():
                    if view:
                        highlighter.clear(view)
    
    def on_cancel(self):
        for view in self.window.views():
            if view:
                highlighter.clear(view)
    
    def _show_results(self, results, keywords):
        formatter = DisplayFormatter(self.settings)
        items = formatter.format_results(results, keywords, "open_files")
        
        def on_select(index):
            if index != -1:
                item = results[index]
                file_path = item['file']
                line_number = item.get('line_number', 1) - 1
                
                target_view = None
                for view in self.window.views():
                    if view.file_name() == file_path:
                        target_view = view
                        break
                
                if target_view:
                    self.window.focus_view(target_view)
                    target_view.run_command("goto_line", {"line": line_number + 1})
                else:
                    self.window.open_file(
                        "{0}:{1}:0".format(file_path, line_number + 1),
                        sublime.ENCODED_POSITION
                    )
        
        def on_highlight(index):
            if index != -1:
                item = results[index]
                file_path = item['file']
                line_number = item.get('line_number', 1) - 1
                
                for view in self.window.views():
                    if view.file_name() == file_path:
                        self.window.focus_view(view)
                        view.run_command("goto_line", {"line": line_number + 1})
                        break
        
        self.window.show_quick_panel(
            items,
            on_select,
            sublime.MONOSPACE_FONT,
            0,
            on_highlight
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
            for ext in whitelist[:10]:  # 显示前10个
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
        cleanup_manager.cleanup_all()
        sublime.status_message(UIText.get_status_message('highlights_cleared'))


class ClearCurrentViewHighlightsCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = self.window.active_view()
        if view:
            highlighter.clear(view)
            cleanup_manager.cleanup_view(view)
            sublime.status_message(UIText.get_status_message('view_highlights_cleared'))


class QuickLineNavigatorEventListener(sublime_plugin.EventListener):
    def on_close(self, view):
        if view and view.is_valid():
            highlighter.clear(view)
            cleanup_manager.cleanup_view(view)


def plugin_loaded():
    cleanup_manager.cleanup_all()
    
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
    cleanup_manager.set_active(False)
    highlighter.clear_all()
    cleanup_manager.cleanup_all()


settings = Settings()
ugrep = UgrepExecutor()
highlighter = Highlighter()
cleanup_manager = CleanupManager()

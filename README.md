# QuickLineNavigator

A powerful Sublime Text plugin that applies accurate pre-filters to narrow candidate lines before performing fuzzy matching and navigating through lines in your codebase.

## 📺 Demo

https://github.com/user-attachments/assets/67b14314-0819-4472-95c2-8a4d6a2e9b4f

## 🔖 Table of Contents

1. [Usage Tips](#-usage-tips)
2. [Key Bindings](#️-key-bindings)
   - [Main Navigation](#-main-navigation)
   - [Search Commands](#-search-commands)
   - [Filter Controls](#️-filter-controls)
   - [Folder Settings](#-folder-settings)
   - [Highlight Management (unnecessary for now)](#-highlight-management-unnecessary-for-now)
3. [File Extension Filtering](#️-file-extension-filtering)
   - [Examples](#examples)
   - [Special Values](#special-values)
4. [Installation](#-installation)
   - [Package Control Installation (Recommended)](#package-control-installation-recommended)
   - [Manual Installation](#manual-installation)
5. [Plugin Directory Structure](#-plugin-directory-structure)
6. [Ugrep Inhancement](#-ugrep-inhancement)
   - [Obtaining Ugrep](#obtaining-ugrep)
   - [Without Ugrep](#without-ugrep)
7. [Features](#-features)
   - [Multi-scope Search](#-multi-scope-search)
   - [Smart Keyword System](#-smart-keyword-system)
   - [Intelligent File Filtering](#-intelligent-file-filtering)
   - [High-Performance Search Engine](#-high-performance-search-engine)
   - [Beautiful User Interface](#-beautiful-user-interface)
8. [Default Settings](#️-default-settings)
9. [Acknowledgments](#-acknowledgments)
   - [Plugin Inspirations](#plugin-inspirations)
   - [Conceptual Alignment](#conceptual-alignment)
   - [Development Tools](#development-tools)
   - [Special Thanks](#special-thanks)
10. [License](#-license)
11. [Contributing](#-contributing)
12. [Issues](#-issues)

## 🎯 Usage Tips

1. **Quick Search**: Select text and press `Ctrl+Alt+F` to search it instantly
   - `word1 word2`: Find lines containing both words.
   - Select next text and press `Ctrl+Alt+F` for incremental search.
2. **Multiple Keywords**: Use spaces to separate multiple search terms
   - `` `phrase with backticks` ``: Alternative phrase syntax
3. **Exact Phrases**: Use quotes for exact phrase matching: `` `error message` ``
4. **Filter Toggle**: Quickly toggle filters with `Ctrl+Alt+R` when needed
5. **Persistent Highlights**: Keywords remain highlighted **until** _cursor_ **move out of** _current line_

## ⌨️ Key Bindings

### 🧭 Main Navigation
| Command   | Windows/Linux  | Mac           | Description                       |
| --------- | -------------- | ------------- | --------------------------------- |
| Main Menu | `Alt+Shift+S` | `Alt+Shift+S` | Open QuickLineNavigator main menu |

### 🔍 Search Commands
| Command | Windows/Linux | Mac | Description |
|---------|---------------|-----|-------------|
| Search Current File | `Ctrl+Alt+F` | `Ctrl+Alt+F` | Search keywords in the active file |
| Search Open Files | `Alt+Shift+F` | `Alt+Shift+F` | Search keywords in all open files |
| Search Project | `Ctrl+Alt+E` | `Ctrl+Alt+E` | Search keywords in all project folders |
| Search Folder | `Alt+Shift+E` | `Alt+Shift+E` | Search keywords in specific folder |

### 🎛️ Filter Controls
| Command                    | Windows/Linux      | Mac               | Description                                       |
| -------------------------- | ------------------ | ----------------- | ------------------------------------------------- |
| Toggle Filters Temporarily | `Ctrl+Alt+R` | `Ctrl+Alt+R` | Enable/disable extension filters for this session |
| Toggle Extension Filters   | `Alt+Shift+R`       | `Alt+Shift+R`       | Enable/disable extension filters permanently      |
| Show Filter Status         | `Ctrl+Alt+S`       | `Ctrl+Alt+S`       | Display current filter settings                   |

### 📁 Folder Settings
| Command             | Windows/Linux      | Mac               | Description                           |
| ------------------- | ------------------ | ----------------- | ------------------------------------- |
| Set Search Folder   | `Alt+Shift+D`       | `Alt+Shift+D`       | Choose a specific folder for searches |
| Clear Search Folder | `Ctrl+Alt+D` | `Ctrl+Alt+D` | Remove custom search folder           |

## 🎛️ File Extension Filtering

The `file_extensions` setting supports various configurations:

| Configuration                       | Effect                            | Search Scope / Examples                                                          |
| ----------------------------------- | --------------------------------- | -------------------------------------------------------------------------------- |
| `["."]`                             | Only files **with extensions**    | Files with extensions like `main.py`, `index.html`, but not `README`, `Makefile` |
| `[""]`                              | Only files **without extensions** | `README`, `Makefile`, `LICENSE`, etc.                                            |
| `[]` or `["*"]`                     | **All files** (except blacklist)  | All files like `main.py`, `README`, etc., unless blacklisted                     |
| `["py"]` or `[".py"]` or `["*.py"]` | Only specific extension files     | `*.py` files like `main.py`, `test.py`                                           |

### Examples

```json
{
    "file_extensions": ["."],            // Only files with extensions
    "file_extensions": [""],             // Only files without extensions
    "file_extensions": ["*"],            // All files
    "file_extensions": [],               // All files (same as above)
    "file_extensions": ["py", "js"],     // Only .py and .js files
    "file_extensions": ["*.py", "*.js"], // Same as above (wildcard format)
    "file_extensions": ["py", ""],       // .py files + files without extensions
    "file_extensions": [".", "py"]       // All files with extensions (including .py)
}
```

### Special Values
- `"*"` - Match all files
- `"."` - Match only files with extensions
- `""` - Match only files without extensions

## 📦 Installation

### Package Control Installation (Recommended)
1. Install [Package Control](https://packagecontrol.io/installation) if you haven't already
2. Open Command Palette:
   - Windows/Linux: `Ctrl+Shift+P`
   - macOS: `Super+Shift+P`
3. Type `Package Control: Install Package` and press Enter
4. Search for `QuickLineNavigator` and press Enter
5. Wait for installation to complete

### Manual Installation
1. **Download the Plugin**
   - Visit [QuickLineNavigator Releases](https://github.com/ChenZhu-Xie/QuickLineNavigator/releases)
   - Download the latest `QuickLineNavigator.zip`

2. **Locate Sublime Text Packages Folder**
   - Open Sublime Text
   - Go to `Preferences` → `Browse Packages...`
   - This opens your Packages directory

3. **Install the Plugin**
   - Create a folder named `QuickLineNavigator` in the Packages directory
   - Extract the downloaded ZIP file into this folder
   - Directory paths by platform:
     - **Windows** (Installed): `%APPDATA%\Sublime Text\Packages\QuickLineNavigator\`
     - **Windows** (Portable): `Sublime Text\Data\Packages\QuickLineNavigator\`
     - **macOS**: `~/Library/Application Support/Sublime Text/Packages/QuickLineNavigator/`
     - **Linux**: `~/.config/sublime-text/Packages/QuickLineNavigator/`

4. **Verify Installation**
   - Restart Sublime Text (and wait for a minute)
   - Open Command Palette and search for `QuickLineNavigator`
   - You should see available commands

## 📁 Plugin Directory Structure

```
QuickLineNavigator/
├── QuickLineNavigator.py                 # Main plugin code
├── Default.sublime-commands              # Command palette entries
├── Default.sublime-settings              # Default settings
├── Default (Windows).sublime-keymap      # Windows key bindings
├── Default (Linux).sublime-keymap        # Linux key bindings
├── Default (OSX).sublime-keymap          # macOS key bindings
├── Main.sublime-menu                     # Menu integration
├── README.md                             # Documentation
├── LICENSE                               # License file
├── .gitignore                            # Git ignore rules
├── messages.json                         # Package Control messages
└── messages/                             # Message files
    └── install.txt                       # Post-install message
```

## 🔧 Ugrep Inhancement

QuickLineNavigator uses [ugrep](https://github.com/Genivia/ugrep) for high-performance searching. While the plugin works without ugrep (falling back to Python search), having ugrep significantly improves search speed (for heavy lines and multiple keywords).

### Obtaining Ugrep

_How-to-install_ `ugrep`: https://github.com/Genivia/ugrep#install

### Without Ugrep

The plugin will automatically detect and use `the appropriate binary` for your platform. If `ugrep` is not found, it will **fall back to Python-based search**, which is slower but fully functional.

## 🚀 Features

### 🔍 Multi-scope Search
Search across different scopes with precision and speed
- **Current File Search**: Quick search within the active file
  - Real-time keyword highlighting while typing
  - Case-insensitive search support
  - Multiple keyword support with space separation
- **Project Search**: Search across all project folders
  - Automatic project folder detection
  - Recursive directory traversal
  - Respects .gitignore patterns
- **Folder Search**: Target specific folders
  - Custom folder selection
  - Persistent folder preferences
  - Quick folder switching
- **Open Files Search**: Search through all open tabs
  - No file system access needed
  - Instant results from memory
  - Maintains file focus

### 🎯 Smart Keyword System
Advanced keyword parsing and highlighting
- **Multi-keyword Support**: Search with multiple keywords or `"key phrases"` simultaneously
  - Space-separated keywords (AND logic)
  - Quoted phrases for exact matches
  - Support for both English and Chinese quotes
- **Visual Indicators**: Beautiful emoji indicators for each keyword
  - 🟥 🟦 🟨 🟩 🟪 🟧 ⬜ (rotating colors)
  - Persistent highlighting across views
  - Clear visual distinction between keywords

### 🔧 Intelligent File Filtering
Comprehensive file extension management
- **Whitelist/Blacklist System**
  - Define allowed file extensions
  - Exclude unwanted file types
  - Default blacklist for binary files
- **Scope-specific Filters**
  - Different filters for file/folder/project searches
  - Temporary filter overrides
  - Per-session filter toggles
- **Performance Optimization**
  - Skip large files automatically
  - Ignore binary files by default
  - Smart encoding detection

### ⚡ High-Performance Search Engine
Blazing fast search with [ugrep](https://github.com/Genivia/ugrep) integration
- **Ugrep Integration**: When available, uses [ugrep](https://github.com/Genivia/ugrep) for faster searches
  - Cross-platform binary support (Windows/macOS/Linux)
  - Automatic fallback to Python search
  - Parallel search capabilities
- **Smart Caching**: Reduces redundant operations
  - Highlight state caching
  - Search result caching
  - View state management

### 🎨 Beautiful User Interface
Clean and intuitive interface design
- **Rich Preview Panel**
  - Monospace font for code alignment
  - Line number display
  - File path indicators
  - Emoji-enhanced readability
- **Interactive Navigation**
  - Live preview on hover
  - Transient file preview
  - Quick jump to results
  - Maintain search context

## ⚙️ Default Settings

Access settings via `Preferences` → `Package Settings` → `QuickLineNavigator` → `Settings`

```json
{
    // Default search scope: "file", "folder", "project", "open_files"
    "default_search_scope": "file",

    // Show line numbers in search results
    "show_line_numbers": true,

    // Preview highlights while typing in search input
    "preview_on_highlight": true,

    // Custom search folder path (empty uses project folders)
    "search_folder_path": "",

    // Enable file extension filters globally
    "extension_filters": true,

    // Scope-specific filter settings (null inherits global setting)
    "extension_filters_file": false,      // Disabled for current file search
    "extension_filters_folder": true,     // Enabled for folder search
    "extension_filters_project": null,    // Inherits global setting
    "extension_filters_open_files": false,// Disabled for open files search

    // Maximum display width for search results (in characters)
    "max_display_length": 120,

    // Whitelisted file extensions (empty array = all files)
    // Examples: [".py", ".js", "txt", "md"]
    "file_extensions": [],
    
    // Blacklisted file extensions (without dots)
    "file_extensions_blacklist": [
        // Executables and binaries
        "exe", "dll", "so", "dylib", "a", "lib", "obj", "o", "bin",
        "class", "jar", "war", "ear", "pyc", "pyo", "pyd",
        
        // Databases
        "db", "sqlite", "sqlite3", "dat",
        
        // Images
        "jpg", "jpeg", "png", "gif", "bmp", "tiff", "ico", "webp", "svg",
        
        // Media files
        "mp3", "mp4", "avi", "mov", "wmv", "flv", "mkv", "webm", "wav", "m4a",
        
        // Documents
        "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
        
        // Archives
        "zip", "rar", "7z", "tar", "gz", "bz2", "xz",
        "iso", "img", "dmg", "deb", "rpm", "msi",
        
        // Fonts
        "ttf", "otf", "woff", "woff2", "eot",
        
        // Sublime Text files
        "sublime-workspace", "sublime-project",
        
        // Version control
        "git", "svn", "hg",
        
        // Temporary files
        "tmp", "cache", "log", "swp", "swo", "swn", "bak", "~"
    ]
}
```

## 🙏 Acknowledgments

This plugin was inspired by and built upon the ideas from several excellent projects and resources:

### Plugin Inspirations
- **[Fuzzy Search Plugin Discussion](https://forum.sublimetext.com/t/fuzzy-search-jump-to-any-line-via-quick-panel-plugin/45947)** + **[SimpleFuzzy](https://github.com/ukyouz/SublimeText-SimpleFuzzy)**
  - The original concept discussion & plugin that sparked the idea for fuzzy searches enhanced quick line navigation in Sublime Text.
- **[SearchInProject](https://github.com/leonid-shevtsov/SearchInProject_SublimeText)** by Leonid Shevtsov
  - An excellent implementation of project-wide search that influenced our multi-scope search design.
- **[StickySearch](https://github.com/vim-zz/StickySearch)** by vim-zz
  - A brilliant plugin that inspired our persistent keyword highlighting feature, showing how visual feedback can enhance search workflows.

### Conceptual Alignment
- **[Jeff Huber's Vision at Chroma](https://youtu.be/pIbIZ_Bxl_g?si=ut13j65qVwYRg0NR)**
  - This plugin shares the same philosophy of `first matching for pre filtering most irrelevant content, and second matching for further scoring, sorting, and retrieval of the remaining small portion`, as beautifully articulated (in a different way) by Jeff Huber.

### Development Tools
- **[Pieces Copilot](https://pieces.app/)**
  - An invaluable AI-powered development assistant that helped streamline the coding process and improve code quality throughout this project.

### Special Thanks
- [ugrep](https://github.com/Genivia/ugrep) by Robert van Engelen _et al._
  - for the blazing-fast search engine which supports `--and`
- All contributors and users who help make sublime searching experience better

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. Focus areas:

- [] Hit the sub-line accurately = directly jump into that sub-line.
- [] Fuzzy search the whole line like **[SimpleFuzzy](https://github.com/ukyouz/SublimeText-SimpleFuzzy)**, while jump to the specific subline?
- [] Performance issue -_+ (should always on one's mind), including segmentation, attaining + prefiltering lines, fuzzy search, fuzzy-search jump-into-line...
- [] More mature whole-subline segmentation algorithms for more common Chinese and English languages, as well as for staccato sentences in programming languages.
- [] Perfect segmentation vs approaching quick panel's max_display_length but not exceeding it. (Now tend toward the former rather than the latter, so that there is still a very low probability that exceeds the maximum display length <= bug or feature?)
- [] More appropriate interaction logic? (I think it seems to have been optimized quite well now)
<!-- - More beautiful/logical color & emoji highlight? -->

## 🐛 Issues

Found a bug or have a feature request? Please open an issue on [GitHub Issues](https://github.com/ChenZhu-Xie/QuickLineNavigator/issues).

- Highlight bugs
  - Some highlights cannot be cleared (such as forcibly switching search scope, switching projects, closing files, or closing the Sublime window during the search process)?
  - Some highlights are not applied to the corresponding keywords in time?
- [x] ~~Currently, immediately closing Sublime or switching projects will cause the highlight to be unable to be eliminated, when the 4 main search functions of the plugin are running.~~
  - [x] ~~I have tried cleaning by view in ST 4 instead of viewid in ST 3, but it seems to have no effect.~~
- {Keywords dict} are not retained?
  - [x] ~~Before executing the precise search, switch the scope.~~
  - [] After the precise retrieval is executed, switch the scope in the quick panel.
  - [] After the precise retrieval is executed, switch the scope outside the quick panel.
    - [] cursor inside the text editor.
    - [] cursor inside the keywords input panel.

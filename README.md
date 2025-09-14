# QuickLineNavigator

A powerful Sublime Text plugin that applies accurate pre-filters to narrow candidate lines before performing fuzzy matching and navigating through lines in your codebase.

## 📺 Demo

https://github.com/user-attachments/assets/67b14314-0819-4472-95c2-8a4d6a2e9b4f

## 🎯 Usage Tips

1. **Quick Search**: Select text and press `Alt+R` to search it instantly
2. **Multiple Keywords**: Use spaces to separate multiple search terms
3. **Exact Phrases**: Use quotes for exact phrase matching: `"error message"`
4. **Filter Toggle**: Quickly toggle filters with `Ctrl+Alt+F` when needed
5. **Persistent Highlights**: Keywords remain highlighted until explicitly cleared

## ⌨️ Key Bindings

### 🎯 Main Navigation
| Command | Windows/Linux | Mac | Description |
|---------|---------------|-----|-------------|
| Main Menu | `Ctrl+Shift+Q` | `Cmd+Shift+Q` | Open QuickLineNavigator main menu |

### 🔍 Search Commands
| Command | Windows/Linux | Mac | Description |
|---------|---------------|-----|-------------|
| Search Current File | `Alt+R` | `Alt+R` | Search keywords in the active file |
| Search Project | `Ctrl+Alt+R` | `Cmd+Alt+R` | Search keywords in all project folders |
| Search Folder | `Shift+Alt+R` | `Shift+Alt+R` | Search keywords in specific folder |
| Search Open Files | `Ctrl+Shift+Alt+R` | `Cmd+Shift+Alt+R` | Search keywords in all open files |

### 🎛️ Filter Controls
| Command | Windows/Linux | Mac | Description |
|---------|---------------|-----|-------------|
| Toggle Extension Filters | `Ctrl+Alt+F` | `Cmd+Alt+F` | Enable/disable extension filters permanently |
| Toggle Filters Temporarily | `Ctrl+Alt+Shift+F` | `Cmd+Alt+Shift+F` | Enable/disable extension filters for this session |
| Show Filter Status | `Ctrl+Alt+S` | `Cmd+Alt+S` | Display current filter settings |

### 📁 Folder Settings
| Command | Windows/Linux | Mac | Description |
|---------|---------------|-----|-------------|
| Set Search Folder | `Ctrl+Alt+D` | `Cmd+Alt+D` | Choose a specific folder for searches |
| Clear Search Folder | `Ctrl+Alt+Shift+D` | `Cmd+Alt+Shift+D` | Remove custom search folder |

### ✨ Highlight Management (unnecessary)
| Command | Windows/Linux | Mac | Description |
|---------|---------------|-----|-------------|
| Clear All Highlights | `Ctrl+Alt+H` | `Cmd+Alt+H` | Remove highlights from all views |
| Clear Current View Highlights | `Ctrl+Shift+H` | `Cmd+Shift+H` | Remove highlights from current view |

## 📦 Installation

### Package Control Installation (Recommended)
1. Install [Package Control](https://packagecontrol.io/installation) if you haven't already
2. Open Command Palette: 
   - Windows/Linux: `Ctrl+Shift+P`
   - macOS: `Cmd+Shift+P`
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
   - Restart Sublime Text
   - Open Command Palette and search for `QuickLineNavigator`
   - You should see available commands

## 📁 Plugin Directory Structure

```
QuickLineNavigator/
├── QuickLineNavigator.py                 # Main plugin code
├── QuickLineNavigator.sublime-commands   # Command palette entries
├── QuickLineNavigator.sublime-settings   # Default settings
├── Default (Windows).sublime-keymap      # Windows key bindings
├── Default (Linux).sublime-keymap        # Linux key bindings
├── Default (OSX).sublime-keymap          # macOS key bindings
├── Main.sublime-menu                     # Menu integration
├── README.md                             # Documentation
├── LICENSE                               # License file
├── .gitignore                           # Git ignore rules
├── messages.json                        # Package Control messages
├── messages/                            # Message files
│   └── install.txt                      # Post-install message
└── bin/                                 # Binary executables
    ├── ugrep.exe                        # Windows executable
    ├── ugrep                            # Linux executable
    └── ugrep_mac                        # macOS executable
```

## 🔧 Setting Up ugrep Binary Files

QuickLineNavigator uses [ugrep](https://github.com/Genivia/ugrep) for high-performance searching. While the plugin works without ugrep (falling back to Python search), having ugrep significantly improves search speed (for heavy lines and multiple keywords).

### Obtaining ugrep Binaries

#### Option 1: Download Pre-compiled Binaries (Recommended)

Visit the [ugrep releases page](https://github.com/Genivia/ugrep/releases) and download the appropriate binary for your platform:

1. **Windows**
   - Download `ugrep-win64.zip` or `ugrep-win32.zip`
   - Extract `ugrep.exe` from the zip file
   - Place it in `QuickLineNavigator/bin/ugrep.exe`

2. **macOS**
   - **Intel Mac**: Download `ugrep-macosx-x64.zip`
   - **Apple Silicon (M1/M2)**: Download `ugrep-macosx-arm64.zip`
   - Extract the `ugrep` binary from the zip file
   - Rename it to `ugrep_mac`
   - Place it in `QuickLineNavigator/bin/ugrep_mac`
   - Make it executable: `chmod +x bin/ugrep_mac`

3. **Linux**
   - **x64**: Download `ugrep-linux-x64.zip`
   - **ARM64**: Download `ugrep-linux-arm64.zip`
   - Extract the `ugrep` binary from the zip file
   - Place it in `QuickLineNavigator/bin/ugrep`
   - Make it executable: `chmod +x bin/ugrep`

#### Option 2: Install via Package Manager

**macOS (Homebrew)**
```bash
brew install ugrep
# Then copy to plugin directory
cp $(which ugrep) /path/to/QuickLineNavigator/bin/ugrep_mac
```

**Ubuntu/Debian**
```bash
sudo apt update
sudo apt install ugrep
# Then copy to plugin directory
cp $(which ugrep) /path/to/QuickLineNavigator/bin/ugrep
```

**Arch Linux**
```bash
sudo pacman -S ugrep
# Then copy to plugin directory
cp $(which ugrep) /path/to/QuickLineNavigator/bin/ugrep
```

#### Option 3: Compile from Source

For systems without pre-compiled binaries:

```bash
# Download source code
wget https://github.com/Genivia/ugrep/archive/refs/tags/v7.5.0.tar.gz
tar -xzf v7.5.0.tar.gz
cd ugrep-7.5.0

# Configure and compile
./configure
make

# Copy the binary to plugin directory
# For Linux:
cp src/ugrep /path/to/QuickLineNavigator/bin/ugrep
# For macOS:
cp src/ugrep /path/to/QuickLineNavigator/bin/ugrep_mac

# Make executable
chmod +x /path/to/QuickLineNavigator/bin/ugrep*
```

### Verifying ugrep Installation

After placing the binaries, your plugin structure should look like:
```
QuickLineNavigator/
└── bin/
    ├── ugrep.exe      # Windows binary
    ├── ugrep          # Linux binary (executable)
    └── ugrep_mac      # macOS binary (executable)
```

The plugin will automatically detect and use the appropriate binary for your platform. If ugrep is not found, it will fall back to Python-based search, which is slower but fully functional.

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
    // Examples: ["py", "js", "txt", "md"]
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
- **[Fuzzy Search Plugin Discussion](https://forum.sublimetext.com/t/fuzzy-search-jump-to-any-line-via-quick-panel-plugin/45947)** - The original concept discussion that sparked the idea for fuzzy searches enhanced quick line navigation in Sublime Text.

- **[SearchInProject](https://github.com/leonid-shevtsov/SearchInProject_SublimeText)** by Leonid Shevtsov - An excellent implementation of project-wide search that influenced our multi-scope search design.

- **[StickySearch](https://github.com/vim-zz/StickySearch)** by vim-zz - A brilliant plugin that inspired our persistent keyword highlighting feature, showing how visual feedback can enhance search workflows.

### Conceptual Alignment
- **[Jeff Huber's Vision at Chroma](https://youtu.be/pIbIZ_Bxl_g?si=ut13j65qVwYRg0NR)** - This plugin shares the same philosophy of `first matching for pre filtering most irrelevant content, and second matching for further scoring, sorting, and retrieval of the remaining small portion`, as beautifully articulated (in a different way) by Jeff Huber.

### Development Tools
- **[Pieces Copilot](https://pieces.app/)** - An invaluable AI-powered development assistant that helped streamline the coding process and improve code quality throughout this project.

### Special Thanks
- [ugrep](https://github.com/Genivia/ugrep) by Robert van Engelen _et al._ for the blazing-fast search engine which supports `--and`
- All contributors and users who help make sublime searching experience better

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🐛 Issues

Found a bug or have a feature request? Please open an issue on [GitHub Issues](https://github.com/ChenZhu-Xie/QuickLineNavigator/issues).

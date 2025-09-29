# QuickLineNavigator

A powerful Sublime Text plugin that applies accurate pre-filters to narrow candidate lines before performing fuzzy matching and navigating through (sub)lines in your codebase.

## 📺 Demo.gif

![QuickLineNavigator-2 9-small](https://github.com/user-attachments/assets/13c0d016-9544-45f1-8f93-801bdf2e5162)

## 📺 Demo.mp4

https://github.com/user-attachments/assets/67b14314-0819-4472-95c2-8a4d6a2e9b4f

>  The actual performance & user experience should surpass that of the old demo.mp4 shown above ↑

## 🔖 Table of Contents

1. [Usage Tips](#-usage-tips)
2. [Key Bindings](#️-key-bindings)
   - [Main Navigation](#-main-navigation)
   - [Search Commands](#-search-commands)
   - [Filter Controls](#️-filter-controls)
   - [Folder Settings](#-folder-settings)
3. [File Extension Filtering](#️-file-extension-filtering)
   - [Examples](#examples)
   - [Special Values](#special-values)
4. [Installation](#-installation)
   - [Package Control Installation (Recommended)](#package-control-installation-recommended)
5. [Ugrep Inhancement](#-ugrep-inhancement)
   - [Obtaining Ugrep](#obtaining-ugrep)
   - [Without Ugrep](#without-ugrep)
6. [Acknowledgments](#-acknowledgments)
   - [Plugin Inspirations](#plugin-inspirations)
   - [Conceptual Alignment](#conceptual-alignment)
   - [Development Tools](#development-tools)
   - [Special Thanks](#special-thanks)
7. [License](#-license)
8. [Contributing](#-contributing)
9. [Issues](#-issues)

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

## 🔧 Ugrep Inhancement

QuickLineNavigator uses [ugrep](https://github.com/Genivia/ugrep) for high-performance searching. While the plugin works without ugrep (falling back to Python search), having ugrep significantly improves search speed (for heavy lines and multiple keywords).

### Obtaining Ugrep

_How-to-install_ `ugrep`: https://github.com/Genivia/ugrep#install

### Without Ugrep

The plugin will automatically detect and use `the appropriate binary` for your platform. If `ugrep` is not found, it will **fall back to Python-based search**, which is slower but fully functional.

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

- [x] Hit the sub-line accurately = directly jump into that sub-line.
- [ ] Fuzzy search the whole line like **[SimpleFuzzy](https://github.com/ukyouz/SublimeText-SimpleFuzzy)**, while jump to the specific subline?
- [ ] Performance issue -_+ (should always on one's mind), including segmentation, attaining + prefiltering lines, fuzzy search, fuzzy-search jump-into-line...
  - [x] attaining + prefiltering lines: ugrep = fast enough for multi-keywords grep?
  - [x] segmentation: The complexity of single-line slicing has been reduced from "binary × substring scan" to "binary × O(1) + bisect", which has an order of magnitude improvement for long lines (especially multiple keywords).
  - [x] The keyword preparation overhead of multiple result formatting is almost eliminated.
- [ ] More mature whole-subline segmentation algorithms for more common Chinese and English languages, as well as for staccato sentences in programming languages.
- [ ] Perfect segmentation vs approaching quick panel's max_display_length but not exceeding it. (Now tend toward the former rather than the latter, so that there is still a very low probability that exceeds the maximum display length <= bug or feature?)
- [ ] Concurrent highlighting within the right-hand “minimap”
- [ ] Refine the search for Chinese phrases
- [ ] Refined log outputs
- [ ] More appropriate interaction logic? (I think it seems to have been optimized quite well now)
- [ ] Highlight (behavior) while editing?
<!-- - More beautiful/logical color & emoji highlight? -->

## 🐛 Issues

Found a bug or have a feature request? Please open an issue on [GitHub Issues](https://github.com/ChenZhu-Xie/QuickLineNavigator/issues).

- Highlight bugs?
  - Some highlights cannot be cleared? (such as forcibly switching search scope, switching projects, closing files, or closing the Sublime window during the search process)
  - Some highlights are not applied to the corresponding keywords (within the editor) in time?
- [x] ~~Currently, immediately closing Sublime or switching projects will cause the highlight to be unable to be eliminated, when the 4 main search functions of the plugin are running. (not a problem anymore, have been figured out.)~~
  - [x] ~~I have tried cleaning by view in ST 4 instead of viewid in ST 3, but it seems to have no effect.~~
- [x] {Keywords dict} are not retained?
  - [x] Before executing the precise search, switch the scope.
  - [x] After the precise retrieval is executed, switch the scope in the quick panel.
  - [x] After the precise retrieval is executed, switch the scope outside the quick panel.
    - [x] cursor inside the text editor.
    - [x] cursor inside the keywords input panel.
- [ ] More appropriate delimiter and identifying logic for keyphrases?

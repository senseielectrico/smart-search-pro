# Smart Search - Component Architecture

## Visual Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Menu Bar: File | Search | View | Help                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Search Bar                                                           │    │
│  │  [Search Input ___________________] [x] Case  [Search] [Stop] [Dark]│    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Quick Filters: [All] [Images] [Docs] [Videos] [Audio] [Code] [Zip] │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
├──────────────┬────────────────────────────────────────────┬─────────────────┤
│              │                                            │                 │
│  Directory   │         Results Area                      │  File Preview   │
│  Tree        │                                            │                 │
│              │  View: [List] [Grid]                      │  ┌────────────┐ │
│  □ C:\       │  ┌──────────────────────────────────────┐ │  │            │ │
│  □ ~Home     │  │ Tabs: Docs | Images | Videos | ...  │ │  │   Image/   │ │
│  ☑ Desktop   │  │                                      │ │  │   Text     │ │
│  ☑ Documents │  │  Name    Path     Size    Modified  │ │  │  Preview   │ │
│  □ Downloads │  │  ──────────────────────────────────  │ │  │            │ │
│  □ Pictures  │  │  file1   /path1   2MB     12:30     │ │  └────────────┘ │
│  □ Videos    │  │  file2   /path2   1.5MB   11:45     │ │                 │
│  □ Music     │  │  file3   /path3   800KB   10:15     │ │  Path: ...      │
│              │  │  [... more rows ...]                │ │  Size: 2.5 MB   │
│  ★ Favorites │  │                                      │ │  Date: 2025..   │
│  ★ Projects  │  │                                      │ │  Type: JPG      │
│              │  └──────────────────────────────────────┘ │                 │
│  ─────────   │                                            │                 │
│  Recent      │  OR Grid View:                            │                 │
│  Searches    │  ┌────┬────┬────┬────┬────┐              │                 │
│              │  │ 📄 │ 🖼️ │ 📄 │ 🎵 │ 📄 │              │                 │
│  • "report"  │  │ f1 │ f2 │ f3 │ f4 │ f5 │              │                 │
│    (50 res)  │  ├────┼────┼────┼────┼────┤              │                 │
│  • "*.py"    │  │ 🖼️ │ 📄 │ 📁 │ 📄 │ 🖼️ │              │                 │
│    (120 res) │  │ f6 │ f7 │ f8 │ f9 │f10 │              │                 │
│  • "photo"   │  └────┴────┴────┴────┴────┘              │                 │
│    (85 res)  │                                            │                 │
│              │                                            │                 │
└──────────────┴────────────────────────────────────────────┴─────────────────┘
│                                                                               │
│  Files: 150  [Open] [Location] [Copy] [Move] [Export] [Presets] [Clear]    │
│                                                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│ Status: Search complete. Found 150 files.              [■■■■■■■■  ] 80%     │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Hierarchy

```
EnhancedSmartSearchWindow (QMainWindow)
│
├── MenuBar
│   ├── File Menu
│   │   ├── Export Results (Ctrl+E)
│   │   └── Exit (Ctrl+Q)
│   │
│   ├── Search Menu
│   │   ├── New Search (Ctrl+N)
│   │   ├── Save as Preset (Ctrl+S)
│   │   ├── Load Preset (Ctrl+P)
│   │   └── Clear History
│   │
│   ├── View Menu
│   │   ├── List View (Ctrl+1)
│   │   ├── Grid View (Ctrl+2)
│   │   └── Toggle Preview (Ctrl+T)
│   │
│   └── Help Menu
│       ├── Keyboard Shortcuts (F1)
│       └── About
│
├── Search Bar Container (VBox)
│   ├── Search Controls Row (HBox)
│   │   ├── QLineEdit (search_input) + Autocomplete
│   │   ├── QCheckBox (case_sensitive_cb)
│   │   ├── QPushButton (search_btn)
│   │   ├── QPushButton (stop_btn)
│   │   └── QPushButton (theme_btn)
│   │
│   └── QuickFilterChips
│       └── Filter Buttons [All, Images, Docs, ...]
│
├── Main Splitter (Horizontal, 3-panel)
│   │
│   ├── LEFT PANEL: Directory & History (VBox)
│   │   ├── EnhancedDirectoryTree
│   │   │   ├── System Drive
│   │   │   ├── User Home
│   │   │   ├── Desktop
│   │   │   ├── Documents
│   │   │   └── ... (with checkboxes)
│   │   │   └── Context Menu:
│   │   │       ├── Add/Remove Favorite
│   │   │       ├── Expand/Collapse All
│   │   │       ├── Open in Explorer
│   │   │       └── Properties
│   │   │
│   │   └── SearchHistoryWidget
│   │       ├── Header + Clear Button
│   │       └── QListWidget (recent searches)
│   │
│   ├── CENTER PANEL: Results (VBox)
│   │   ├── View Toggle (HBox)
│   │   │   ├── List View Button
│   │   │   └── Grid View Button
│   │   │
│   │   ├── QTabWidget (results_tabs) - List View
│   │   │   ├── Documents Tab → ResultsTableWidget
│   │   │   ├── Images Tab → ResultsTableWidget
│   │   │   ├── Videos Tab → ResultsTableWidget
│   │   │   ├── Audio Tab → ResultsTableWidget
│   │   │   ├── Archives Tab → ResultsTableWidget
│   │   │   ├── Code Tab → ResultsTableWidget
│   │   │   ├── Executables Tab → ResultsTableWidget
│   │   │   └── Other Tab → ResultsTableWidget
│   │   │
│   │   └── GridViewWidget (grid_view) - Grid View
│   │       └── Grid Layout (5 columns)
│   │           └── File Items (icon + name)
│   │
│   └── RIGHT PANEL: FilePreviewPanel (VBox)
│       ├── Title Label
│       ├── Separator
│       ├── Scroll Area
│       │   ├── QLabel (image preview)
│       │   ├── QTextEdit (text preview)
│       │   └── QLabel (file info)
│       └── Metadata Display
│
├── Action Bar (HBox)
│   ├── QLabel (file_count_label)
│   ├── Stretch
│   ├── QPushButton (open_btn)
│   ├── QPushButton (open_location_btn)
│   ├── QPushButton (copy_btn)
│   ├── QPushButton (move_btn)
│   ├── QPushButton (export_btn) ← NEW
│   ├── QPushButton (presets_btn) ← NEW
│   └── QPushButton (clear_btn)
│
└── Status Bar
    ├── Status Message
    └── QProgressBar (progress_bar)
```

## Data Flow Diagram

```
┌──────────────┐
│  User Input  │
└──────┬───────┘
       │
       ├─────────────────────────────────────────────┐
       │                                             │
       v                                             v
┌──────────────┐                            ┌─────────────────┐
│ Search Input │                            │ Directory Tree  │
│   + Filter   │                            │   Checkboxes    │
└──────┬───────┘                            └────────┬────────┘
       │                                              │
       │                                              │
       v                                              │
┌──────────────────────────────────────────────────┐ │
│          Validate & Prepare Search               │ │
│   - Get search term                              │ │
│   - Get selected directories ←────────────────────┘
│   - Get active filters                           │
│   - Get case sensitivity                         │
└──────────────────┬───────────────────────────────┘
                   │
                   v
           ┌───────────────┐
           │ SearchWorker  │ (Background Thread)
           │   Thread      │
           └───────┬───────┘
                   │
                   ├──→ progress signal ──→ Update status bar
                   │
                   ├──→ result signal ──────┐
                   │                        │
                   │                        v
                   │              ┌──────────────────┐
                   │              │ Categorize File  │
                   │              │  by FileType     │
                   │              └────────┬─────────┘
                   │                       │
                   │                       v
                   │              ┌──────────────────┐
                   │              │  Add to Results  │
                   │              │   Table/Grid     │
                   │              └────────┬─────────┘
                   │                       │
                   │                       ├──→ Update tab count
                   │                       ├──→ Update file count
                   │                       └──→ Sync grid view
                   │
                   └──→ finished signal ──┐
                                          │
                                          v
                                 ┌─────────────────┐
                                 │ Post-Processing │
                                 │ - Add to history│
                                 │ - Update autocmp│
                                 │ - Show notific. │
                                 └─────────────────┘

┌─────────────────┐
│ User Selection  │
└────────┬────────┘
         │
         ├──→ Table Selection Changed ──┐
         │                              │
         └──→ Grid Item Selected ───────┤
                                        │
                                        v
                               ┌────────────────┐
                               │ Update Preview │
                               │     Panel      │
                               └────────────────┘
                                        │
                                        ├──→ Load image
                                        ├──→ Load text
                                        └──→ Show metadata

┌──────────────┐
│ User Action  │
└──────┬───────┘
       │
       ├──→ Open ──────────→ os.startfile()
       │
       ├──→ Copy/Move ──────→ FileOperationWorker Thread
       │                              │
       │                              v
       │                     ┌─────────────────┐
       │                     │ Copy/Move Files │
       │                     │  with Progress  │
       │                     └─────────────────┘
       │
       ├──→ Export ────────→ ExportDialog
       │                         │
       │                         v
       │                    ┌──────────┐
       │                    │ CSV File │
       │                    └──────────┘
       │
       └──→ Save Preset ───→ SearchPresetsDialog
                                  │
                                  v
                             ┌─────────┐
                             │ JSON    │
                             │ Storage │
                             └─────────┘
```

## Signal/Slot Connections

```
Component                    Signal                      → Slot
─────────────────────────────────────────────────────────────────────

search_input                 returnPressed               → _start_search()
search_btn                   clicked                     → _start_search()
stop_btn                     clicked                     → _stop_search()

filter_chips                 filter_changed(list)        → _on_filter_changed(list)

search_history               search_selected(str, list)  → _load_search_from_history(...)

SearchWorker                 progress(int, str)          → _on_search_progress(...)
SearchWorker                 result(dict)                → _on_search_result(dict)
SearchWorker                 finished(int)               → _on_search_finished(int)
SearchWorker                 error(str)                  → _on_search_error(str)

result_tables[*]             itemSelectionChanged        → _on_selection_changed()

grid_view                    item_selected(str)          → _on_grid_item_selected(str)
grid_view                    item_double_clicked(str)    → _open_file_from_path(str)

list_view_btn                clicked                     → _set_view_mode("list")
grid_view_btn                clicked                     → _set_view_mode("grid")

open_btn                     clicked                     → _open_files()
copy_btn                     clicked                     → _copy_files()
move_btn                     clicked                     → _move_files()
export_btn                   clicked                     → _export_results()
presets_btn                  clicked                     → _show_presets_dialog()
clear_btn                    clicked                     → _clear_results()

theme_btn                    clicked(bool)               → _toggle_theme(bool)

FileOperationWorker          progress(int, str)          → _on_operation_progress(...)
FileOperationWorker          finished(int, int)          → _on_operation_finished(...)
FileOperationWorker          error(str)                  → _on_operation_error(str)
```

## State Management

```
Application State:
├── search_worker: Optional[SearchWorker]
├── operation_worker: Optional[FileOperationWorker]
├── dark_mode: bool
├── view_mode: str ("list" | "grid")
├── current_filter: List[str] (file extensions)
└── presets_dialog: SearchPresetsDialog

Search State:
├── search_term: str (from search_input.text())
├── case_sensitive: bool (from case_sensitive_cb.isChecked())
├── selected_paths: List[str] (from dir_tree.get_selected_paths())
└── active_filter: List[str] (from filter_chips.get_selected_filter())

Results State:
├── result_tables: Dict[FileType, ResultsTableWidget]
│   └── Each table contains file info rows
├── grid_view.items: List[Dict] (parallel to tables)
└── preview_panel.current_file: Optional[str]

Persistent State (JSON files):
├── ~/.smart_search_history.json
│   └── List[SearchHistory]
├── ~/.smart_search_favorites.json
│   └── Set[str] (directory paths)
└── ~/.smart_search_presets.json
    └── List[SearchPreset]
```

## Threading Model

```
┌─────────────────┐
│   Main Thread   │ (UI Thread)
│   (Qt Event     │
│    Loop)        │
└────────┬────────┘
         │
         ├──→ User interaction
         ├──→ UI updates
         ├──→ Signal emissions
         └──→ Slot executions
              │
              ├──→ Start SearchWorker ──────┐
              │                             │
              └──→ Start FileOperationWorker┐
                                            │
                                            │
┌───────────────────────────────────────────┼──────────────┐
│  Background Threads                       │              │
│                                           │              │
│  ┌─────────────────┐                     │              │
│  │ SearchWorker    │ ←────────────────────┘              │
│  │                 │                                     │
│  │ - Walk dirs     │                                     │
│  │ - Match files   │                                     │
│  │ - Emit results  │                                     │
│  └─────────────────┘                                     │
│                                                          │
│  ┌─────────────────────┐                                │
│  │ FileOperationWorker │ ←────────────────────────────────┘
│  │                     │
│  │ - Copy/move files   │
│  │ - Handle conflicts  │
│  │ - Emit progress     │
│  └─────────────────────┘
│
└────────────────────────────────────────────────────────────┘

Signals automatically use Qt's thread-safe signal/slot mechanism
to communicate back to main thread.
```

## Class Relationships

```
QMainWindow
    ↑
    │
SmartSearchWindow (original)
    ↑
    │
EnhancedSmartSearchWindow
    │
    ├──→ uses SearchHistoryWidget
    ├──→ uses QuickFilterChips
    ├──→ uses EnhancedDirectoryTree
    ├──→ uses FilePreviewPanel
    ├──→ uses GridViewWidget
    ├──→ uses SearchPresetsDialog
    ├──→ uses ExportDialog
    ├──→ uses KeyboardShortcutsDialog
    └──→ uses show_notification()

QThread
    ↑
    ├─ SearchWorker
    └─ FileOperationWorker

QWidget
    ↑
    ├─ SearchHistoryWidget
    ├─ QuickFilterChips
    ├─ FilePreviewPanel
    └─ GridViewWidget

QTreeWidget
    ↑
    ├─ DirectoryTreeWidget (original)
    └─ EnhancedDirectoryTree

QTableWidget
    ↑
    └─ ResultsTableWidget

QDialog
    ↑
    ├─ SearchPresetsDialog
    ├─ ExportDialog
    └─ KeyboardShortcutsDialog
```

## File Organization

```
smart_search/
│
├── Core Components
│   ├── ui.py                      # Original UI implementation
│   └── ui_enhancements.py         # New enhancement widgets
│
├── Examples & Integration
│   └── ui_enhanced_example.py     # Complete enhanced version
│
├── Documentation
│   ├── UX_IMPROVEMENTS_README.md  # User guide
│   ├── UI_ENHANCEMENTS_GUIDE.md   # Developer guide
│   └── COMPONENT_ARCHITECTURE.md  # This file
│
└── User Data (in home directory)
    ├── .smart_search_history.json
    ├── .smart_search_favorites.json
    └── .smart_search_presets.json
```

## Performance Characteristics

| Component           | Time Complexity | Space Complexity | Notes                    |
|---------------------|-----------------|------------------|--------------------------|
| SearchWorker        | O(n)            | O(1)             | n = total files          |
| ResultsTable        | O(n log n)      | O(n)             | Sorting enabled          |
| GridView            | O(n)            | O(n)             | Creates all widgets      |
| FilePreview         | O(1)            | O(1)             | Loads one file           |
| SearchHistory       | O(1) insert     | O(h)             | h = history size (50)    |
| DirectoryTree       | O(d)            | O(d)             | d = directory depth      |
| QuickFilter         | O(1)            | O(1)             | Pre-defined filters      |

## Memory Footprint

Estimated memory usage:

- **Base UI**: ~50 MB
- **Per 1000 results**: ~5 MB (list view)
- **Per 1000 results**: ~15 MB (grid view with thumbnails)
- **Preview panel**: +2-10 MB (depending on file)
- **Search history**: ~100 KB
- **Total typical**: 70-150 MB

## Extension Points

To add new features, implement at these points:

1. **New Filter Type**
   - Add to `QuickFilterChips.FILTERS`
   - Update signal handler

2. **New View Mode**
   - Create new widget inheriting `QWidget`
   - Add to center panel
   - Add toggle in view toolbar

3. **New Export Format**
   - Extend `ExportDialog`
   - Add format-specific writer

4. **New Preview Type**
   - Extend `FilePreviewPanel._preview_*` methods
   - Add file extension check

5. **New Menu Action**
   - Add to `_create_menu_bar()`
   - Create handler method
   - Add keyboard shortcut

This architecture ensures modularity, maintainability, and extensibility.

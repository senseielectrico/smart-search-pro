# Notes System - Quick Start Guide

Get started with the integrated notes system in 5 minutes!

## Installation

The notes system is already integrated into Smart Search Pro. No additional installation needed!

## Running the Example

```bash
cd C:\Users\ramos\.local\bin\smart_search
python notes\example_integration.py
```

This launches a standalone notes application with:
- Full notepad interface
- Quick note dialog (Ctrl+Shift+N)
- Example notes to explore
- Statistics viewer

## Basic Usage

### 1. Creating a Note

**Method 1: From the main panel**
1. Click "New Note"
2. Enter title
3. Type content
4. Add tags (comma-separated)
5. Select category
6. Click "Save" (or auto-saves in 30 seconds)

**Method 2: Quick note (Ctrl+Shift+N)**
1. Press `Ctrl+Shift+N` anywhere
2. Start typing
3. Press `Ctrl+Enter` to save and close
4. Or just close - it auto-saves!

### 2. Searching Notes

- Type in the search box at the top of the notes list
- Full-text search in titles, content, and tags
- Results update as you type

### 3. Organizing with Tags and Categories

**Categories:**
- Click "Categories" button
- Create categories with custom icons and colors
- Assign notes to categories from the dropdown

**Tags:**
- Add tags in the "Tags" field (comma-separated)
- Tags auto-complete from existing tags
- Filter by tag using the dropdown

### 4. Pinning Important Notes

- Click the "Pin" button in the toolbar
- Pinned notes appear at the top of the list
- Marked with a 📌 icon

### 5. Linking Notes to Files

1. Open a note
2. Click "Link File"
3. Select a file or folder
4. Note is now linked to that path

Use case: Keep notes about projects, documents, or folders!

## Editor Features

### Formatting Toolbar

- **B** - Bold text
- **I** - Italic text
- **U** - Underline text
- Headings dropdown - H1, H2, H3
- Bullet/Numbered lists
- Task lists with checkboxes
- Code blocks
- Tables
- Images

### Markdown Support

The editor supports Markdown syntax:

```markdown
# Heading 1
## Heading 2
### Heading 3

**bold** *italic* `code`

- Bullet list
1. Numbered list

☐ Task list
☑ Completed task

[Link](https://example.com)

![Image](path/to/image.png)
```

### Preview Mode

- Click "Preview" button to see rendered Markdown
- Split view shows editor and preview side-by-side

### Find and Replace

- Click "Find" button or press Ctrl+F
- Search and replace text
- Case sensitive and whole word options

## Keyboard Shortcuts

### Main Window
- `Ctrl+N` - New note
- `Ctrl+S` - Save note
- `Delete` - Delete current note
- `Ctrl+Shift+N` - Quick note dialog

### Editor
- `Ctrl+B` - Bold
- `Ctrl+I` - Italic
- `Ctrl+U` - Underline
- `Ctrl+F` - Find and replace

### Quick Note Dialog
- `Ctrl+Enter` - Save and close
- `Escape` - Close
- Auto-saves every 5 seconds

## Advanced Features

### Version History

Notes automatically save version history:
1. Each time you save, a new version is created
2. Last 10 versions are kept
3. Right-click a note → "View History" to restore

### Export/Import

**Export a note:**
1. Open the note
2. Click "Export"
3. Choose format: Markdown, Text, HTML, or JSON
4. Save to file

**Import notes:**
1. Click "Import"
2. Select JSON or text file
3. Note is imported into your collection

**Export all notes:**
```python
note_manager.export_all_notes(Path("./my_notes"))
```

### Statistics

Click "Show Statistics" to see:
- Total notes count
- Pinned notes
- Notes by category
- Top tags
- Tag usage

## Integration with Smart Search Pro

To integrate into your main Smart Search Pro window:

```python
from notes.note_manager import NoteManager
from ui.notepad_panel import NotepadPanel
from ui.quick_note_dialog import QuickNoteButton

# In your main window
note_manager = NoteManager(self.db)

# Add notes panel as tab
notepad = NotepadPanel(note_manager)
self.tabs.addTab(notepad, "📝 Notes")

# Add quick note button to toolbar
quick_note_btn = QuickNoteButton(note_manager, self)
toolbar.addWidget(quick_note_btn)
```

### Link Notes to Search Results

When viewing search results:
1. Right-click a file
2. Select "Create Note"
3. Note is created and linked to that file
4. View linked notes from the file's context menu

## Tips and Tricks

1. **Use the quick note dialog for rapid capture**
   - Press Ctrl+Shift+N anytime
   - Great for sudden ideas or reminders

2. **Tag consistently**
   - Use lowercase tags
   - Create a tagging system (e.g., #work, #personal, #urgent)

3. **Link notes to project folders**
   - Keep project documentation with the code
   - Right-click folder → "Notes" to see all linked notes

4. **Pin important notes**
   - Current tasks
   - Reference information
   - Quick access items

5. **Use categories for high-level organization**
   - Work, Personal, Learning, Projects, etc.
   - Tags for specific topics

6. **Export regularly**
   - Backup your notes
   - Share with others
   - Archive completed projects

## Troubleshooting

### Notes not saving
- Check database file permissions
- Look for error messages in status bar
- Database location: `~/.smart_search/smart_search.db`

### Search not working
- Full-text search requires exact word matches
- Try partial words with wildcards: `prog*`
- Check if notes are actually created

### Slow performance
- Vacuum database: `note_manager.db.vacuum()`
- Check database size
- Optimize if >100MB

### Quick note dialog not appearing
- Check if Ctrl+Shift+N is captured by another app
- Try clicking "Quick Note" button instead
- Restart application

## Next Steps

1. **Run the example**: `python notes\example_integration.py`
2. **Create your first note**
3. **Explore the features**
4. **Organize with tags and categories**
5. **Try the quick note dialog**
6. **Link notes to files**

## Support

- Read full documentation: `notes\README.md`
- Check examples: `notes\example_integration.py`
- Run tests: `python test_notes_system.py`

Enjoy your new integrated notes system! 📝✨

# Smart Search - Quick Start

## Installation (First Time)

Run the installation script:

```bash
install.bat
```

It will:
1. Check Python installation
2. Install all dependencies (PyQt6, pywin32, comtypes)
3. Verify everything works
4. Optionally create desktop shortcuts

## Running the Application

### Option 1: Simple Launch (Recommended)
```bash
start.bat
```
- Launches without console window
- Professional appearance

### Option 2: With Dependency Check
```bash
start.bat --check
```
- Verifies dependencies before launch
- Good for first-time setup

### Option 3: Debug Mode
```bash
start.bat --console
```
- Shows console window
- Displays error messages
- For troubleshooting

### Option 4: Double-Click
Simply double-click `smart_search.pyw` file

## Basic Usage

1. **Select Directories**
   - Check/uncheck folders in the left panel
   - Search will only scan selected folders

2. **Enter Search Terms**
   - Type in the search box at the top
   - Separate multiple keywords with `*`
   - Example: `python * script` finds files containing both words

3. **Choose Search Type**
   - Filename: Search in file names
   - Content: Search inside files (slower)

4. **Click Search**
   - Press Enter or click the Search button
   - Results appear in tabs by file type

5. **Work with Results**
   - Open files with default application
   - Copy or move files
   - View file location in Explorer

## File Organization

- `smart_search.pyw` - Production executable (no console)
- `start.bat` - Main launcher (recommended)
- `run.bat` - Alternative launcher
- `install.bat` - Installation & setup
- `main.py` - Application entry point
- `verify_setup.py` - Dependency verification

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+F   | Focus search |
| Ctrl+O   | Open selected |
| Ctrl+L   | Clear results |
| Enter    | Start search |

## Troubleshooting

**Problem:** Application won't start
```bash
start.bat --console
```
- Shows error messages
- Try with `--check` flag

**Problem:** "No module named PyQt6"
```bash
pip install PyQt6
```

**Problem:** Windows Search not working
- Application falls back to filesystem search
- Still works, just slower

## Advanced

For detailed documentation:
- `PRODUCTION_GUIDE.md` - Complete setup & deployment guide
- `README.md` - Full project documentation

## Support

If you encounter issues:

1. Run: `start.bat --console` for error details
2. Check: `%USERPROFILE%\.smart_search\error.log`
3. Verify: `python verify_setup.py`

---

**Quick Reference:**
- Install: `install.bat`
- Run: `start.bat`
- Debug: `start.bat --console`
- Check: `start.bat --check`

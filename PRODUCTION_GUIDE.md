# Smart Search - Production Deployment Guide

## Overview

Smart Search is a professional Windows file search application with a modern PyQt6 interface. This guide covers setup, deployment, and usage of the production-ready version.

**Version:** 1.0.0
**Platform:** Windows 7 SP1, 8.1, 10, 11
**Python:** 3.8+

---

## Quick Start

### Option 1: Simple Double-Click Launch
Simply double-click `smart_search.pyw` or `start.bat` to launch the application.

```
start.bat
```

### Option 2: Console Mode (Debugging)
For troubleshooting, run with console window visible:

```
start.bat --console
```

### Option 3: Verify Dependencies First
Before first use, verify all dependencies:

```
start.bat --check
```

### Option 4: Using run.bat
Alternative launcher with more control:

```
run.bat
run.bat --console
```

---

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Windows 7 SP1 or later

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or manually install required packages:

```bash
pip install PyQt6>=6.6.0
pip install pywin32
pip install comtypes
```

### Step 2: Complete pywin32 Setup (Important!)

After installing pywin32, run the post-install script:

```bash
# From the smart_search directory
python -m pip install --upgrade pywin32
python Scripts/pywin32_postinstall.py -install
```

Or using the full path:

```bash
python -m pip install --upgrade pywin32
python -c "import sys; from pywin32_postinstall import install; install(['-install'])"
```

### Step 3: Verify Installation

Run the dependency checker:

```bash
python verify_setup.py
```

Expected output:
```
[OK] Python                            OK (version: 3.10.2)
[OK] Windows Platform                 OK
[OK] PyQt6                             OK (version: 6.6.0)
[OK] pywin32                           OK (version: 306)
[OK] comtypes                          OK (version: 1.2.0)
[OK] Local Module: main                OK
[OK] Local Module: backend             OK
[OK] Local Module: ui                  OK
...
Summary: 11/11 components OK
```

---

## File Structure

```
smart_search/
├── smart_search.pyw           # Production executable (no console)
├── main.py                    # Application entry point
├── backend.py                 # Windows Search API integration
├── ui.py                      # PyQt6 user interface
├── categories.py              # File classification system
├── classifier.py              # File type classifier
├── file_manager.py            # Directory tree manager
├── utils.py                   # Utility functions
├── config.py                  # Configuration management
├── start.bat                  # Main launcher script
├── run.bat                    # Alternative launcher
├── install.bat                # Installation script
├── verify_setup.py            # Dependency verification
├── requirements.txt           # Python dependencies
└── PRODUCTION_GUIDE.md        # This file
```

---

## Usage Guide

### Launching the Application

#### Method 1: Direct Execution (Recommended)
```bash
start.bat
```
- No console window visible
- Professional appearance
- Uses `pythonw.exe` if available

#### Method 2: With Dependency Check
```bash
start.bat --check
```
- Verifies all dependencies before launching
- Good for first-time setup

#### Method 3: Console Mode
```bash
start.bat --console
```
- Shows console window
- Displays error messages
- Useful for debugging

### Application Features

#### Search Options
- **Filename Search:** Find files by name pattern
- **Content Search:** Search inside file contents
- **Multiple Keywords:** Separate with `*` (e.g., `python * script`)

#### Directory Selection
- Check/uncheck directories in the left panel
- Selections are saved between sessions
- Supports partial selection (mixed state)

#### Results Management
- Results organized by file type (tabs)
- Sort by name, size, date, or category
- Right-click context menu for file operations

#### File Operations
- **Open:** Open selected files with default application
- **Open Location:** Show in Windows Explorer
- **Copy To:** Copy selected files to another location
- **Move To:** Move selected files to another location

#### Theme Support
- Toggle between light and dark themes
- Settings saved automatically
- Dark theme optimized for extended use

---

## Troubleshooting

### Issue: "ImportError: No module named 'PyQt6'"

**Solution:** Install PyQt6
```bash
pip install PyQt6>=6.6.0
```

### Issue: "ModuleNotFoundError: No module named 'win32com'"

**Solution:** Install and setup pywin32
```bash
pip install pywin32
python -m pip install --upgrade pywin32
python Scripts/pywin32_postinstall.py -install
```

### Issue: Application starts but crashes immediately

**Solution:** Run with console to see error details
```bash
start.bat --console
```

Then check:
1. All imports succeed: `python -c "import main"`
2. Dependencies are installed: `start.bat --check`
3. Error log: `%USERPROFILE%\.smart_search\error.log`

### Issue: "Windows Search not available"

This is normal on some systems. The application falls back to filesystem search.

**Workaround:**
- Application still works but may be slower
- Index more folders in Windows Search settings

### Issue: "Access Denied" errors

**Solutions:**
- Run as Administrator for system directories
- Check folder permissions
- Exclude protected folders from search

### Issue: Slow search performance

**Solutions:**
1. Reduce number of selected directories
2. Disable "Search Content" if not needed
3. Index directories in Windows Search
4. Check system resources (disk, CPU)

---

## Configuration

### Application Settings

Settings are stored in:
```
%USERPROFILE%\.smart_search\config.json
```

Configuration includes:
- Theme preference (light/dark)
- Window size and position
- Selected directories

### Error Logging

Error logs are saved to:
```
%USERPROFILE%\.smart_search\error.log
```

To view errors:
```bash
type "%USERPROFILE%\.smart_search\error.log"
```

### Directory Tree State

Selected directories are saved in:
```
%USERPROFILE%\.smart_search\directory_tree.json
```

---

## Advanced Usage

### Command-Line Arguments

#### For Developers
```bash
# Run with console for debugging
python main.py

# Run tests
pytest
pytest --cov
pytest tests/test_backend.py -v
```

#### For End Users
```bash
# Standard launch (no console)
start.bat

# With dependency check
start.bat --check

# Debug mode (with console)
start.bat --console
```

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+F | Focus search input |
| Ctrl+O | Open selected file |
| Ctrl+L | Clear results |
| Enter | Start search |
| Esc | Cancel search |

### Export Results

Copy selected file paths using "Copy Path" from context menu:
1. Right-click file in results
2. Select "Copy Path"
3. Paste paths into text editor

---

## Performance Optimization

### For Faster Searches

1. **Index Directories in Windows Search**
   - Settings > Search > Searching Windows
   - Add commonly used directories to index

2. **Reduce Search Scope**
   - Select only necessary directories
   - Avoid searching entire drive

3. **Use Filename Search Only**
   - Content search is slower
   - Use only when necessary

4. **Regular Maintenance**
   - Close other applications
   - Check disk space
   - Update Windows Search index

### System Requirements

**Minimum:**
- Processor: 2 GHz
- RAM: 2 GB
- Disk: 100 MB free space

**Recommended:**
- Processor: 2.5+ GHz
- RAM: 4+ GB
- Disk: 500 MB free space

---

## Uninstallation

### Remove Application

1. Delete the `smart_search` folder
2. Delete configuration folder: `%USERPROFILE%\.smart_search`

### Remove Python Packages (Optional)

```bash
pip uninstall PyQt6 pywin32 comtypes
```

---

## Support & Documentation

### Built-in Help
- Hover over buttons for tooltips
- Check status bar for operation messages

### Additional Resources
- `README.md` - Project overview
- `EXAMPLES.md` - Usage examples
- `USAGE_GUIDE.md` - Detailed feature guide

### Error Reporting

If you encounter errors:

1. Run with console: `start.bat --console`
2. Note the error message
3. Check error log: `%USERPROFILE%\.smart_search\error.log`
4. Run verification: `python verify_setup.py`

---

## Version History

### v1.0.0 (2025-12-11)
- Initial production release
- Full PyQt6 interface
- Windows Search API integration
- File classification system
- Theme support
- Directory tree management
- Error handling and logging

---

## License & Credits

Smart Search v1.0.0
Production-ready file search application for Windows

Developed with Python, PyQt6, and Windows Search APIs.

---

## Deployment Checklist

Before deploying to production:

- [ ] All dependencies installed: `start.bat --check`
- [ ] Application launches correctly: `start.bat`
- [ ] Search functionality works
- [ ] File operations functional (open, copy, move)
- [ ] Error logging working
- [ ] Configuration saving/loading
- [ ] Both launchers working (start.bat, run.bat)
- [ ] Keyboard shortcuts responsive
- [ ] Theme toggle functional
- [ ] No console window visible with start.bat

---

**Last Updated:** 2025-12-11
**Status:** Production Ready

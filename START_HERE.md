# Smart Search v1.0.0 - START HERE

Welcome to Smart Search - A Professional Windows File Search Application

**Status:** Production Ready | **Version:** 1.0.0 | **Date:** 2025-12-11

---

## What is Smart Search?

Smart Search is a modern, professional file search application for Windows with:

- Fast filename and content search using Windows Search API
- Clean PyQt6 graphical interface
- Directory selection with persistent state
- File classification by type
- Dark/light themes
- File operations (open, copy, move)
- Complete error handling and logging

---

## Getting Started (3 Steps)

### Step 1: Install Dependencies (2 minutes)

```bash
install.bat
```

This runs an automated installer that:
- Verifies Python 3.8+ is installed
- Installs PyQt6, pywin32, and comtypes
- Configures everything automatically
- Optionally creates a desktop shortcut

### Step 2: Verify Installation (1 minute)

After installation, verify everything works:

```bash
python verify_setup.py
```

Expected output: All components [OK]

### Step 3: Launch Application (Click)

```bash
start.bat
```

Or simply double-click `smart_search.pyw`

---

## Documentation Guide

### For Users
1. **START_HERE.md** ← You are here (Overview)
2. **QUICK_START.md** - Quick reference guide (5 min read)
3. **PRODUCTION_GUIDE.md** - Complete feature guide (15 min read)

### For Administrators/Deployers
1. **DEPLOYMENT_SUMMARY.txt** - Overview and checklist
2. **FINAL_CHECKLIST.md** - Verification and sign-off
3. **PRODUCTION_GUIDE.md** - Troubleshooting section

---

## Quick Launcher Commands

```bash
start.bat                    # Normal launch (recommended)
start.bat --console          # Debug mode (shows errors)
start.bat --check            # Verify dependencies before launch
smart_search.pyw             # Direct execution
```

---

## Basic Usage

1. **Select Directories** - Check folders in the left panel
2. **Enter Search Terms** - Type in the search box (separate multiple with `*`)
3. **Choose Search Type** - Check Filename or Content
4. **Click Search** - Or press Enter
5. **Use Results** - Open, copy, or move files

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+F   | Focus search input |
| Ctrl+O   | Open selected files |
| Ctrl+L   | Clear results |
| Enter    | Start search |

---

## File Organization

```
smart_search/
├── smart_search.pyw           Main executable (no console)
├── start.bat                  Primary launcher
├── run.bat                    Alternative launcher
├── install.bat                Installation script
│
├── QUICK_START.md             Quick reference (READ NEXT)
├── PRODUCTION_GUIDE.md        Complete guide
├── DEPLOYMENT_SUMMARY.txt     Admin overview
│
├── verify_setup.py            Dependency checker
├── test_production.py         Environment tester
└── requirements.txt           Python dependencies
```

---

## System Requirements

**Minimum:**
- Windows 7 SP1 or later
- Python 3.8+
- 2 GB RAM
- 100 MB disk space

**Recommended:**
- Windows 10 or 11
- Python 3.10+
- 4 GB RAM
- SSD storage

---

## Common Issues

| Issue | Solution |
|-------|----------|
| App won't start | Run `start.bat --console` to see errors |
| "No module named PyQt6" | Run `install.bat` or `pip install PyQt6` |
| Search is slow | Reduce search scope or use filename-only |
| "Access Denied" errors | Run as Administrator or exclude folders |
| Windows Search unavailable | App falls back to filesystem (slower but works) |

More solutions in **PRODUCTION_GUIDE.md**

---

## What Gets Installed

### Python Packages
- **PyQt6 6.6.0+** - Graphics framework
- **pywin32** - Windows API for search
- **comtypes** - COM library

### User Files (Created Automatically)
- `~/.smart_search/config.json` - Settings
- `~/.smart_search/directory_tree.json` - Saved selections
- `~/.smart_search/error.log` - Errors and logs

### Desktop Shortcut (Optional)
- Created during installation
- Points to `start.bat`

---

## Next Steps

### Read These In Order
1. You've read this (Overview) ✓
2. **QUICK_START.md** (Quick reference)
3. **PRODUCTION_GUIDE.md** (Full features)

### Or Just Run It
```bash
install.bat
start.bat
```

---

## Verify Everything Works

```bash
# Check dependencies
python verify_setup.py

# Run tests
python test_production.py

# Launch with debug
start.bat --console
```

---

## Features Overview

### Search
- Filename search
- Content search
- Multiple keywords
- Windows Search API
- Filesystem fallback

### Interface
- Modern PyQt6 design
- Directory tree selection
- Tabbed results
- Real-time progress
- Light/dark themes

### Files
- Open with default app
- Show in Explorer
- Copy to folder
- Move to folder

### Reliability
- Friendly error messages
- Complete error logging
- Dependency checking
- Configuration saving

---

## Support Resources

1. **Error Logs** - `%USERPROFILE%\.smart_search\error.log`
2. **Dependency Check** - `python verify_setup.py`
3. **Troubleshooting** - See PRODUCTION_GUIDE.md
4. **Quick Help** - See QUICK_START.md

---

## Quick Links

| Need | Read/Run |
|------|----------|
| Installation | install.bat |
| Launch | start.bat |
| Quick help | QUICK_START.md |
| Full guide | PRODUCTION_GUIDE.md |
| Deploy info | DEPLOYMENT_SUMMARY.txt |
| Check deps | verify_setup.py |

---

## Version Info

**Smart Search v1.0.0**
- Release: 2025-12-11
- Status: Production Ready
- Python: 3.8+
- Windows: 7 SP1+

---

## Ready to Start?

### Option A: Fastest (5 min)
```bash
install.bat && start.bat
```

### Option B: Safe (10 min)
```bash
install.bat
python verify_setup.py
start.bat
```

### Option C: Thorough (20 min)
1. Read QUICK_START.md
2. Run install.bat
3. Run verify_setup.py
4. Read PRODUCTION_GUIDE.md
5. Launch start.bat

---

## Questions?

1. Check **QUICK_START.md** for quick answers
2. Check **PRODUCTION_GUIDE.md** for detailed help
3. Run `start.bat --console` to see error messages
4. Check `%USERPROFILE%\.smart_search\error.log`

---

## Document Roadmap

```
START_HERE.md (Overview)
    ↓
QUICK_START.md (Quick Reference)
    ↓
PRODUCTION_GUIDE.md (Complete Guide)
    ↓
DEPLOYMENT_SUMMARY.txt (Admin Info)
    ↓
FINAL_CHECKLIST.md (Verification)
```

---

**Welcome to Smart Search!**

Next step: Read **QUICK_START.md** (5 min) or run **install.bat** now

For complete information: See **PRODUCTION_GUIDE.md**

For deployment: Follow **DEPLOYMENT_SUMMARY.txt**

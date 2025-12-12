# Smart Search - Installation Guide

## Quick Start

### Windows (Recommended)

1. **Run installer** (automated):
   ```bash
   install.bat
   ```

2. **Launch application**:
   ```bash
   run.bat
   ```

### Manual Installation

1. **Install Python 3.8+** (if not already installed)
   - Download from: https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"

2. **Install PyQt6**:
   ```bash
   pip install PyQt6
   ```

   Or install from requirements:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python ui.py
   ```

## Verification

Test that PyQt6 is installed correctly:

```bash
python -c "import PyQt6.QtWidgets; print('PyQt6 OK')"
```

Expected output: `PyQt6 OK`

## System Requirements

### Minimum
- **OS**: Windows 10/11
- **Python**: 3.8+
- **RAM**: 2 GB
- **Disk**: 100 MB (including dependencies)

### Recommended
- **OS**: Windows 11
- **Python**: 3.11+
- **RAM**: 4 GB
- **Disk**: 200 MB
- **Display**: 1920x1080 or higher

## Dependencies

The application requires only PyQt6:

```
PyQt6 >= 6.6.0
├── PyQt6-Qt6 >= 6.6.0
└── PyQt6-sip >= 13.6.0
```

## Common Issues

### Issue: "ModuleNotFoundError: No module named 'PyQt6'"

**Solution**:
```bash
pip install PyQt6
```

### Issue: "pip is not recognized"

**Solution**: Python not in PATH. Reinstall Python with "Add to PATH" option checked.

### Issue: Application doesn't start

**Solutions**:
1. Check Python version: `python --version` (must be 3.8+)
2. Verify PyQt6: `python -c "import PyQt6; print('OK')"`
3. Run with error output: `python ui.py 2> errors.txt`

### Issue: Permission errors during search

**Solution**: Run as Administrator or exclude protected directories (System32, Program Files, etc.)

## Uninstallation

Remove PyQt6:
```bash
pip uninstall PyQt6
```

Remove all dependencies:
```bash
pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip
```

## Development Setup

For development with additional tools:

```bash
# Install development dependencies
pip install PyQt6 pytest black flake8 mypy

# Run tests
pytest tests/

# Format code
black ui.py

# Type checking
mypy ui.py
```

## Portable Installation

Create a portable version without system Python:

1. Download Python embeddable package
2. Extract to `smart_search/python/`
3. Install pip in embedded Python
4. Install PyQt6
5. Create launcher script pointing to embedded Python

## Alternative Installation Methods

### Using conda
```bash
conda create -n smart-search python=3.11
conda activate smart-search
pip install PyQt6
python ui.py
```

### Using pipenv
```bash
pipenv install PyQt6
pipenv run python ui.py
```

### Using poetry
```bash
poetry add PyQt6
poetry run python ui.py
```

## Updating

Update to latest version:
```bash
pip install --upgrade PyQt6
```

## Support

For issues or questions:
1. Check this installation guide
2. Review README.md for usage instructions
3. Check Python and PyQt6 versions
4. Run with verbose output: `python -v ui.py`

## License

Free to use under MIT License

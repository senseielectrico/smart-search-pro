# File Unlocking Tools - Quick Start Guide

## Installation

```bash
# Already included with Smart Search Pro
# Optional dependencies for enhanced features:
pip install msoffcrypto-tool pikepdf
```

## Launch GUI Tools

### From Python

```python
from PyQt6.QtWidgets import QApplication
from ui.file_unlocker_dialog import FileUnlockerDialog
from ui.permission_dialog import PermissionDialog

app = QApplication([])

# File Unlocker
unlocker_dialog = FileUnlockerDialog()
unlocker_dialog.exec()

# Permission Fixer
permission_dialog = PermissionDialog()
permission_dialog.exec()
```

### From Command Line

```bash
# File Unlocker GUI
python -c "from PyQt6.QtWidgets import QApplication; from ui.file_unlocker_dialog import FileUnlockerDialog; app = QApplication([]); d = FileUnlockerDialog(); d.exec()"

# Permission Fixer GUI
python -c "from PyQt6.QtWidgets import QApplication; from ui.permission_dialog import PermissionDialog; app = QApplication([]); d = PermissionDialog(); d.exec()"
```

## Common Tasks

### 1. Unlock File Locked by Another Application

**GUI Method:**
1. Open File Unlocker dialog
2. Browse to locked file
3. Click "Scan for Locks"
4. Review locking processes
5. Click "Unlock File(s)"

**Code Method:**
```python
from tools.file_unlocker import unlock_file

# Simple one-liner
if unlock_file(r'C:\locked_file.nwd'):
    print("File unlocked successfully")
```

**Command Line:**
```bash
python -m tools.file_unlocker "C:\locked_file.nwd"
```

### 2. Fix Broken Permissions

**GUI Method:**
1. Open Permission Fixer dialog
2. Browse to file/folder
3. Click "Load Permissions"
4. Review current permissions
5. Click "Take Ownership"
6. Click "Grant Full Control"

**Code Method:**
```python
from tools.permission_fixer import take_ownership, grant_full_control

# Take ownership and grant full control
take_ownership(r'C:\inaccessible_folder', recursive=True)
grant_full_control(r'C:\inaccessible_folder', recursive=True)
```

**Command Line:**
```bash
# Take ownership recursively
python -m tools.permission_fixer --take-ownership --recursive "C:\folder"

# Grant full control
python -m tools.permission_fixer --grant-full --recursive "C:\folder"
```

### 3. Decrypt Password-Protected Office File

**Code Method:**
```python
from tools.file_decryptor import FileDecryptor

with FileDecryptor() as decryptor:
    result = decryptor.decrypt_office_file(
        r'C:\protected.xlsx',
        password='mypassword',  # If known
        try_common=True,        # Try common passwords
        output_path=r'C:\decrypted.xlsx'
    )

    if result['success']:
        print(f"Password: {result['password_found']}")
```

**Command Line:**
```bash
# With known password
python -m tools.file_decryptor --password "secret" "C:\file.xlsx"

# Try common passwords
python -m tools.file_decryptor "C:\file.xlsx"
```

### 4. Clone Locked CAD File

**Code Method:**
```python
from tools.cad_file_handler import clone_cad_file

clone_path = clone_cad_file(r'C:\locked_model.nwd')
if clone_path:
    print(f"Clone created: {clone_path}")
```

**Command Line:**
```bash
python -m tools.cad_file_handler --clone --output "C:\copy.nwd" "C:\locked.nwd"
```

### 5. Batch Unlock Multiple Files

**GUI Method:**
1. Open File Unlocker dialog
2. Click "Add File" for each file
3. Enable options as needed
4. Click "Unlock File(s)"

**Code Method:**
```python
from tools.file_unlocker import FileUnlocker

unlocker = FileUnlocker()
files = [
    r'C:\file1.txt',
    r'C:\file2.docx',
    r'C:\file3.pdf'
]

results = unlocker.batch_unlock(files)

for result in results:
    print(f"{result['file']}: {'SUCCESS' if result['success'] else 'FAILED'}")
```

## Real-World Scenarios

### Scenario 1: Navisworks File Won't Delete

```python
from tools.file_unlocker import FileUnlocker

unlocker = FileUnlocker()

# Find what's locking it
processes = unlocker.get_locking_processes(r'C:\project\model.nwd')

for p in processes:
    print(f"{p.process_name} (PID: {p.pid})")
    # Close the handle without killing Navisworks
    unlocker.close_handle(p.pid, p.handle_value)
```

### Scenario 2: Inherited Folder Permissions Broken

```python
from tools.permission_fixer import PermissionFixer

fixer = PermissionFixer()

# Backup first
fixer.backup_permissions(r'C:\important_folder')

# Take ownership recursively
fixer.take_ownership(r'C:\important_folder', recursive=True)

# Grant full control to current user
fixer.grant_full_control(r'C:\important_folder', recursive=True)

# Remove any deny ACEs
fixer.remove_deny_aces(r'C:\important_folder', recursive=True)
```

### Scenario 3: Recover Password-Protected Excel

```python
from tools.file_decryptor import FileDecryptor

with FileDecryptor() as decryptor:
    # First check if it's encrypted
    detection = decryptor.detect_encryption(r'C:\report.xlsx')

    if detection['encrypted']:
        print(f"Encryption types: {detection['encryption_types']}")

        # Try to decrypt
        result = decryptor.decrypt_office_file(
            r'C:\report.xlsx',
            try_common=True  # Try common passwords
        )

        if result['success']:
            print(f"Decrypted with password: {result['password_found']}")
            print(f"Saved to: {result['output_path']}")
```

### Scenario 4: Access Locked AutoCAD Drawing

```python
from tools.cad_file_handler import CADFileHandler

with CADFileHandler() as handler:
    # Clone the locked DWG
    result = handler.clone_for_readonly_access(
        r'C:\drawings\locked.dwg',
        output_path=r'C:\temp\readable.dwg'
    )

    if result['success']:
        print(f"Clone method: {result['method']}")
        print(f"Clone path: {result['clone_path']}")
        # Now open the clone in viewer
```

## Integration with Smart Search Pro

### Add to Context Menu

```python
# In your search results context menu:

def _add_unlock_menu_items(self, menu, file_path):
    from tools.file_unlocker import unlock_file
    from tools.permission_fixer import take_ownership

    unlock_action = menu.addAction("🔓 Unlock File")
    unlock_action.triggered.connect(
        lambda: self._unlock_and_refresh(file_path)
    )

    perms_action = menu.addAction("🔑 Fix Permissions")
    perms_action.triggered.connect(
        lambda: self._fix_permissions_and_refresh(file_path)
    )

def _unlock_and_refresh(self, file_path):
    if unlock_file(file_path):
        QMessageBox.information(self, "Success", "File unlocked")
        self.refresh_results()
```

### Add to Tools Menu

```python
# In main window:

tools_menu = menubar.addMenu("Tools")

unlock_dialog_action = tools_menu.addAction("File Unlocker...")
unlock_dialog_action.setShortcut("Ctrl+Shift+U")
unlock_dialog_action.triggered.connect(self._open_file_unlocker)

perms_dialog_action = tools_menu.addAction("Permission Fixer...")
perms_dialog_action.setShortcut("Ctrl+Shift+P")
perms_dialog_action.triggered.connect(self._open_permission_dialog)
```

## Troubleshooting

### "Access Denied" Errors

**Solution:** Run as Administrator

```bash
# Right-click your terminal/IDE and "Run as Administrator"
# Or use runas:
runas /user:Administrator python script.py
```

### "Not running as Admin" Warning

**Check:**
```python
from tools.file_unlocker import FileUnlocker

unlocker = FileUnlocker()
if not unlocker.is_admin():
    print("Not admin - run as administrator")
```

### Handle Enumeration Fails

**Common causes:**
- Not running as admin
- Security software blocking
- Insufficient privileges

**Solution:**
```python
# Enable all required privileges first
from tools.permission_fixer import PermissionFixer

fixer = PermissionFixer()
# Privileges are automatically enabled on initialization
```

### Decryption Fails

**Check dependencies:**
```python
try:
    import msoffcrypto
    print("Office decryption available")
except ImportError:
    print("Install: pip install msoffcrypto-tool")

try:
    import pikepdf
    print("PDF decryption available")
except ImportError:
    print("Install: pip install pikepdf")
```

## Security Checklist

Before using these tools:

- [ ] I have administrator privileges
- [ ] I own the file or have authorization
- [ ] I've backed up important files
- [ ] I understand the security implications
- [ ] I've verified this is legal in my jurisdiction
- [ ] I've documented the operation reason
- [ ] I'm not violating any policies

## Quick Reference

### File Unlocker Methods

```python
unlocker = FileUnlocker()

# Check admin status
unlocker.is_admin()

# Find locking processes
unlocker.get_locking_processes(file_path)

# Close specific handle
unlocker.close_handle(pid, handle_value)

# Kill process
unlocker.kill_locking_process(pid, force=True)

# Remove attributes
unlocker.remove_file_attributes(file_path)

# Full unlock
unlocker.unlock_file(file_path, kill_process=False)
```

### Permission Fixer Methods

```python
fixer = PermissionFixer()

# View permissions
fixer.get_current_permissions(path)

# Backup/restore
fixer.backup_permissions(path)
fixer.restore_permissions(path)

# Take ownership
fixer.take_ownership(path, recursive=True)

# Grant access
fixer.grant_full_control(path, recursive=True)

# Remove deny ACEs
fixer.remove_deny_aces(path, recursive=True)
```

### File Decryptor Methods

```python
with FileDecryptor() as decryptor:
    # Detect encryption
    decryptor.detect_encryption(file_path)

    # Decrypt Office
    decryptor.decrypt_office_file(file_path, password=None)

    # Decrypt PDF
    decryptor.decrypt_pdf(file_path, password=None)

    # Decrypt ZIP
    decryptor.decrypt_zip(file_path, password=None)

    # Remove EFS
    decryptor.remove_efs_encryption(file_path)
```

### CAD Handler Methods

```python
with CADFileHandler() as handler:
    # Detect type
    handler.detect_cad_type(file_path)

    # Clone file
    handler.clone_for_readonly_access(file_path, output_path)

    # Extract metadata
    handler.extract_metadata(file_path)

    # Read locked file
    handler.read_locked_file(file_path, output_path)
```

## Need More Help?

- Read: `tools/README.md` - Comprehensive documentation
- Read: `FILE_UNLOCKING_IMPLEMENTATION.md` - Technical details
- Enable debug logging:
  ```python
  import logging
  logging.basicConfig(level=logging.DEBUG)
  ```

## One-Liner Examples

```python
# Quick unlock
from tools.file_unlocker import unlock_file; unlock_file(r'C:\file.txt')

# Quick permission fix
from tools.permission_fixer import take_ownership, grant_full_control; take_ownership(r'C:\folder', True); grant_full_control(r'C:\folder', True)

# Quick decrypt
from tools.file_decryptor import decrypt_file; decrypt_file(r'C:\file.xlsx')

# Quick CAD clone
from tools.cad_file_handler import clone_cad_file; print(clone_cad_file(r'C:\model.nwd'))
```

## Support

For issues or questions:
1. Check this quick start guide
2. Review tools/README.md
3. Read FILE_UNLOCKING_IMPLEMENTATION.md
4. Enable debug logging
5. Verify administrator privileges

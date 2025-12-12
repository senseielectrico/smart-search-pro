# Smart Search Pro - File Unlocking and Decryption Tools

Advanced toolkit for handling locked, encrypted, and inaccessible files on Windows.

## SECURITY WARNING

These tools are powerful and can modify system resources, file permissions, and process states. They should only be used on files you own or have explicit authorization to access.

**Misuse of these tools may:**
- Violate computer security policies
- Break laws in your jurisdiction
- Cause data corruption or loss
- Compromise system security
- Violate software licenses

**Always:**
- Verify you have legal authority to access the files
- Create backups before modifying permissions or decrypting files
- Understand the implications of each operation
- Use with caution in production environments

## Requirements

### Python Packages
```bash
pip install pywin32 psutil
```

### Optional Packages (for enhanced features)
```bash
# Office document decryption
pip install msoffcrypto-tool

# PDF decryption
pip install pikepdf

# PyQt6 for GUI dialogs
pip install PyQt6
```

### Windows Requirements
- Windows 7 or later
- Administrator privileges for most operations
- NTFS file system for permission operations

## Components

### 1. FileUnlocker - Remove File Locks

**Features:**
- Detect which process has a file locked
- Enumerate all system handles (requires admin)
- Force close handles from other processes
- Kill locking processes
- Remove read-only/hidden/system attributes
- Safe mode: copy file instead of forcing unlock

**Usage:**

```python
from tools.file_unlocker import FileUnlocker

unlocker = FileUnlocker()

# Find processes locking a file
processes = unlocker.get_locking_processes(r'C:\locked_file.txt')
for p in processes:
    print(f"Process: {p.process_name} (PID: {p.pid})")

# Unlock file
result = unlocker.unlock_file(
    r'C:\locked_file.txt',
    kill_process=False,  # Don't kill processes
    safe_mode=False      # Try to force unlock
)

print(f"Success: {result['success']}")
print(f"Handles closed: {result['handles_closed']}")
```

**Command Line:**
```bash
# List locking processes
python -m tools.file_unlocker --list "C:\locked_file.txt"

# Unlock file
python -m tools.file_unlocker "C:\locked_file.txt"

# Force unlock with process kill
python -m tools.file_unlocker --kill "C:\locked_file.txt"
```

**GUI:**
```python
from ui.file_unlocker_dialog import FileUnlockerDialog
from PyQt6.QtWidgets import QApplication

app = QApplication([])
dialog = FileUnlockerDialog()
dialog.exec()
```

### 2. PermissionFixer - Repair Permissions

**Features:**
- Take ownership of files/folders
- Grant full control to current user
- Remove deny ACEs
- Reset permissions to defaults
- Recursive operations
- Backup and restore permissions

**Usage:**

```python
from tools.permission_fixer import PermissionFixer

fixer = PermissionFixer()

# View current permissions
perms = fixer.get_current_permissions(r'C:\inaccessible_folder')
print(f"Owner: {perms['owner']}")
for ace in perms['aces']:
    print(f"{ace['type']}: {ace['account']} - {ace['permissions']}")

# Take ownership
result = fixer.take_ownership(
    r'C:\inaccessible_folder',
    recursive=True
)

# Grant full control
result = fixer.grant_full_control(
    r'C:\inaccessible_folder',
    recursive=True
)

# Remove deny ACEs
result = fixer.remove_deny_aces(
    r'C:\inaccessible_folder',
    recursive=True
)
```

**Command Line:**
```bash
# Show permissions
python -m tools.permission_fixer --show "C:\folder"

# Take ownership
python -m tools.permission_fixer --take-ownership "C:\folder"

# Grant full control recursively
python -m tools.permission_fixer --grant-full --recursive "C:\folder"
```

**GUI:**
```python
from ui.permission_dialog import PermissionDialog
from PyQt6.QtWidgets import QApplication

app = QApplication([])
dialog = PermissionDialog()
dialog.exec()
```

### 3. FileDecryptor - Handle Encrypted Files

**Features:**
- Detect EFS, Office, PDF, ZIP encryption
- Remove EFS encryption
- Office document password attempts
- PDF password attempts
- ZIP password recovery
- Common password dictionary

**Usage:**

```python
from tools.file_decryptor import FileDecryptor

with FileDecryptor() as decryptor:
    # Detect encryption
    detection = decryptor.detect_encryption(r'C:\encrypted.xlsx')
    print(f"Encrypted: {detection['encrypted']}")
    print(f"Types: {detection['encryption_types']}")

    # Decrypt Office file
    result = decryptor.decrypt_office_file(
        r'C:\encrypted.xlsx',
        password='mypassword',  # Known password
        try_common=True,        # Try common passwords
        output_path=r'C:\decrypted.xlsx'
    )

    # Decrypt PDF
    result = decryptor.decrypt_pdf(
        r'C:\encrypted.pdf',
        try_common=True
    )

    # Remove EFS encryption
    result = decryptor.remove_efs_encryption(
        r'C:\efs_file.txt',
        backup=True
    )
```

**Command Line:**
```bash
# Detect encryption
python -m tools.file_decryptor --detect "C:\file.xlsx"

# Decrypt with password
python -m tools.file_decryptor --password "secret" "C:\file.xlsx"

# Try common passwords
python -m tools.file_decryptor "C:\file.pdf"
```

### 4. CADFileHandler - CAD File Access

**Features:**
- Detect CAD file types (DWG, DXF, NWD, NWF, NWC, RVT)
- Clone locked CAD files
- Extract metadata without opening
- Force read access to locked files
- Parse file headers

**Usage:**

```python
from tools.cad_file_handler import CADFileHandler

with CADFileHandler() as handler:
    # Detect CAD type
    detection = handler.detect_cad_type(r'C:\model.nwd')
    print(f"Is CAD: {detection['is_cad']}")
    print(f"Type: {detection['type']}")

    # Clone locked file for reading
    result = handler.clone_for_readonly_access(
        r'C:\locked_model.nwd',
        output_path=r'C:\temp\clone.nwd'
    )

    # Extract metadata
    metadata = handler.extract_metadata(r'C:\drawing.dxf')
    print(metadata)

    # Read locked file
    result = handler.read_locked_file(
        r'C:\locked_model.dwg',
        output_path=r'C:\copy.dwg'
    )
```

**Command Line:**
```bash
# Detect CAD type
python -m tools.cad_file_handler --detect "C:\model.nwd"

# Extract metadata
python -m tools.cad_file_handler --metadata "C:\drawing.dxf"

# Clone locked file
python -m tools.cad_file_handler --clone --output "C:\copy.nwd" "C:\locked.nwd"
```

## Common Use Cases

### Unlock File Locked by Navisworks

```python
from tools.file_unlocker import FileUnlocker

unlocker = FileUnlocker()

# Find Navisworks processes locking the file
processes = unlocker.get_locking_processes(r'C:\project\model.nwd')

navisworks_processes = [p for p in processes if 'roamer' in p.process_name.lower()]

if navisworks_processes:
    # Close handles without killing Navisworks
    for p in navisworks_processes:
        unlocker.close_handle(p.pid, p.handle_value)
```

### Access Folder with Broken Permissions

```python
from tools.permission_fixer import PermissionFixer

fixer = PermissionFixer()

# Backup current permissions
fixer.backup_permissions(r'C:\broken_folder')

# Take ownership
fixer.take_ownership(r'C:\broken_folder', recursive=True)

# Grant full control
fixer.grant_full_control(r'C:\broken_folder', recursive=True)

# If needed, restore later
fixer.restore_permissions(r'C:\broken_folder')
```

### Decrypt Password-Protected Office File

```python
from tools.file_decryptor import FileDecryptor

with FileDecryptor() as decryptor:
    # Try to decrypt with common passwords
    result = decryptor.decrypt_office_file(
        r'C:\protected.xlsx',
        try_common=True,
        output_path=r'C:\decrypted.xlsx'
    )

    if result['success']:
        print(f"Decrypted with password: {result['password_found']}")
    else:
        print(f"Failed: {result['errors']}")
```

### Clone Locked AutoCAD Drawing

```python
from tools.cad_file_handler import CADFileHandler

with CADFileHandler() as handler:
    # Clone the locked DWG file
    result = handler.clone_for_readonly_access(
        r'C:\project\locked_drawing.dwg',
        output_path=r'C:\temp\copy.dwg'
    )

    if result['success']:
        print(f"Clone created: {result['clone_path']}")
        print(f"Method: {result['method']}")

        # Now you can read the clone
```

## Integration with Smart Search Pro

These tools can be integrated into Smart Search Pro's operations panel:

```python
# In operations panel or context menu:

from tools.file_unlocker import unlock_file
from tools.permission_fixer import take_ownership

# Add "Unlock File" operation
if unlock_file(file_path):
    print("File unlocked successfully")

# Add "Fix Permissions" operation
if take_ownership(folder_path, recursive=True):
    print("Ownership taken successfully")
```

## GUI Dialogs

### File Unlocker Dialog

```python
from ui.file_unlocker_dialog import FileUnlockerDialog

# Open dialog
dialog = FileUnlockerDialog()
if dialog.exec():
    # Dialog closed successfully
    pass
```

Features:
- File/folder browser
- Locking process scanner
- Batch unlock multiple files
- Progress log
- Safe mode option

### Permission Dialog

```python
from ui.permission_dialog import PermissionDialog

# Open dialog
dialog = PermissionDialog()
if dialog.exec():
    # Dialog closed successfully
    pass
```

Features:
- Current permissions viewer
- ACE table display
- One-click ownership
- Recursive operations
- Backup/restore

## Error Handling

All tools return detailed result dictionaries:

```python
result = {
    'success': True/False,
    'path': 'file_path',
    'errors': [],  # List of error messages
    # Tool-specific fields
}
```

Always check the `success` field and handle errors:

```python
result = unlocker.unlock_file(file_path)

if not result['success']:
    print(f"Failed to unlock: {file_path}")
    for error in result['errors']:
        print(f"  - {error}")
```

## Logging

All tools use Python's logging module:

```python
import logging

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Now run tools with detailed logging
unlocker = FileUnlocker()
result = unlocker.unlock_file(file_path)
```

## Security Best Practices

1. **Always run as Administrator** for full functionality
2. **Backup before modifying** permissions or decrypting files
3. **Verify authorization** before accessing others' files
4. **Test in safe environment** before production use
5. **Monitor system behavior** when forcefully unlocking files
6. **Document actions** for compliance and auditing
7. **Understand legal implications** in your jurisdiction

## Limitations

### FileUnlocker
- Requires admin for handle enumeration
- Cannot unlock kernel handles
- May destabilize applications if handles closed
- Some system files cannot be unlocked

### PermissionFixer
- Requires admin and special privileges
- Default permissions may not match exact Windows defaults
- Some system files are protected and cannot be modified
- NTFS file system required

### FileDecryptor
- Cannot break strong encryption
- Password recovery limited to weak passwords
- Some encryption types not supported
- Requires optional dependencies for full functionality

### CADFileHandler
- Binary CAD formats require specialized parsers
- Some file types may be corrupted during clone
- VSS snapshot not fully implemented
- Metadata extraction limited for binary formats

## Troubleshooting

### "Access Denied" errors
- Run as Administrator
- Check antivirus/security software
- Verify file is not system-protected

### Handle enumeration fails
- Must run as Administrator
- Some handles are kernel-mode only
- Security software may block

### Permission changes don't take effect
- Restart Explorer or application
- Check if file is in use
- Verify NTFS file system

### Decryption fails
- Install optional dependencies
- Password may be wrong
- Encryption may be too strong
- File may be corrupted

## Contributing

When extending these tools:
1. Maintain security warnings
2. Add comprehensive error handling
3. Document security implications
4. Test with various file types
5. Consider Windows version compatibility

## License

Part of Smart Search Pro. Use responsibly and legally.

## Version

1.0.0 - Initial release with full unlocking and decryption capabilities

# Secure Vault System - Quick Start Guide

## Installation (5 minutes)

### Step 1: Install Dependencies

```bash
pip install cryptography PyQt6 Pillow
```

### Step 2: Verify Installation

```bash
python test_vault_system.py
```

All tests should pass.

## Basic Usage

### Create Your First Vault

```python
from vault.secure_vault import SecureVault, VaultConfig

# 1. Configure vault
config = VaultConfig()
config.container_path = "C:/Users/YourName/.vault.dll"  # Hidden system file

# 2. Create vault instance
vault = SecureVault(config)

# 3. Set passwords
main_password = "MyStrongPassword123!@#"
decoy_password = "FakePassword456$%^"  # Optional

# 4. Create vault
vault.create_vault(main_password, decoy_password)

print("Vault created successfully!")
```

### Add Files to Vault

```python
# 1. Unlock vault
vault.unlock_vault("MyStrongPassword123!@#")

# 2. Add file
vault.add_file("C:/path/to/secret_document.pdf", "/secret_document.pdf")

# 3. Save changes
vault.save_vault()

# 4. Lock vault
vault.lock_vault()

print("File secured!")
```

### Extract Files from Vault

```python
# 1. Unlock vault
vault.unlock_vault("MyStrongPassword123!@#")

# 2. List files
files = vault.list_files()
for path, info in files.items():
    print(f"{path}: {info['size']} bytes")

# 3. Extract file
vault.extract_file("/secret_document.pdf", "C:/extracted/document.pdf")

# 4. Lock vault
vault.lock_vault()

print("File extracted!")
```

## UI Usage

### Launch Vault Panel

Press **Ctrl+Shift+V** anywhere in Smart Search Pro to access the vault.

### First Time Setup

1. Press **Ctrl+Shift+V** to open vault panel
2. Click "Unlock Vault"
3. Since no vault exists, you'll be prompted to create one
4. Enter main password (required)
5. Enter decoy password (optional, recommended)
6. Vault is created and ready

### Adding Files (Drag & Drop)

1. Unlock vault (**Ctrl+Shift+V** then click "Unlock")
2. Drag files from Windows Explorer into vault panel
3. Files are automatically encrypted and added
4. Lock vault when done

### Emergency Hide

Press **Ctrl+Shift+H** to instantly hide and lock vault (panic button).

## Advanced Features

### Hide Vault Inside Image

```python
from vault.steganography import SteganographyEngine

# 1. Read vault container
with open(".vault.dll", 'rb') as f:
    vault_data = f.read()

# 2. Hide in family photo
SteganographyEngine.hide_in_png(
    "family_photo.png",
    vault_data,
    "family_photo_backup.png"
)

# Now your vault is hidden inside a normal-looking image!
# Delete original .vault.dll file securely
```

### Recover Hidden Vault

```python
# Extract vault from image
vault_data = SteganographyEngine.extract_from_png("family_photo_backup.png")

# Save recovered vault
with open(".vault.dll", 'wb') as f:
    f.write(vault_data)

# Unlock normally
vault.unlock_vault("MyStrongPassword123!@#")
```

### Anti-Forensics Mode

```python
from vault.anti_forensics import AntiForensics

# Make vault invisible to casual inspection
vault_file = ".vault.dll"

# 1. Randomize timestamp (appears old)
AntiForensics.randomize_timestamps(vault_file)

# 2. Blend with system files
AntiForensics.blend_with_system_files(vault_file)

# 3. Create decoys around it
decoys = AntiForensics.generate_decoy_files(
    "C:/Windows/System32",
    count=10
)

# Now vault looks like old system file among many others
```

### Virtual Filesystem

```python
from vault.virtual_fs import VirtualFileSystem

# 1. Mount VFS
vfs = VirtualFileSystem()
vfs.mount(vault)

# 2. Create folder structure
vfs.mkdir("/documents/work", parents=True)
vfs.mkdir("/documents/personal", parents=True)
vfs.mkdir("/photos")

# 3. Add files
vfs.write_file("/documents/work/project.txt", b"Secret project")
vfs.write_file("/documents/personal/diary.txt", b"My thoughts")

# 4. Browse and search
all_files = vfs.list_dir("/")
work_docs = vfs.find("*.txt", "/documents/work")

# 5. Unmount when done
vfs.unmount()
```

## Common Workflows

### Daily Use

```python
# Morning: Start work session
vault.unlock_vault("password")

# Work with encrypted files
content = vault.read_file("/work/document.txt")
# Edit content...
vault.write_file("/work/document.txt", updated_content)

# Evening: End session
vault.save_vault()
vault.lock_vault()
```

### Travel Security

```python
# Before travel: Hide vault in innocent file
with open(".vault.dll", 'rb') as f:
    vault_data = f.read()

SteganographyEngine.hide_in_png(
    "vacation_photo.png",
    vault_data,
    "vacation_backup.png"
)

# Securely delete original
AntiForensics.secure_delete(".vault.dll", passes=7)

# Travel with "vacation_backup.png"
# At destination: Extract vault from image
```

### Emergency Situations

```python
# Option 1: Use decoy password
vault.unlock_vault("DecoyPassword456$%^")
# Shows fake/innocent files

# Option 2: Emergency wipe
vault.emergency_wipe("DESTROY_ALL_DATA")
# WARNING: Irreversible!
```

## Security Checklist

- [ ] Use strong passwords (16+ characters)
- [ ] Enable auto-lock (5 minute timeout recommended)
- [ ] Set up decoy vault with believable content
- [ ] Hide vault container in system directory
- [ ] Randomize file timestamps
- [ ] Generate decoy files around vault
- [ ] Use virtual keyboard for sensitive passwords
- [ ] Clear clipboard after use
- [ ] Test panic button regularly
- [ ] Keep backup of vault (encrypted, separate location)

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Ctrl+Shift+V** | Show/Hide vault panel |
| **Ctrl+Shift+H** | Panic button (emergency hide) |
| **Esc** | Hide vault panel |

## Troubleshooting

### "Failed to unlock vault"
- Check password (case-sensitive)
- Wait if locked out after failed attempts
- Verify vault file exists and not corrupted

### "Cannot add file"
- Ensure vault is unlocked
- Check file exists and readable
- Verify sufficient disk space

### "Steganography failed"
- Install Pillow: `pip install Pillow`
- Check carrier image large enough
- Use PNG or JPEG format

### "Auto-lock not working"
- Verify timeout configured
- Check vault is unlocked
- Ensure no errors in logs

## Best Practices

### DO:
- Use unique, strong passwords
- Lock vault after each use
- Keep backups (encrypted separately)
- Test recovery procedures
- Update regularly
- Use anti-forensics features

### DON'T:
- Store passwords in plain text
- Leave vault unlocked unattended
- Use same password elsewhere
- Share vault containers unencrypted
- Ignore security warnings
- Skip backups

## Performance Tips

1. **Large files**: Use streaming (automatic)
2. **Many files**: Use virtual filesystem
3. **Frequent access**: Keep unlocked during session
4. **SSD**: Better encryption performance
5. **RAM**: More RAM = faster operations

## Getting Help

1. Read full documentation: `VAULT_DOCUMENTATION.md`
2. Run test suite: `python test_vault_system.py`
3. Check code examples in documentation
4. Review security best practices

## Next Steps

1. Create your first vault
2. Add some test files
3. Practice unlocking/locking
4. Test decoy password
5. Try steganography
6. Set up anti-forensics
7. Configure auto-lock
8. Test panic button
9. Create backup
10. Read full documentation

## Example: Complete Setup

```python
#!/usr/bin/env python3
"""Complete vault setup example"""

from vault.secure_vault import SecureVault, VaultConfig
from vault.steganography import SteganographyEngine
from vault.anti_forensics import AntiForensics
from vault.virtual_fs import VirtualFileSystem

# 1. Create vault
config = VaultConfig()
config.container_path = "C:/Windows/System32/.msvcrt.dll"
config.auto_lock_timeout = 300

vault = SecureVault(config)
vault.create_vault("MyStrongPassword123", "DecoyPassword456")

# 2. Add files
vault.unlock_vault("MyStrongPassword123")

vfs = VirtualFileSystem()
vfs.mount(vault)

vfs.mkdir("/documents", parents=True)
vfs.write_file("/documents/secret.txt", b"Confidential data")

vfs.unmount()
vault.save_vault()
vault.lock_vault()

# 3. Anti-forensics
AntiForensics.randomize_timestamps(config.container_path)
AntiForensics.blend_with_system_files(config.container_path)
decoys = AntiForensics.generate_decoy_files("C:/Windows/System32", 5)

# 4. Hide in image (optional)
with open(config.container_path, 'rb') as f:
    vault_data = f.read()

SteganographyEngine.hide_in_png(
    "innocent_photo.png",
    vault_data,
    "photo_backup.png"
)

print("Vault setup complete!")
print("Vault hidden in: photo_backup.png")
print("Decoy files created:", len(decoys))
```

---

**You're now ready to use the Secure Vault System!**

For detailed information, see `VAULT_DOCUMENTATION.md`

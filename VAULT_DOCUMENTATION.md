# Secure Vault System - Complete Documentation

## Overview

Military-grade encrypted vault system with plausible deniability and anti-forensics capabilities for Smart Search Pro.

## Features

### Core Security
- **AES-256-GCM Encryption**: Authenticated encryption with 256-bit keys
- **PBKDF2 Key Derivation**: 600,000 iterations (OWASP 2024 standard)
- **Plausible Deniability**: Decoy vault with secondary password
- **Anti-Tampering**: Cryptographic authentication tags
- **Secure Memory**: Automatic key clearing from memory
- **Auto-Lock**: Configurable timeout with automatic vault locking
- **Failed Attempts Lockout**: Protection against brute force

### Steganography
- **PNG Embedding**: LSB steganography in images
- **JPEG Embedding**: DCT coefficient modification
- **Audio Embedding**: WAV file LSB embedding
- **Integrity Verification**: Checksum validation
- **Auto Detection**: Automatic carrier type detection

### Anti-Forensics
- **Secure Deletion**: DoD 5220.22-M standard (7-pass overwrite)
- **Timestamp Manipulation**: Randomize file timestamps
- **File Disguise**: Hidden/system attributes, disguised extensions
- **No Registry Traces**: No Windows registry entries
- **Memory Cleanup**: Secure memory wiping
- **Decoy Generation**: Create decoy files to hide vault
- **Environment Detection**: Detect debuggers, VMs, forensic tools

### Virtual Filesystem
- **Directory Structure**: Full directory tree inside vault
- **File Operations**: Create, read, write, delete, copy, move
- **Metadata Encryption**: All file metadata encrypted
- **Path Validation**: Protection against path traversal
- **Import/Export**: Bulk operations for folders
- **File Search**: Pattern-based file finding

## Installation

### Dependencies

```bash
pip install cryptography PyQt6 Pillow
```

### Files Structure

```
smart_search/
├── vault/
│   ├── __init__.py
│   ├── secure_vault.py       # Core encryption engine
│   ├── steganography.py       # Hide vault in files
│   ├── anti_forensics.py      # Anti-detection
│   └── virtual_fs.py          # Virtual filesystem
├── ui/
│   ├── vault_panel.py         # Main vault interface
│   └── vault_unlock_dialog.py # Secure unlock dialog
└── test_vault_system.py       # Comprehensive tests
```

## Quick Start

### Creating a Vault

```python
from vault.secure_vault import SecureVault, VaultConfig

# Configure vault
config = VaultConfig()
config.container_path = "C:/Users/YourName/.vault.dll"  # Disguised as DLL
config.auto_lock_timeout = 300  # 5 minutes
config.use_decoy = True

# Create vault
vault = SecureVault(config)

# Main password
main_password = "YourStrongPassword123!@#"

# Optional decoy password (shows fake data)
decoy_password = "DecoyPassword456$%^"

vault.create_vault(main_password, decoy_password)
```

### Unlocking Vault

```python
from vault.secure_vault import SecureVault, VaultConfig

config = VaultConfig()
config.container_path = "C:/Users/YourName/.vault.dll"

vault = SecureVault(config)

# Unlock with main password
is_main = vault.unlock_vault("YourStrongPassword123!@#")

if is_main:
    print("Main vault unlocked")
else:
    print("Decoy vault unlocked (duress password used)")
```

### Adding Files

```python
# Add single file
vault.add_file("C:/path/to/secret.pdf", "/documents/secret.pdf")

# Save changes
vault.save_vault()

# Lock vault when done
vault.lock_vault()
```

### Using Virtual Filesystem

```python
from vault.virtual_fs import VirtualFileSystem

# Mount VFS
vfs = VirtualFileSystem()
vfs.mount(vault)

# Create directories
vfs.mkdir("/documents/personal", parents=True)

# Write file
content = b"Secret data"
vfs.write_file("/documents/personal/notes.txt", content)

# Read file
data = vfs.read_file("/documents/personal/notes.txt")

# List directory
files = vfs.list_dir("/documents")
for file_info in files:
    print(f"{file_info.path} - {file_info.size} bytes")

# Import entire folder
vfs.import_tree("C:/MyDocuments", "/imported")

# Export vault contents
vfs.export_tree("C:/Export", "/")

# Unmount when done
vfs.unmount()
```

### Steganography - Hide Vault

```python
from vault.steganography import SteganographyEngine

# Read vault container
with open("vault.dll", 'rb') as f:
    vault_data = f.read()

# Hide in innocent-looking image
carrier_image = "family_photo.png"
output_image = "family_photo_backup.png"

SteganographyEngine.hide_in_png(carrier_image, vault_data, output_image)

# Later, extract vault
extracted_vault = SteganographyEngine.extract_from_png(output_image)

with open("recovered_vault.dll", 'wb') as f:
    f.write(extracted_vault)
```

### Anti-Forensics

```python
from vault.anti_forensics import AntiForensics

# Make vault file blend with system files
AntiForensics.blend_with_system_files("vault.dll")

# Randomize timestamp (looks old)
AntiForensics.randomize_timestamps("vault.dll")

# Create decoy files around vault
decoys = AntiForensics.generate_decoy_files("C:/Windows/System32", count=10)

# Secure delete when needed
AntiForensics.secure_delete("old_vault.dll", passes=7)

# Check environment security
env = AntiForensics.get_environment_info()
if env['debugger_attached']:
    print("WARNING: Debugger detected!")
if env['vm_detected']:
    print("WARNING: Running in VM!")
```

## UI Integration

### Using Vault Panel

The vault panel can be accessed via keyboard shortcut:

**Ctrl+Shift+V** - Show/Hide vault panel

**Ctrl+Shift+H** - Panic button (emergency hide)

### Programmatic Usage

```python
from ui.vault_panel import VaultPanel
from PyQt6.QtWidgets import QMainWindow

# Add to main window
main_window = QMainWindow()
vault_panel = VaultPanel()

# Connect signals
vault_panel.vault_unlocked.connect(lambda: print("Vault unlocked"))
vault_panel.vault_locked.connect(lambda: print("Vault locked"))
vault_panel.panic_triggered.connect(lambda: print("PANIC!"))

# Show vault
vault_panel.show()
```

### Unlock Dialog

```python
from ui.vault_unlock_dialog import VaultUnlockDialog

# Show unlock dialog
password, is_duress, accepted = VaultUnlockDialog.get_unlock_password(
    max_attempts=5,
    lockout_duration=300  # 5 minutes
)

if accepted:
    if is_duress:
        print("Duress password entered - load decoy vault")
    else:
        print("Normal password - load main vault")
```

## Advanced Features

### Password Change

```python
# Change vault password
old_password = "OldPassword123"
new_password = "NewPassword456"

vault.unlock_vault(old_password)
vault.change_password(old_password, new_password)
```

### Vault Statistics

```python
stats = vault.get_vault_stats()

print(f"Files: {stats['file_count']}")
print(f"Total size: {stats['total_size']} bytes")
print(f"Created: {stats['created']}")
print(f"Location: {stats['container_path']}")
```

### Emergency Wipe

**WARNING: This is irreversible!**

```python
# Emergency destruction of vault
vault.emergency_wipe("DESTROY_ALL_DATA")
```

### Auto-Lock

```python
# Configure auto-lock
config.auto_lock_timeout = 300  # 5 minutes of inactivity

# Check if auto-lock triggered
if vault.check_auto_lock():
    print("Vault auto-locked")
```

## Security Best Practices

### Password Security
1. Use strong passwords (16+ characters)
2. Mix uppercase, lowercase, numbers, symbols
3. Don't reuse passwords
4. Consider using a password manager

### Container Location
1. Hide in system directories with disguised names
2. Use system-like extensions (.dll, .dat, .tmp)
3. Randomize timestamps to blend with old files
4. Consider hiding inside images using steganography

### Operational Security
1. Always lock vault when not in use
2. Enable auto-lock with short timeout
3. Use virtual keyboard to prevent keyloggers
4. Clear clipboard after copying sensitive data
5. Use panic button when needed

### Anti-Forensics
1. Generate decoy files around vault
2. Randomize file timestamps regularly
3. Use secure deletion for old vaults
4. Monitor for debuggers/forensic tools
5. Consider running in isolated environment

### Plausible Deniability
1. Set up decoy vault with believable content
2. Remember both passwords
3. Practice using decoy password
4. Keep decoy data realistic

## Configuration Options

```python
class VaultConfig:
    container_path: str = ""                    # Vault file location
    auto_lock_timeout: int = 300                # Auto-lock after 5 min
    clipboard_clear_delay: int = 30             # Clear clipboard after 30s
    max_failed_attempts: int = 5                # Max unlock attempts
    lockout_duration: int = 300                 # Lockout for 5 min
    use_decoy: bool = True                      # Enable decoy vault
    secure_delete_passes: int = 7               # DoD standard
    disguise_extension: str = ".dll"            # File extension
```

## Performance Considerations

### Encryption Performance
- AES-256-GCM is hardware-accelerated on modern CPUs
- PBKDF2 with 600,000 iterations takes ~1-2 seconds
- Large files are encrypted in streaming fashion

### Memory Usage
- Vault metadata kept in memory while unlocked
- File contents loaded on-demand
- Automatic memory cleanup on lock

### Storage Overhead
- ~10% overhead for encryption and authentication
- Metadata stored efficiently
- Compression not included (encrypt before compress if needed)

## Troubleshooting

### Common Issues

**Vault won't unlock**
- Check password carefully
- Ensure vault file not corrupted
- Check for lockout after failed attempts

**Performance slow**
- KDF iterations intentionally slow (security)
- Consider SSD for better I/O performance
- Large files take time to encrypt/decrypt

**Steganography fails**
- Ensure Pillow installed: `pip install Pillow`
- Check carrier file size is sufficient
- Verify carrier file format supported

**Auto-lock not working**
- Check timeout configuration
- Ensure timer is running
- Verify vault unlocked state

## Testing

Run comprehensive test suite:

```bash
python test_vault_system.py
```

Tests include:
- Vault creation and unlocking
- Encryption security
- Steganography
- Anti-forensics
- Virtual filesystem
- Password changes
- Statistics

## Security Audit

### Threat Model
- **Local Attacker**: File system access, no admin privileges
- **Forensic Analysis**: Disk imaging, file recovery attempts
- **Keyloggers**: Keyboard input monitoring
- **Memory Dumps**: RAM analysis

### Protections
- **Encryption**: AES-256-GCM (military-grade)
- **Key Derivation**: PBKDF2 (resistant to brute force)
- **Authentication**: GCM mode provides integrity
- **Plausible Deniability**: Decoy vault feature
- **Anti-Forensics**: Secure deletion, timestamp manipulation
- **Anti-Keylogger**: Virtual keyboard option

### Known Limitations
1. **Python Memory**: Sensitive data may remain in Python interpreter memory
2. **Swap/Pagefile**: Encrypted data may be written to disk swap
3. **Cold Boot Attacks**: Keys in RAM vulnerable to physical attacks
4. **Rubber Hose Cryptanalysis**: No protection against coercion
5. **Malware**: Active malware can compromise vault when unlocked

### Recommended Mitigations
1. Disable swap/pagefile on secure systems
2. Use encrypted RAM if available
3. Run in isolated/air-gapped environment
4. Use full-disk encryption for host system
5. Regular security audits and updates

## Legal Notice

**IMPORTANT**: This vault system is designed for legitimate privacy and security purposes only.

- Do not use for illegal activities
- Comply with local encryption laws
- Do not export to restricted countries
- Respect data retention regulations
- Understand your local laws regarding encryption

## Support

For issues or questions:
1. Check this documentation
2. Run test suite for diagnostics
3. Review code comments
4. Consult security best practices

## Version History

**v1.0.0** (2024-12-12)
- Initial release
- AES-256-GCM encryption
- Steganography support
- Anti-forensics features
- Virtual filesystem
- PyQt6 UI integration
- Comprehensive test suite

## License

This software is provided as-is for educational and legitimate privacy purposes.
Use at your own risk. No warranty provided.

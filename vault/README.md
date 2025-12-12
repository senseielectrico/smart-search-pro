# Secure Vault System

Military-grade encrypted vault with plausible deniability and anti-forensics.

## Quick Start

```python
from vault import SecureVault, VaultConfig

# Create vault
config = VaultConfig()
vault = SecureVault(config)
vault.create_vault("YourPassword123", "DecoyPassword456")

# Add file
vault.unlock_vault("YourPassword123")
vault.add_file("secret.pdf", "/secret.pdf")
vault.save_vault()
vault.lock_vault()
```

## Features

- **AES-256-GCM Encryption** - Military-grade security
- **Plausible Deniability** - Decoy vault with separate password
- **Steganography** - Hide vault inside images/audio
- **Anti-Forensics** - Secure deletion, timestamp manipulation
- **Virtual Filesystem** - Full directory structure inside vault
- **Auto-Lock** - Automatic locking after timeout
- **UI Integration** - Ctrl+Shift+V to access

## Documentation

- **VAULT_QUICKSTART.md** - Get started in 5 minutes
- **VAULT_DOCUMENTATION.md** - Complete reference
- **VAULT_SECURITY_SUMMARY.md** - Security analysis
- **VAULT_IMPLEMENTATION_SUMMARY.md** - Technical details

## Modules

### secure_vault.py
Core encryption engine with AES-256-GCM and PBKDF2 key derivation.

```python
from vault.secure_vault import SecureVault, VaultConfig

vault = SecureVault(VaultConfig())
vault.create_vault("password", "decoy_password")
```

### steganography.py
Hide vault inside innocent-looking files (PNG, JPEG, WAV).

```python
from vault.steganography import SteganographyEngine

SteganographyEngine.hide_in_png("photo.png", vault_data, "output.png")
data = SteganographyEngine.extract_from_png("output.png")
```

### anti_forensics.py
Counter forensic detection and analysis.

```python
from vault.anti_forensics import AntiForensics

AntiForensics.secure_delete("old_file.dat", passes=7)
AntiForensics.randomize_timestamps("vault.dll")
AntiForensics.blend_with_system_files("vault.dll")
```

### virtual_fs.py
Virtual encrypted filesystem with full directory support.

```python
from vault.virtual_fs import VirtualFileSystem

vfs = VirtualFileSystem()
vfs.mount(vault)
vfs.mkdir("/documents")
vfs.write_file("/documents/note.txt", b"Secret")
vfs.unmount()
```

## Security

- **Encryption:** AES-256-GCM (NIST approved)
- **Key Derivation:** PBKDF2-SHA256 (600,000 iterations)
- **Authentication:** GCM tag verification
- **Random:** Cryptographically secure (secrets module)
- **Deletion:** DoD 5220.22-M (7-pass overwrite)

## UI Access

**Keyboard Shortcuts:**
- `Ctrl+Shift+V` - Show/Hide vault
- `Ctrl+Shift+H` - Panic button (emergency hide)
- `Esc` - Hide vault panel

## Testing

```bash
python test_vault_system.py
```

All tests should pass.

## Dependencies

```bash
pip install cryptography PyQt6 Pillow
```

## License

Educational and legitimate privacy use only.

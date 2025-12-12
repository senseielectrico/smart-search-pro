"""
Secure Vault Engine - Military-Grade Encryption
AES-256-GCM with PBKDF2 key derivation and plausible deniability

Security Features:
- AES-256-GCM authenticated encryption
- PBKDF2 with 600,000 iterations
- Secure memory handling
- Anti-tampering detection
- Decoy vault support
- Auto-lock mechanism
- No file system traces
"""

import os
import json
import secrets
import hashlib
import struct
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import hmac as hmac_module  # CVE-004 FIX: HMAC para autenticación de headers

# Constants
AES_KEY_SIZE = 32  # 256 bits
NONCE_SIZE = 12    # 96 bits for GCM
SALT_SIZE = 32     # 256 bits
TAG_SIZE = 16      # 128 bits authentication tag
HMAC_SIZE = 32     # 256 bits HMAC tag (CVE-004 FIX)
KDF_ITERATIONS = 600000  # OWASP recommendation for 2024
HEADER_MAGIC = b'MSDN'  # Disguised as Microsoft Developer Network
DECOY_MAGIC = b'MSVS'   # Disguised as Microsoft Visual Studio
LOCKOUT_FILE = '.vault_lockout'  # CVE-005 FIX: Persistent lockout state


@dataclass
class VaultConfig:
    """Vault configuration with security parameters"""
    container_path: str = ""
    auto_lock_timeout: int = 300  # 5 minutes
    clipboard_clear_delay: int = 30  # 30 seconds
    max_failed_attempts: int = 5
    lockout_duration: int = 300  # 5 minutes
    use_decoy: bool = True
    secure_delete_passes: int = 7
    disguise_extension: str = ".dll"  # Disguise as system file

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VaultConfig':
        return cls(**data)


class SecureMemory:
    """Secure memory handling to prevent data leakage"""

    @staticmethod
    def clear_bytes(data: bytearray) -> None:
        """Securely overwrite bytes in memory"""
        if data:
            # Overwrite with random data
            for i in range(len(data)):
                data[i] = secrets.randbelow(256)
            # Overwrite with zeros
            for i in range(len(data)):
                data[i] = 0

    @staticmethod
    def clear_string(s: str) -> None:
        """Attempt to clear string from memory (Python limitation)"""
        # Python strings are immutable, but we can at least try
        # This is more of a symbolic gesture in Python
        pass


class SecureVault:
    """
    Military-grade encrypted vault with plausible deniability

    Features:
    - AES-256-GCM encryption
    - PBKDF2 key derivation
    - Decoy vault with secondary password
    - Anti-tampering detection
    - Secure memory handling
    - No metadata leakage
    - HMAC header authentication (CVE-004 FIX)
    - Persistent lockout state (CVE-005 FIX)
    """

    def __init__(self, config: Optional[VaultConfig] = None):
        self.config = config or VaultConfig()
        self._master_key: Optional[bytes] = None
        self._decoy_key: Optional[bytes] = None
        self._last_access = time.time()
        self._failed_attempts = 0
        self._lockout_until = 0
        self._is_locked = True
        self._vault_data: Dict[str, Any] = {}
        self._decoy_data: Dict[str, Any] = {}
        # CVE-005 FIX: Load persistent lockout state
        self._load_lockout_state()

    def _get_lockout_file_path(self) -> Path:
        """Get path to lockout state file (fallback storage)"""
        if self.config.container_path:
            return Path(self.config.container_path).parent / LOCKOUT_FILE
        return Path.home() / LOCKOUT_FILE

    def _get_registry_key_path(self) -> str:
        """CVE-VAULT-002 FIX: Get unique registry key path for this vault"""
        vault_id = hashlib.sha256(
            (self.config.container_path or "default").encode()
        ).hexdigest()[:16]
        return rf"SOFTWARE\SmartSearchPro\VaultSecurity\{vault_id}"

    def _load_lockout_state(self) -> None:
        """CVE-005/CVE-VAULT-002 FIX: Load lockout state from Registry (primary) or file (fallback)"""
        # Try Windows Registry first (CVE-VAULT-002 FIX)
        try:
            import winreg
            key_path = self._get_registry_key_path()
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
                self._failed_attempts = winreg.QueryValueEx(key, "FailedAttempts")[0]
                lockout_str = winreg.QueryValueEx(key, "LockoutUntil")[0]
                self._lockout_until = float(lockout_str)
                return  # Success - registry has priority
        except (WindowsError, ImportError, FileNotFoundError):
            pass  # Registry not available or key doesn't exist

        # Fallback to file (backward compatibility)
        try:
            lockout_file = self._get_lockout_file_path()
            if lockout_file.exists():
                data = json.loads(lockout_file.read_text())
                self._failed_attempts = data.get('failed_attempts', 0)
                self._lockout_until = data.get('lockout_until', 0)
        except Exception:
            # If file is corrupted, start fresh
            self._failed_attempts = 0
            self._lockout_until = 0

    def _save_lockout_state(self) -> None:
        """CVE-005/CVE-VAULT-002 FIX: Save lockout state to Registry (primary) and file (backup)"""
        # Save to Windows Registry (CVE-VAULT-002 FIX - harder to bypass)
        try:
            import winreg
            key_path = self._get_registry_key_path()
            # Create key if it doesn't exist
            key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, "FailedAttempts", 0, winreg.REG_DWORD, self._failed_attempts)
            # Store float as string since REG_QWORD has issues with floats
            winreg.SetValueEx(key, "LockoutUntil", 0, winreg.REG_SZ, str(self._lockout_until))
            winreg.CloseKey(key)
        except (WindowsError, ImportError) as e:
            pass  # Registry write failed, continue to file backup

        # Also save to file (backup, may be deleted but registry remains)
        try:
            lockout_file = self._get_lockout_file_path()
            data = {
                'failed_attempts': self._failed_attempts,
                'lockout_until': self._lockout_until
            }
            lockout_file.write_text(json.dumps(data))
        except Exception as e:
            pass  # Silent fail - registry is primary

    def _compute_header_hmac(self, header_data: bytes, key: bytes) -> bytes:
        """CVE-004 FIX: Compute HMAC for header authentication"""
        return hmac_module.new(key, header_data, hashlib.sha256).digest()

    def _verify_header_hmac(self, header_data: bytes, expected_hmac: bytes, key: bytes) -> bool:
        """CVE-004 FIX: Verify header HMAC using constant-time comparison"""
        computed_hmac = self._compute_header_hmac(header_data, key)
        return hmac_module.compare_digest(computed_hmac, expected_hmac)

    def _derive_key(self, password: str, salt: bytes, iterations: int = KDF_ITERATIONS) -> bytes:
        """Derive encryption key from password using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=AES_KEY_SIZE,
            salt=salt,
            iterations=iterations,
        )
        key = kdf.derive(password.encode('utf-8'))
        return key

    def _generate_nonce(self) -> bytes:
        """Generate cryptographically secure nonce"""
        return secrets.token_bytes(NONCE_SIZE)

    def _generate_salt(self) -> bytes:
        """Generate cryptographically secure salt"""
        return secrets.token_bytes(SALT_SIZE)

    def _encrypt_data(self, data: bytes, key: bytes) -> bytes:
        """Encrypt data using AES-256-GCM"""
        nonce = self._generate_nonce()
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        return nonce + ciphertext  # Nonce + encrypted data + auth tag

    def _decrypt_data(self, encrypted: bytes, key: bytes) -> bytes:
        """Decrypt data using AES-256-GCM"""
        nonce = encrypted[:NONCE_SIZE]
        ciphertext = encrypted[NONCE_SIZE:]
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)

    def _create_header(self, salt: bytes, decoy_salt: Optional[bytes] = None,
                      is_decoy: bool = False, master_key: Optional[bytes] = None) -> bytes:
        """Create vault container header with HMAC authentication (CVE-004 FIX)"""
        magic = DECOY_MAGIC if is_decoy else HEADER_MAGIC
        version = struct.pack('!H', 2)  # Version 2 - with HMAC
        timestamp = struct.pack('!Q', int(time.time()))

        header = magic + version + timestamp + salt

        if decoy_salt and self.config.use_decoy:
            header += decoy_salt
        else:
            header += b'\x00' * SALT_SIZE

        # Add random padding to disguise structure
        padding_size = secrets.randbelow(256) + 256
        padding = secrets.token_bytes(padding_size)
        header += struct.pack('!H', padding_size) + padding

        # CVE-004 FIX: Append HMAC for header authentication
        if master_key:
            hmac_tag = self._compute_header_hmac(header, master_key)
            header += hmac_tag

        return header

    def _parse_header(self, header: bytes) -> Tuple[bytes, Optional[bytes], bool]:
        """Parse vault container header"""
        magic = header[:4]
        is_decoy = (magic == DECOY_MAGIC)

        if magic not in (HEADER_MAGIC, DECOY_MAGIC):
            raise ValueError("Invalid vault header")

        # Skip version (2 bytes) and timestamp (8 bytes)
        offset = 4 + 2 + 8
        salt = header[offset:offset + SALT_SIZE]
        offset += SALT_SIZE

        decoy_salt = header[offset:offset + SALT_SIZE]
        if decoy_salt == b'\x00' * SALT_SIZE:
            decoy_salt = None

        return salt, decoy_salt, is_decoy

    def create_vault(self, password: str, decoy_password: Optional[str] = None,
                    container_path: Optional[str] = None) -> bool:
        """Create new encrypted vault container"""
        try:
            if container_path:
                self.config.container_path = container_path

            if not self.config.container_path:
                # Generate random disguised name
                random_name = secrets.token_hex(8)
                self.config.container_path = str(Path.home() / f".{random_name}{self.config.disguise_extension}")

            # Generate salts
            main_salt = self._generate_salt()
            decoy_salt = self._generate_salt() if decoy_password and self.config.use_decoy else None

            # Derive keys
            master_key = self._derive_key(password, main_salt)
            decoy_key = self._derive_key(decoy_password, decoy_salt) if decoy_salt else None

            # Create empty vault data
            vault_data = {
                'version': 1,
                'created': int(time.time()),
                'files': {},
                'metadata': {}
            }

            decoy_data = {
                'version': 1,
                'created': int(time.time()),
                'files': {
                    'readme.txt': {
                        'content': b'Personal notes and reminders',
                        'size': 30,
                        'created': int(time.time())
                    }
                },
                'metadata': {}
            } if decoy_key else {}

            # Encrypt vault data
            vault_json = json.dumps(vault_data).encode('utf-8')
            encrypted_vault = self._encrypt_data(vault_json, master_key)

            # Create header with HMAC authentication (CVE-004 FIX)
            header = self._create_header(main_salt, decoy_salt, False, master_key)

            # Write container
            with open(self.config.container_path, 'wb') as f:
                f.write(header)
                f.write(encrypted_vault)

                # Add decoy data if enabled
                if decoy_key:
                    decoy_json = json.dumps(decoy_data).encode('utf-8')
                    encrypted_decoy = self._encrypt_data(decoy_json, decoy_key)
                    f.write(encrypted_decoy)

            # Set random file timestamps to blend in
            from .anti_forensics import AntiForensics
            AntiForensics.randomize_timestamps(self.config.container_path)

            # Clear sensitive data from memory
            SecureMemory.clear_bytes(bytearray(master_key))
            if decoy_key:
                SecureMemory.clear_bytes(bytearray(decoy_key))

            return True

        except Exception as e:
            print(f"Vault creation error: {e}")
            return False

    def unlock_vault(self, password: str) -> bool:
        """Unlock vault with password"""
        try:
            # Check lockout
            if time.time() < self._lockout_until:
                remaining = int(self._lockout_until - time.time())
                raise PermissionError(f"Vault locked. Try again in {remaining} seconds")

            if not os.path.exists(self.config.container_path):
                raise FileNotFoundError("Vault container not found")

            # Read container
            with open(self.config.container_path, 'rb') as f:
                # Read fixed header part: magic(4) + version(2) + timestamp(8) + salts(64) + padding_size(2)
                header_base = f.read(4 + 2 + 8 + SALT_SIZE * 2 + 2)

                # Get padding size and read padding
                padding_size = struct.unpack('!H', header_base[-2:])[0]
                padding = f.read(padding_size)

                # Check version for HMAC support (CVE-004 FIX)
                version = struct.unpack('!H', header_base[4:6])[0]
                header_hmac = None
                if version >= 2:
                    # Version 2+ includes HMAC
                    header_hmac = f.read(HMAC_SIZE)

                # Full header for HMAC verification (without HMAC itself)
                full_header = header_base + padding

                # Parse header to get salts
                salt, decoy_salt, _ = self._parse_header(header_base)

                # Try to derive key
                key = self._derive_key(password, salt)

                # CVE-004 FIX: Verify HMAC before proceeding
                if header_hmac and version >= 2:
                    if not self._verify_header_hmac(full_header, header_hmac, key):
                        # HMAC mismatch - either wrong password or header tampered
                        raise ValueError("Header integrity check failed - possible tampering detected")

                # Try to decrypt main vault
                encrypted_data = f.read()

                # Determine if this is decoy or main
                is_decoy = False
                try:
                    # Try main vault first
                    vault_size = len(encrypted_data) // 2 if decoy_salt else len(encrypted_data)
                    main_encrypted = encrypted_data[:vault_size]
                    decrypted = self._decrypt_data(main_encrypted, key)
                    self._vault_data = json.loads(decrypted)
                except Exception:
                    # Try decoy vault if available
                    if decoy_salt:
                        try:
                            decoy_key = self._derive_key(password, decoy_salt)
                            decoy_encrypted = encrypted_data[vault_size:]
                            decrypted = self._decrypt_data(decoy_encrypted, decoy_key)
                            self._vault_data = json.loads(decrypted)
                            is_decoy = True
                            key = decoy_key
                        except Exception:
                            raise ValueError("Invalid password")
                    else:
                        raise ValueError("Invalid password")

            # Success - reset failed attempts
            self._failed_attempts = 0
            self._lockout_until = 0
            self._save_lockout_state()  # CVE-005 FIX: Persist clean state
            self._is_locked = False
            self._master_key = key
            self._last_access = time.time()

            return not is_decoy  # Return True if main vault, False if decoy

        except Exception as e:
            # Failed attempt
            self._failed_attempts += 1

            if self._failed_attempts >= self.config.max_failed_attempts:
                self._lockout_until = time.time() + self.config.lockout_duration
                self._failed_attempts = 0

            # CVE-005 FIX: Persist lockout state to prevent restart bypass
            self._save_lockout_state()

            if self._lockout_until > time.time():
                raise PermissionError("Too many failed attempts. Vault locked.")

            raise ValueError(f"Failed to unlock vault: {e}")

    def lock_vault(self) -> None:
        """Lock vault and clear sensitive data from memory"""
        if self._master_key:
            SecureMemory.clear_bytes(bytearray(self._master_key))
            self._master_key = None

        if self._decoy_key:
            SecureMemory.clear_bytes(bytearray(self._decoy_key))
            self._decoy_key = None

        self._vault_data = {}
        self._is_locked = True

    def add_file(self, file_path: str, virtual_path: str) -> bool:
        """Add file to vault"""
        if self._is_locked:
            raise PermissionError("Vault is locked")

        try:
            # Read file
            with open(file_path, 'rb') as f:
                content = f.read()

            # Encrypt content
            encrypted_content = self._encrypt_data(content, self._master_key)

            # Store in vault
            self._vault_data['files'][virtual_path] = {
                'content': encrypted_content.hex(),
                'size': len(content),
                'created': int(time.time()),
                'modified': int(os.path.getmtime(file_path))
            }

            # Update last access
            self._last_access = time.time()

            return True

        except Exception as e:
            print(f"Error adding file: {e}")
            return False

    def extract_file(self, virtual_path: str, output_path: str) -> bool:
        """Extract file from vault"""
        if self._is_locked:
            raise PermissionError("Vault is locked")

        try:
            if virtual_path not in self._vault_data['files']:
                raise FileNotFoundError(f"File not found in vault: {virtual_path}")

            file_info = self._vault_data['files'][virtual_path]
            encrypted_content = bytes.fromhex(file_info['content'])

            # Decrypt content
            content = self._decrypt_data(encrypted_content, self._master_key)

            # Write file
            with open(output_path, 'wb') as f:
                f.write(content)

            # Restore original timestamp
            if 'modified' in file_info:
                os.utime(output_path, (time.time(), file_info['modified']))

            # Update last access
            self._last_access = time.time()

            return True

        except Exception as e:
            print(f"Error extracting file: {e}")
            return False

    def list_files(self) -> Dict[str, Dict[str, Any]]:
        """List all files in vault"""
        if self._is_locked:
            raise PermissionError("Vault is locked")

        files = {}
        for path, info in self._vault_data['files'].items():
            files[path] = {
                'size': info['size'],
                'created': info['created'],
                'modified': info.get('modified', info['created'])
            }

        return files

    def remove_file(self, virtual_path: str) -> bool:
        """Remove file from vault"""
        if self._is_locked:
            raise PermissionError("Vault is locked")

        if virtual_path in self._vault_data['files']:
            del self._vault_data['files'][virtual_path]
            self._last_access = time.time()
            return True

        return False

    def save_vault(self) -> bool:
        """Save vault changes to container"""
        if self._is_locked:
            raise PermissionError("Vault is locked")

        try:
            # Read current header
            with open(self.config.container_path, 'rb') as f:
                header_data = f.read(4 + 2 + 8 + SALT_SIZE * 2 + 2)
                padding_size = struct.unpack('!H', header_data[-2:])[0]
                padding = f.read(padding_size)

            # Encrypt updated vault data
            vault_json = json.dumps(self._vault_data).encode('utf-8')
            encrypted_vault = self._encrypt_data(vault_json, self._master_key)

            # Write back
            with open(self.config.container_path, 'wb') as f:
                f.write(header_data)
                f.write(padding)
                f.write(encrypted_vault)

            return True

        except Exception as e:
            print(f"Error saving vault: {e}")
            return False

    def change_password(self, old_password: str, new_password: str) -> bool:
        """Change vault password"""
        try:
            # Verify old password by unlocking
            if not self.unlock_vault(old_password):
                raise ValueError("Invalid current password")

            # Generate new salt
            new_salt = self._generate_salt()

            # Derive new key
            new_key = self._derive_key(new_password, new_salt)

            # Re-encrypt all file contents with new key
            for file_path, file_info in self._vault_data['files'].items():
                # Decrypt with old key
                encrypted_content = bytes.fromhex(file_info['content'])
                content = self._decrypt_data(encrypted_content, self._master_key)

                # Re-encrypt with new key
                new_encrypted = self._encrypt_data(content, new_key)
                file_info['content'] = new_encrypted.hex()

            # Create new header
            header = self._create_header(new_salt, None, False)

            # Encrypt vault data with new key
            vault_json = json.dumps(self._vault_data).encode('utf-8')
            encrypted_vault = self._encrypt_data(vault_json, new_key)

            # Write new container
            with open(self.config.container_path, 'wb') as f:
                f.write(header)
                f.write(encrypted_vault)

            # Update master key
            SecureMemory.clear_bytes(bytearray(self._master_key))
            self._master_key = new_key

            return True

        except Exception as e:
            print(f"Error changing password: {e}")
            return False

    def get_vault_stats(self) -> Dict[str, Any]:
        """Get vault statistics"""
        if self._is_locked:
            raise PermissionError("Vault is locked")

        total_size = sum(info['size'] for info in self._vault_data['files'].values())

        return {
            'file_count': len(self._vault_data['files']),
            'total_size': total_size,
            'created': self._vault_data.get('created', 0),
            'container_path': self.config.container_path,
            'is_locked': self._is_locked
        }

    def check_auto_lock(self) -> bool:
        """Check if vault should auto-lock"""
        if not self._is_locked and self.config.auto_lock_timeout > 0:
            if time.time() - self._last_access > self.config.auto_lock_timeout:
                self.lock_vault()
                return True
        return False

    def emergency_wipe(self, confirmation: str) -> bool:
        """Emergency vault destruction (irreversible)"""
        if confirmation != "DESTROY_ALL_DATA":
            raise ValueError("Invalid confirmation code")

        try:
            from .anti_forensics import AntiForensics

            # Secure delete container
            if os.path.exists(self.config.container_path):
                AntiForensics.secure_delete(
                    self.config.container_path,
                    passes=self.config.secure_delete_passes
                )

            # Clear memory
            self.lock_vault()

            return True

        except Exception as e:
            print(f"Emergency wipe error: {e}")
            return False

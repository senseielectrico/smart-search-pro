# REMEDIATION QUICK START GUIDE
## Smart Search Pro v3.0 Security Fixes

**Priority Level:** CRITICAL
**Time to Implement:** 2-3 weeks
**Difficulty:** MEDIUM

---

## QUICK FIX CHECKLIST

- [ ] CVE-001: SQL Injection (2-3 days)
- [ ] CVE-004: Add HMAC Verification (1-2 days)
- [ ] CVE-005: Persistent Lockout (1 day)
- [ ] CVE-002: Event Log Clearing (2-3 days)
- [ ] CVE-003: Timestamp Obfuscation (1 day)

---

## CVE-001: SQL INJECTION - QUICK FIX

### Problem Location
File: `backend.py`, lines 183-191

### Root Cause
```python
# DANGEROUS - escape_percent=False allows injection
sanitized = sanitize_sql_input(
    keyword_with_wildcards,
    escape_percent=False  # Allows % injection
)
```

### Quick Fix (5 minutes)
```python
# Option A: Always escape percent (safest for now)
sanitized = sanitize_sql_input(
    keyword_with_wildcards,
    escape_percent=True  # Always escape
)

# Option B: Validate wildcards separately
def safe_wildcard_handling(keyword):
    """Ensure wildcards are only * characters"""
    if '*' in keyword and '%' in keyword:
        raise ValueError("Invalid wildcard characters")

    # Replace * with % only if no other dangerous chars
    return keyword.replace('*', '%')
```

### Proper Fix (Requires refactoring)
```python
def build_sql_query_safe(self) -> tuple:
    """
    Builds SQL query with parameterized approach.

    Returns:
        Tuple of (query_string, parameters_list)
    """
    conditions = []
    parameters = []

    if self.search_filename:
        for keyword in self.keywords:
            # 1. Validate input
            validate_search_input(keyword)

            # 2. Convert wildcards
            keyword_pattern = keyword.replace('*', '%')

            # 3. Use parameter placeholder
            conditions.append("System.FileName LIKE ?")
            parameters.append(f'%{keyword_pattern}%')

    # Build query
    where = ' OR '.join(conditions)
    query = f"""
    SELECT TOP {self.max_results}
        System.ItemPathDisplay,
        System.FileName,
        System.Size,
        System.DateModified
    FROM SystemIndex
    WHERE {where}
    ORDER BY System.DateModified DESC
    """

    return query, parameters

# Then use parameterized execution:
# recordset.Open(query, connection, parameters)
```

### Testing
```python
# Test with attack payloads
test_cases = [
    "test.txt",  # Normal
    "*.py",      # Wildcard
    "test%' OR '1'='1",  # Injection attempt
    "admin'; DROP TABLE",  # Drop attempt
]

for test in test_cases:
    try:
        query, params = query_obj.build_sql_query_safe([test])
        # Should succeed for normal, fail for injections
    except ValueError as e:
        print(f"Blocked: {e}")
```

---

## CVE-004: MISSING HMAC - QUICK FIX

### Problem Location
File: `vault/secure_vault.py`, lines 137-175

### Root Cause
Header metadata is not authenticated - only encrypted data has GCM auth

### Quick Fix Implementation

```python
# In secure_vault.py, add HMAC imports
from cryptography.hazmat.primitives import hashes, hmac as hmac_module

# Modify _create_header to add HMAC
def _create_header_with_auth(self, salt: bytes, key: bytes,
                            decoy_salt: Optional[bytes] = None,
                            is_decoy: bool = False) -> bytes:
    """Create header with HMAC authentication"""

    # Build header data
    magic = DECOY_MAGIC if is_decoy else HEADER_MAGIC
    version = struct.pack('!H', 1)
    timestamp = struct.pack('!Q', int(time.time()))

    header_data = magic + version + timestamp + salt

    if decoy_salt and self.config.use_decoy:
        header_data += decoy_salt
    else:
        header_data += b'\x00' * SALT_SIZE

    # Add padding
    padding_size = secrets.randbelow(256) + 256
    padding = secrets.token_bytes(padding_size)
    header_data += struct.pack('!H', padding_size) + padding

    # Compute HMAC over header
    h = hmac_module.HMAC(key, hashes.SHA256())
    h.update(header_data)
    header_hmac = h.finalize()

    # Return header + HMAC
    return header_data + header_hmac

# Modify _parse_header to verify HMAC
def _parse_header_with_verification(self, header: bytes, key: bytes):
    """Parse header and verify HMAC"""

    # Split header and HMAC
    if len(header) < 32:
        raise ValueError("Header too short for HMAC")

    header_data = header[:-32]
    header_hmac = header[-32:]

    # Verify HMAC
    h = hmac_module.HMAC(key, hashes.SHA256())
    h.update(header_data)

    try:
        h.verify(header_hmac)
    except Exception:
        raise ValueError("Header HMAC verification failed - tampering detected")

    # Parse verified header
    magic = header_data[:4]
    is_decoy = (magic == DECOY_MAGIC)

    offset = 4 + 2 + 8  # skip version and timestamp
    salt = header_data[offset:offset + SALT_SIZE]

    return salt, is_decoy
```

### Update unlock_vault()
```python
def unlock_vault(self, password: str) -> bool:
    try:
        # ... existing code ...

        # Read and verify header with HMAC
        header_data = f.read(4 + 2 + 8 + SALT_SIZE * 2 + 2 + 256 + 32)  # Include HMAC

        # Derive key for header verification
        key = self._derive_key(password, salt)  # Use salt from first attempt

        # Verify HMAC
        salt, decoy_salt, is_decoy = self._parse_header_with_verification(
            header_data, key
        )

        # Continue with existing decryption logic
```

---

## CVE-005: PERSISTENT LOCKOUT - QUICK FIX

### Problem Location
File: `vault/secure_vault.py`, lines 251-319

### Root Cause
Lockout state is in-memory only - restarting app resets counter

### Quick Fix Implementation

```python
import os
import json
from pathlib import Path

class SecureVault:
    LOCKOUT_FILE = os.path.expanduser("~/.vault_lockout")

    def __init__(self, config: Optional[VaultConfig] = None):
        # ... existing init ...
        self._load_lockout_state()  # Add this line

    def _persist_lockout_state(self):
        """Save lockout state to encrypted file"""
        lockout_info = {
            'lockout_until': self._lockout_until,
            'failed_attempts': self._failed_attempts,
            'timestamp': time.time()
        }

        try:
            lockout_json = json.dumps(lockout_info)

            # Use a hardcoded derivation for lockout file
            lockout_salt = b'LOCKOUT_STATE_12345678901234567'  # Fixed salt for lockout
            lockout_key = self._derive_key("LOCKOUT", lockout_salt)

            # Encrypt lockout file
            encrypted = self._encrypt_data(lockout_json.encode(), lockout_key)

            # Save with restricted permissions
            with open(self.LOCKOUT_FILE, 'wb') as f:
                f.write(encrypted)

            # Set file permissions (Windows only)
            import stat
            os.chmod(self.LOCKOUT_FILE, stat.S_IRUSR | stat.S_IWUSR)
        except Exception as e:
            logger.error(f"Failed to persist lockout state: {e}")

    def _load_lockout_state(self):
        """Load lockout state from file"""
        if not os.path.exists(self.LOCKOUT_FILE):
            return

        try:
            with open(self.LOCKOUT_FILE, 'rb') as f:
                encrypted = f.read()

            lockout_salt = b'LOCKOUT_STATE_12345678901234567'
            lockout_key = self._derive_key("LOCKOUT", lockout_salt)

            # Decrypt
            lockout_json = self._decrypt_data(encrypted, lockout_key)
            lockout_info = json.loads(lockout_json)

            # Restore state
            self._lockout_until = lockout_info.get('lockout_until', 0)
            self._failed_attempts = lockout_info.get('failed_attempts', 0)

            logger.info("Lockout state loaded from disk")
        except Exception as e:
            # If we can't load lockout file, apply maximum penalty
            logger.warning(f"Invalid lockout file, applying 1-hour penalty: {e}")
            self._lockout_until = time.time() + 3600

    def unlock_vault(self, password: str) -> bool:
        try:
            # ... existing code ...

            # After failed attempt, persist lockout
            if self._failed_attempts >= self.config.max_failed_attempts:
                self._lockout_until = time.time() + self.config.lockout_duration
                self._persist_lockout_state()  # Add this line
                raise PermissionError("Too many failed attempts. Vault locked.")

            # After successful unlock, clear lockout
            self._failed_attempts = 0
            self._lockout_until = 0
            if os.path.exists(self.LOCKOUT_FILE):
                os.remove(self.LOCKOUT_FILE)  # Add this line

            return not is_decoy
```

---

## CVE-002: EVENT LOG CLEARING - QUICK FIX

### Problem Location
File: `vault/anti_forensics.py`, lines 112-145

### Root Cause
Only clears Recent Documents, not Windows Event Logs

### Quick Fix Implementation

```python
@staticmethod
def clear_forensic_traces() -> bool:
    """Clear critical forensic evidence"""
    if platform.system() != 'Windows':
        return True

    try:
        success = True

        # 1. Clear Recent Documents
        recent_path = os.path.join(
            os.environ.get('APPDATA', ''),
            'Microsoft\\Windows\\Recent'
        )

        if os.path.exists(recent_path):
            for file in os.listdir(recent_path):
                try:
                    os.remove(os.path.join(recent_path, file))
                except Exception as e:
                    logger.warning(f"Failed to clear recent file: {e}")
                    success = False

        # 2. Clear Event Logs (requires admin)
        try:
            import subprocess

            # Clear Security Event Log
            subprocess.run(
                ['powershell', '-Command',
                 'Clear-EventLog -LogName Security'],
                check=False,
                capture_output=True,
                timeout=10
            )

            # Clear Application Event Log
            subprocess.run(
                ['powershell', '-Command',
                 'Clear-EventLog -LogName Application'],
                check=False,
                capture_output=True,
                timeout=10
            )

            # Clear System Event Log (if possible)
            subprocess.run(
                ['powershell', '-Command',
                 'Clear-EventLog -LogName System'],
                check=False,
                capture_output=True,
                timeout=10
            )
        except Exception as e:
            logger.warning(f"Event log clearing failed (may require admin): {e}")
            # Don't fail completely - continue with other cleanup

        # 3. Clear Windows Search cache (if accessible)
        try:
            search_cache = os.path.join(
                os.environ.get('PROGRAMDATA', 'C:\\ProgramData'),
                'Microsoft\\Windows Search\\Data\\Applications\\Windows'
            )

            if os.path.exists(search_cache):
                for file in os.listdir(search_cache):
                    try:
                        AntiForensics.secure_delete(os.path.join(search_cache, file))
                    except Exception:
                        pass  # Ignore errors here
        except Exception:
            pass

        logger.info("Forensic trace clearing completed")
        return success

    except Exception as e:
        logger.error(f"Forensic trace clearing error: {e}")
        return False
```

### Usage
```python
# Call after vault operations
from vault.anti_forensics import AntiForensics

def secure_vault_operations():
    # ... perform vault operations ...

    # Clear traces when done
    if AntiForensics.clear_forensic_traces():
        logger.info("Forensic traces cleared successfully")
    else:
        logger.warning("Some forensic traces could not be cleared")
```

---

## CVE-003: TIMESTAMP OBFUSCATION - QUICK FIX

### Problem Location
File: `vault/secure_vault.py`, lines 137-156

### Root Cause
Unencrypted timestamp allows timing correlation attacks

### Quick Fix Implementation

```python
def _create_header_with_obfuscated_time(self, salt: bytes,
                                        decoy_salt: Optional[bytes] = None,
                                        is_decoy: bool = False) -> bytes:
    """Create header with obfuscated timestamp"""

    magic = DECOY_MAGIC if is_decoy else HEADER_MAGIC
    version = struct.pack('!H', 1)

    # Obfuscate timestamp
    current_time = int(time.time())

    # Round to hour-level precision (reduces correlation)
    quantized_time = (current_time // 3600) * 3600

    # Further obfuscate with random offset within the hour
    random_offset = secrets.randbelow(3600)
    obfuscated_time = quantized_time + random_offset

    timestamp = struct.pack('!Q', obfuscated_time)

    # Rest of header as before
    header = magic + version + timestamp + salt

    if decoy_salt and self.config.use_decoy:
        header += decoy_salt
    else:
        header += b'\x00' * SALT_SIZE

    # Add randomized padding
    padding_size = secrets.randbelow(256) + 256
    padding = secrets.token_bytes(padding_size)
    header += struct.pack('!H', padding_size) + padding

    return header
```

### Why This Works
- Original timestamp precision: 1 second
- Quantized precision: 1 hour (3600 seconds)
- Random offset: 0-3599 seconds within hour
- Result: Attacker can only correlate to hour-level, not exact access time

---

## TESTING CHECKLIST

```bash
# Run security tests
pytest test_security_fixes.py -v

# Test SQL injection prevention
python -c "from backend import SearchQuery; q = SearchQuery(keywords=[\"test%' OR '1'='1\"])"

# Test path traversal prevention
python -c "from file_manager import validate_path_safety; validate_path_safety(src, r'C:\Windows')"

# Test vault lockout persistence
python -c "from vault import SecureVault; v = SecureVault(); v.unlock_vault('wrong'); import os; os.path.exists(os.path.expanduser('~/.vault_lockout'))"

# Run POC demonstrations
python SECURITY_POC_DEMONSTRATIONS.py
```

---

## DEPLOYMENT CHECKLIST

- [ ] All fixes reviewed by second developer
- [ ] Security tests pass 100%
- [ ] Attack payloads tested
- [ ] Performance impact assessed
- [ ] Documentation updated
- [ ] Changelog entry created
- [ ] Version bumped (v3.0.1 security release)
- [ ] Release notes mention security fixes
- [ ] Users notified of security update

---

## REFERENCE DOCUMENTS

- `SECURITY_ASSESSMENT_FINAL.md` - Comprehensive audit report
- `SECURITY_AUDIT_SUMMARY.txt` - Quick reference summary
- `SECURITY_POC_DEMONSTRATIONS.py` - Executable POC demonstrations
- `test_security_fixes.py` - Test suite for vulnerabilities

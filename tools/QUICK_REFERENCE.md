# Smart Search Tools - Quick Reference Guide

## Installation Check

```python
# Verify all components are available
from tools import ExifToolWrapper, FileDecryptor, FileUnlocker, MetadataAnalyzer

print("All tools imported successfully!")
```

---

## 1. ExifToolWrapper - Metadata Analysis

### Basic Usage

```python
from tools.exiftool_wrapper import ExifToolWrapper

# Initialize
wrapper = ExifToolWrapper()

# Check version
print(f"ExifTool version: {wrapper.get_version()}")

# Extract metadata from a file
metadata = wrapper.extract_metadata("photo.jpg")
for key, value in metadata.items():
    print(f"{key}: {value}")
```

### Advanced Features

```python
# Get specific tag
camera_model = wrapper.get_tag("photo.jpg", "Model")
print(f"Camera: {camera_model}")

# Set tag
wrapper.set_tag("photo.jpg", "Artist", "John Doe")

# Set multiple tags
wrapper.set_tags("photo.jpg", {
    "Artist": "John Doe",
    "Copyright": "2024 John Doe",
    "Description": "My photo"
})

# Remove all metadata
wrapper.remove_all_metadata("photo.jpg")

# Copy metadata from one file to another
wrapper.copy_metadata("source.jpg", "target.jpg")

# Extract thumbnail
wrapper.extract_thumbnail("photo.jpg", "thumb.jpg")

# Batch extraction (more efficient)
files = ["photo1.jpg", "photo2.jpg", "photo3.jpg"]
metadata_dict = wrapper.extract_metadata_batch(files)
```

---

## 2. FileDecryptor - File Decryption

### Basic Usage

```python
from tools.file_decryptor import FileDecryptor

# Initialize with context manager
with FileDecryptor() as decryptor:
    # Detect encryption
    result = decryptor.detect_encryption("document.docx")
    if result['encrypted']:
        print(f"Encryption types: {result['encryption_types']}")
```

### Decrypt Files

```python
with FileDecryptor() as decryptor:
    # Decrypt Office document
    result = decryptor.decrypt_office_file(
        "protected.docx",
        password="mypassword",  # Optional
        try_common=True,  # Try common passwords
        output_path="decrypted.docx"
    )
    if result['success']:
        print(f"Password found: {result['password_found']}")
        print(f"Saved to: {result['output_path']}")

    # Decrypt PDF
    result = decryptor.decrypt_pdf(
        "protected.pdf",
        password="secret",
        output_path="unlocked.pdf"
    )

    # Decrypt ZIP
    result = decryptor.decrypt_zip(
        "protected.zip",
        password="zippass",
        output_dir="extracted/"
    )

    # Remove EFS encryption
    result = decryptor.remove_efs_encryption("encrypted.txt")
```

### Batch Decryption

```python
with FileDecryptor() as decryptor:
    files = ["file1.docx", "file2.pdf", "file3.zip"]
    results = decryptor.batch_decrypt(files, try_common=True)

    for result in results:
        print(f"{result['path']}: {'SUCCESS' if result['success'] else 'FAILED'}")
```

### Convenience Functions

```python
from tools.file_decryptor import detect_encryption, decrypt_file

# Quick encryption check
is_encrypted = detect_encryption("document.docx")

# Quick decrypt
success = decrypt_file("document.docx", password="test123")
```

---

## 3. FileUnlocker - Locked File Handling

### Basic Usage

```python
from tools.file_unlocker import FileUnlocker

# Initialize
unlocker = FileUnlocker()

# Check if running as admin
if not unlocker.is_admin():
    print("WARNING: Not running as admin - some features limited")

# Remove file attributes
unlocker.remove_file_attributes("readonly_file.txt")
```

### Find Locking Processes

```python
# Find what's locking a file (requires admin)
locking_processes = unlocker.get_locking_processes("locked_file.txt")

for process in locking_processes:
    print(f"PID: {process.pid}")
    print(f"Name: {process.process_name}")
    print(f"Handle: {process.handle_value}")
```

### Unlock Files

```python
# Comprehensive unlock
result = unlocker.unlock_file(
    "locked_file.txt",
    kill_process=False,  # Don't kill processes
    safe_mode=False  # Force unlock instead of copying
)

print(f"Success: {result['success']}")
print(f"Handles closed: {result['handles_closed']}")
print(f"Processes killed: {result['processes_killed']}")
print(f"Locking processes: {result['locking_processes']}")

# Unlock with process termination
result = unlocker.unlock_file("locked_file.txt", kill_process=True)

# Batch unlock
files = ["file1.txt", "file2.txt"]
results = unlocker.batch_unlock(files)
```

### Advanced Operations

```python
# Close specific handle
unlocker.close_handle(pid=1234, handle_value=0x1A0)

# Kill locking process
unlocker.kill_locking_process(pid=1234, force=False)
```

### Convenience Functions

```python
from tools.file_unlocker import unlock_file, find_locking_processes

# Quick unlock
success = unlock_file("locked.txt", kill_process=False)

# Quick process lookup
processes = find_locking_processes("locked.txt")
for p in processes:
    print(f"{p['name']} (PID: {p['pid']})")
```

---

## 4. MetadataAnalyzer - Forensic Analysis

### Basic Usage

```python
from tools.metadata_analyzer import MetadataAnalyzer

# Initialize
analyzer = MetadataAnalyzer()

# Analyze a file
analysis = analyzer.analyze_file("photo.jpg")

print(f"File: {analysis['file_path']}")
print(f"Size: {analysis['file_size']} bytes")
```

### Detailed Analysis

```python
# Camera information
camera = analysis['camera_info']
if camera:
    print(f"Camera: {camera.get('make')} {camera.get('model')}")
    print(f"Lens: {camera.get('lens')}")
    print(f"ISO: {camera.get('iso')}")

# GPS information
gps = analysis['gps_info']
if gps:
    print(f"Coordinates: {gps.get('coordinates')}")
    print(f"Google Maps: {gps.get('map_link')}")
    print(f"OpenStreetMap: {gps.get('osm_link')}")

# Date/Time information
dates = analysis['datetime_info']
for key, value in dates.items():
    print(f"{key}: {value}")

# Software information
software = analysis['software_info']
if software.get('editors_detected'):
    print(f"Edited with: {', '.join(software['editors_detected'])}")

# Author information
author = analysis['author_info']
if author:
    print(f"Author: {author.get('author', 'Unknown')}")

# Hidden metadata
hidden = analysis['hidden_metadata']
if hidden.get('email'):
    print(f"Emails found: {hidden['email']}")
if hidden.get('url'):
    print(f"URLs found: {hidden['url']}")

# Anomalies
anomalies = analysis['anomalies']
if anomalies:
    print("Potential issues detected:")
    for anomaly in anomalies:
        print(f"  - {anomaly}")

# Device fingerprint
print(f"Device: {analysis['device_fingerprint']}")
```

### Compare Files

```python
# Compare metadata between two files
comparison = analyzer.compare_metadata("photo1.jpg", "photo2.jpg")

print(f"Similarity: {comparison['similarity_score']:.2%}")
print(f"Common fields: {len(comparison['similarities'])}")
print(f"Differences: {len(comparison['differences'])}")

# Show differences
for key, values in comparison['differences'].items():
    print(f"{key}:")
    print(f"  File 1: {values['file1']}")
    print(f"  File 2: {values['file2']}")
```

### Create Timeline

```python
# Create timeline from multiple files
files = ["photo1.jpg", "photo2.jpg", "photo3.jpg"]
timeline = analyzer.create_timeline(files)

for event in timeline:
    print(f"{event['timestamp']}: {event['file']} - {event['event']}")
```

### Detect Duplicates

```python
# Find duplicates based on metadata similarity
files = ["img1.jpg", "img2.jpg", "img3.jpg", "img4.jpg"]
duplicates = analyzer.detect_duplicates_by_metadata(
    files,
    tolerance=0.9  # 90% similarity threshold
)

for group in duplicates:
    print(f"Duplicate group: {group}")
```

---

## Common Workflows

### Workflow 1: Analyze Suspicious File

```python
from tools import ExifToolWrapper, MetadataAnalyzer, FileDecryptor

# Check if encrypted
with FileDecryptor() as dec:
    encryption = dec.detect_encryption("suspicious.jpg")
    if encryption['encrypted']:
        print(f"File is encrypted: {encryption['encryption_types']}")

# Analyze metadata
analyzer = MetadataAnalyzer()
analysis = analyzer.analyze_file("suspicious.jpg")

# Check for anomalies
if analysis['anomalies']:
    print("WARNING: Anomalies detected!")
    for anomaly in analysis['anomalies']:
        print(f"  - {anomaly}")

# Check for hidden data
hidden = analysis['hidden_metadata']
if hidden:
    print("Hidden metadata found:")
    for key, value in hidden.items():
        print(f"  {key}: {value}")
```

### Workflow 2: Unlock and Process File

```python
from tools import FileUnlocker, ExifToolWrapper

# Unlock file
unlocker = FileUnlocker()
result = unlocker.unlock_file("locked.jpg")

if result['success']:
    # Now process the file
    wrapper = ExifToolWrapper()
    wrapper.set_tag("locked.jpg", "Copyright", "My Company")
    print("File processed successfully")
else:
    print(f"Failed to unlock: {result['errors']}")
```

### Workflow 3: Batch Forensic Analysis

```python
from tools import MetadataAnalyzer
import os

# Get all images in directory
image_files = [
    f for f in os.listdir("photos/")
    if f.lower().endswith(('.jpg', '.jpeg', '.png'))
]

analyzer = MetadataAnalyzer()
results = []

for filename in image_files:
    filepath = os.path.join("photos/", filename)
    analysis = analyzer.analyze_file(filepath)
    results.append({
        'file': filename,
        'camera': analysis['camera_info'].get('model', 'Unknown'),
        'date': analysis['datetime_info'].get('creation', 'Unknown'),
        'gps': 'coordinates' in analysis['gps_info'],
        'edited': len(analysis['software_info'].get('editors_detected', [])) > 0,
        'anomalies': len(analysis['anomalies'])
    })

# Generate report
for r in results:
    print(f"{r['file']}:")
    print(f"  Camera: {r['camera']}")
    print(f"  Date: {r['date']}")
    print(f"  Has GPS: {r['gps']}")
    print(f"  Edited: {r['edited']}")
    print(f"  Anomalies: {r['anomalies']}")
    print()
```

### Workflow 4: Clean Metadata for Privacy

```python
from tools import ExifToolWrapper, MetadataAnalyzer

# Analyze what metadata exists
analyzer = MetadataAnalyzer()
analysis = analyzer.analyze_file("photo.jpg")

# Check for sensitive data
sensitive_found = False
hidden = analysis['hidden_metadata']

if hidden.get('email'):
    print(f"WARNING: Email addresses found: {hidden['email']}")
    sensitive_found = True

if hidden.get('ip_address'):
    print(f"WARNING: IP addresses found: {hidden['ip_address']}")
    sensitive_found = True

if analysis['gps_info']:
    print("WARNING: GPS coordinates found")
    sensitive_found = True

# Remove all metadata if sensitive data found
if sensitive_found:
    wrapper = ExifToolWrapper()
    wrapper.remove_all_metadata("photo.jpg")
    print("All metadata removed for privacy")
```

---

## Error Handling Best Practices

```python
from tools import FileUnlocker
import logging

logging.basicConfig(level=logging.INFO)

try:
    unlocker = FileUnlocker()

    if not unlocker.is_admin():
        raise PermissionError("Administrator privileges required")

    result = unlocker.unlock_file("important_file.txt")

    if not result['success']:
        print(f"Unlock failed: {', '.join(result['errors'])}")

        # Log details
        logging.error(f"Failed to unlock {result['file']}")
        logging.error(f"Locking processes: {result['locking_processes']}")
    else:
        logging.info("File successfully unlocked")

except PermissionError as e:
    print(f"Permission error: {e}")
except FileNotFoundError as e:
    print(f"File not found: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
    logging.exception("Unexpected error during unlock operation")
```

---

## Performance Tips

1. **Use batch operations when possible:**
   ```python
   # Instead of:
   for file in files:
       metadata = wrapper.extract_metadata(file)

   # Use:
   all_metadata = wrapper.extract_metadata_batch(files)
   ```

2. **Reuse objects:**
   ```python
   # Create once
   analyzer = MetadataAnalyzer()

   # Reuse for multiple files
   for file in files:
       analysis = analyzer.analyze_file(file)
   ```

3. **Use context managers for cleanup:**
   ```python
   with FileDecryptor() as decryptor:
       # Temp files automatically cleaned up
       result = decryptor.decrypt_office_file("file.docx")
   ```

4. **Cache results when appropriate:**
   ```python
   # ExifToolWrapper has built-in caching
   wrapper = ExifToolWrapper()
   metadata = wrapper.extract_metadata("file.jpg")  # Cached
   metadata = wrapper.extract_metadata("file.jpg")  # From cache

   # Clear cache if needed
   wrapper.clear_cache()
   ```

---

## Security Warnings

⚠️ **Always backup files before modification**
⚠️ **Only use on files you own or have authorization for**
⚠️ **Some operations require administrator privileges**
⚠️ **Force-closing handles can cause data loss**
⚠️ **Encryption bypass may violate laws in some jurisdictions**
⚠️ **Forensic analysis may expose sensitive personal data**

---

## Additional Resources

- **Full API Documentation:** See individual module docstrings
- **Verification Report:** `VERIFICATION_REPORT.md`
- **Module README:** `README.md`
- **Source Code:** `C:/Users/ramos/.local/bin/smart_search/tools/`

---

**Last Updated:** 2025-12-12

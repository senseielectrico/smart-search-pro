# File Operations Module

TeraCopy-style high-performance file operations for Smart Search Pro.

## Features

### Core Components

1. **OperationsManager** - Central queue system with pause/resume/cancel
2. **FileCopier** - Multi-threaded copying with adaptive buffering
3. **FileMover** - Intelligent move (rename for same-volume, copy+delete for cross-volume)
4. **FileVerifier** - Hash verification (CRC32, MD5, SHA-256, xxHash)
5. **ConflictResolver** - Advanced conflict handling
6. **ProgressTracker** - Detailed progress tracking with speed graphs

### Key Features

- **Adaptive Buffer Sizing**: 4KB to 256MB based on file size and device type
- **Multi-threaded Operations**: Parallel copying with ThreadPoolExecutor
- **Progress Tracking**: Per-file and overall progress with ETA
- **Error Recovery**: Automatic retry with exponential backoff
- **Queue Management**: Priority-based operation queue
- **Conflict Resolution**: Multiple strategies (skip, overwrite, rename, ask)
- **Verification**: Multiple hash algorithms with parallel verification
- **Operation History**: Audit trail with JSON persistence

## Installation

```python
# The module is part of Smart Search Pro
from operations import (
    OperationsManager,
    FileCopier,
    FileMover,
    FileVerifier,
    ConflictResolver,
    ProgressTracker
)
```

## Quick Start

### Basic Copy Operation

```python
from operations.copier import FileCopier

# Simple copy
with FileCopier() as copier:
    success, error = copier.copy_file_with_retry(
        source="C:/source/file.txt",
        destination="D:/backup/file.txt"
    )
    if success:
        print("Copy successful!")
    else:
        print(f"Copy failed: {error}")
```

### Copy with Progress Tracking

```python
from operations.copier import FileCopier

def on_progress(bytes_copied, total_bytes):
    percent = (bytes_copied / total_bytes) * 100
    print(f"Progress: {percent:.1f}%")

with FileCopier() as copier:
    copier.copy_file_with_retry(
        source="large_file.bin",
        destination="backup.bin",
        progress_callback=on_progress
    )
```

### Batch Copy Operations

```python
from operations.copier import FileCopier

file_pairs = [
    ("C:/data/file1.txt", "D:/backup/file1.txt"),
    ("C:/data/file2.txt", "D:/backup/file2.txt"),
    ("C:/data/file3.txt", "D:/backup/file3.txt"),
]

with FileCopier(max_workers=4) as copier:
    results = copier.copy_files_batch(file_pairs)

    for dest, (success, error) in results.items():
        if success:
            print(f"✓ {dest}")
        else:
            print(f"✗ {dest}: {error}")
```

### File Move Operations

```python
from operations.mover import FileMover

# Move single file
with FileMover() as mover:
    success, error = mover.move_file(
        source="C:/temp/file.txt",
        destination="D:/archive/file.txt"
    )
```

### File Verification

```python
from operations.verifier import FileVerifier, HashAlgorithm

# Verify copy
verifier = FileVerifier(algorithm=HashAlgorithm.MD5)
is_valid, error = verifier.verify_copy(
    source="original.bin",
    dest="copy.bin"
)

if is_valid:
    print("Verification successful - files match!")
else:
    print(f"Verification failed: {error}")
```

### Hash Calculation

```python
from operations.verifier import FileVerifier, HashAlgorithm

# Calculate MD5
verifier = FileVerifier(algorithm=HashAlgorithm.MD5)
hash_value = verifier.calculate_hash("file.bin")
print(f"MD5: {hash_value}")

# Calculate SHA-256
verifier = FileVerifier(algorithm=HashAlgorithm.SHA256)
hash_value = verifier.calculate_hash("file.bin")
print(f"SHA-256: {hash_value}")
```

### Batch Verification

```python
from operations.verifier import FileVerifier

file_pairs = [
    ("source1.txt", "dest1.txt"),
    ("source2.txt", "dest2.txt"),
]

verifier = FileVerifier()
results = verifier.verify_batch(file_pairs, max_workers=4)

for dest, (is_valid, error) in results.items():
    print(f"{dest}: {'✓' if is_valid else '✗'}")
```

### Conflict Resolution

```python
from operations.conflicts import ConflictResolver, ConflictAction

# Auto-rename on conflict
resolver = ConflictResolver(
    default_action=ConflictAction.RENAME,
    rename_pattern="{stem} ({counter}){suffix}"
)

resolution = resolver.resolve(
    source_path="file.txt",
    dest_path="existing_file.txt"
)

if resolution.action == ConflictAction.RENAME:
    print(f"Rename to: {resolution.new_path}")
```

### Operations Manager

```python
from operations.manager import OperationsManager, OperationPriority

# Create manager
manager = OperationsManager(
    max_concurrent_operations=2,
    history_file="operations_history.json"
)

# Queue copy operation
op_id = manager.queue_copy(
    source_paths=["file1.txt", "file2.txt", "file3.txt"],
    dest_paths=["backup/file1.txt", "backup/file2.txt", "backup/file3.txt"],
    priority=OperationPriority.HIGH,
    verify=True
)

# Monitor progress
progress = manager.get_progress(op_id)
if progress:
    print(f"Progress: {progress.progress_percent:.1f}%")
    print(f"Speed: {manager._progress_tracker.format_speed(progress.current_speed)}")
    print(f"ETA: {manager._progress_tracker.format_time(progress.eta_seconds)}")

# Pause/resume
manager.pause_operation(op_id)
manager.resume_operation(op_id)

# Cancel
manager.cancel_operation(op_id)

# Cleanup
manager.shutdown()
```

### Advanced Progress Tracking

```python
from operations.progress import ProgressTracker

tracker = ProgressTracker()

# Start tracking
files = ["file1.bin", "file2.bin", "file3.bin"]
sizes = [1024*1024, 2048*1024, 4096*1024]  # 1MB, 2MB, 4MB
progress = tracker.start_operation("op-001", files, sizes)

# Update progress
tracker.update_file("op-001", "file1.bin", 512*1024)  # 512KB copied
tracker.update_file("op-001", "file2.bin", 1024*1024)  # 1MB copied

# Get current status
current = tracker.get_progress("op-001")
print(f"Overall: {current.progress_percent:.1f}%")
print(f"Speed: {tracker.format_speed(current.current_speed)}")
print(f"ETA: {tracker.format_time(current.eta_seconds)}")
print(f"Completed: {current.completed_files}/{current.total_files}")

# Complete files
tracker.complete_file("op-001", "file1.bin")
tracker.complete_file("op-001", "file2.bin", error="Verification failed")
```

## Performance Optimization

### Buffer Size Selection

The module automatically selects optimal buffer sizes:

- **< 1MB**: 4KB buffer
- **< 100MB**: 1MB buffer
- **< 1GB**: 8MB buffer
- **≥ 1GB**: 64MB buffer

Same-volume operations use 2x larger buffers (up to 256MB).

### Multi-threading

```python
# Optimal worker count
from operations.copier import FileCopier

# For SSD-to-SSD: 4-8 workers
copier = FileCopier(max_workers=4)

# For HDD-to-HDD: 2-4 workers
copier = FileCopier(max_workers=2)

# For network: 8-16 workers
copier = FileCopier(max_workers=8)
```

### Verification Strategy

```python
from operations.copier import FileCopier
from operations.verifier import FileVerifier, HashAlgorithm

# Fast CRC32 for quick checks
verifier = FileVerifier(algorithm=HashAlgorithm.CRC32)

# MD5 for balance of speed and security
verifier = FileVerifier(algorithm=HashAlgorithm.MD5)

# SHA-256 for maximum security
verifier = FileVerifier(algorithm=HashAlgorithm.SHA256)

# xxHash for maximum speed (requires: pip install xxhash)
verifier = FileVerifier(algorithm=HashAlgorithm.XXHASH64)
```

## Error Handling

### Retry Logic

```python
from operations.copier import FileCopier

copier = FileCopier(
    retry_attempts=3,      # Retry up to 3 times
    retry_delay=1.0        # Start with 1s delay (exponential backoff)
)

# Automatic retry on failure
success, error = copier.copy_file_with_retry(source, dest)
```

### Conflict Handling

```python
from operations.conflicts import ConflictResolver, ConflictAction

# Custom conflict callback
def handle_conflict(source, dest):
    print(f"Conflict: {dest} already exists")
    user_choice = input("(S)kip, (O)verwrite, (R)ename? ").upper()

    if user_choice == 'S':
        return ConflictResolution(action=ConflictAction.SKIP)
    elif user_choice == 'O':
        return ConflictResolution(action=ConflictAction.OVERWRITE)
    else:
        return ConflictResolution(action=ConflictAction.RENAME)

resolver = ConflictResolver(default_action=ConflictAction.ASK)
resolver.set_callback(handle_conflict)
```

## Testing

Run the test suite:

```bash
cd C:\Users\ramos\.local\bin\smart_search\operations
python test_operations.py
```

## Performance Benchmarks

Typical performance on modern hardware:

| Operation | Speed | Notes |
|-----------|-------|-------|
| SSD to SSD (same drive) | 3-5 GB/s | Limited by OS overhead |
| SSD to SSD (different) | 500 MB/s - 1 GB/s | Limited by PCIe lanes |
| HDD to HDD | 100-150 MB/s | Sequential reads/writes |
| Network (1 Gbps) | 100-120 MB/s | TCP overhead |
| Network (10 Gbps) | 500-800 MB/s | CPU becomes bottleneck |

## API Reference

### FileCopier

```python
FileCopier(
    max_workers: int = 4,
    verify_after_copy: bool = False,
    retry_attempts: int = 3,
    retry_delay: float = 1.0
)
```

Methods:
- `copy_file(source, destination, progress_callback, preserve_metadata)`
- `copy_file_with_retry(source, destination, progress_callback, preserve_metadata)`
- `copy_files_batch(file_pairs, progress_callback, preserve_metadata)`
- `copy_directory(source_dir, dest_dir, progress_callback, preserve_metadata)`
- `pause()`, `resume()`, `cancel()`

### FileMover

```python
FileMover(
    verify_after_move: bool = False,
    delete_after_verify: bool = True,
    preserve_metadata: bool = True
)
```

Methods:
- `move_file(source, destination, progress_callback)`
- `move_files_batch(file_pairs, progress_callback)`
- `move_directory(source_dir, dest_dir, progress_callback)`

### FileVerifier

```python
FileVerifier(
    algorithm: HashAlgorithm = HashAlgorithm.MD5,
    buffer_size: int = 64 * 1024 * 1024
)
```

Methods:
- `calculate_hash(file_path)`
- `verify_copy(source_path, dest_path)`
- `verify_batch(file_pairs, max_workers)`
- `generate_checksum_file(file_paths, output_path, format)`
- `verify_checksum_file(checksum_file, base_dir)`

### OperationsManager

```python
OperationsManager(
    max_concurrent_operations: int = 2,
    history_file: Optional[str] = None,
    auto_save_history: bool = True
)
```

Methods:
- `queue_copy(source_paths, dest_paths, priority, verify, preserve_metadata, conflict_action)`
- `queue_move(source_paths, dest_paths, priority, verify, preserve_metadata)`
- `queue_verify(source_paths, dest_paths, priority)`
- `pause_operation(operation_id)`, `resume_operation(operation_id)`, `cancel_operation(operation_id)`
- `get_operation(operation_id)`, `get_progress(operation_id)`
- `save_history()`, `load_history()`

## Integration with Smart Search Pro

```python
# In Smart Search Pro UI
from operations import OperationsManager, OperationPriority

class SmartSearchUI:
    def __init__(self):
        self.operations_manager = OperationsManager(
            max_concurrent_operations=2,
            history_file="operations_history.json"
        )

    def copy_search_results(self, results, destination):
        """Copy search results to destination."""
        source_paths = [r.path for r in results]
        dest_paths = [os.path.join(destination, os.path.basename(r.path))
                      for r in results]

        op_id = self.operations_manager.queue_copy(
            source_paths=source_paths,
            dest_paths=dest_paths,
            priority=OperationPriority.NORMAL,
            verify=True
        )

        return op_id
```

## License

Part of Smart Search Pro. See main project license.

## Version

1.0.0 - Initial TeraCopy-style implementation

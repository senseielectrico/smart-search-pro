"""
Virtual File System - Encrypted Virtual Drive
Mount encrypted containers as virtual file systems

Features:
- Directory structure inside vault
- File metadata encryption
- Streaming encryption for large files
- Path traversal protection
- Virtual mount points
"""

import os
import json
import time
from pathlib import Path, PurePosixPath
from typing import Dict, List, Optional, Any, BinaryIO
from dataclasses import dataclass, asdict
from io import BytesIO


@dataclass
class VirtualFileInfo:
    """Information about a file in the virtual filesystem"""
    path: str
    size: int
    created: float
    modified: float
    is_dir: bool
    permissions: int = 0o644
    owner: str = "user"
    group: str = "user"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VirtualFileInfo':
        return cls(**data)


class VirtualFileSystem:
    """
    Virtual encrypted filesystem inside vault

    Provides a directory structure with file operations
    All data is encrypted in the underlying vault
    """

    def __init__(self, vault_instance=None):
        """
        Initialize virtual filesystem

        Args:
            vault_instance: Instance of SecureVault
        """
        self.vault = vault_instance
        self._file_tree: Dict[str, VirtualFileInfo] = {}
        self._mounted = False
        self._mount_point = "/"

    def mount(self, vault_instance) -> bool:
        """
        Mount virtual filesystem

        Args:
            vault_instance: Unlocked SecureVault instance

        Returns:
            True if mounted successfully
        """
        if vault_instance is None:
            raise ValueError("Vault instance required")

        if vault_instance._is_locked:
            raise PermissionError("Vault must be unlocked first")

        self.vault = vault_instance
        self._load_file_tree()
        self._mounted = True

        return True

    def unmount(self) -> bool:
        """Unmount virtual filesystem"""
        if self._mounted:
            self._save_file_tree()
            self._mounted = False
            self._file_tree = {}

        return True

    def _load_file_tree(self) -> None:
        """Load file tree from vault metadata"""
        if 'file_tree' in self.vault._vault_data['metadata']:
            tree_data = self.vault._vault_data['metadata']['file_tree']
            self._file_tree = {
                path: VirtualFileInfo.from_dict(info)
                for path, info in tree_data.items()
            }
        else:
            # Initialize with root directory
            self._file_tree = {
                '/': VirtualFileInfo(
                    path='/',
                    size=0,
                    created=time.time(),
                    modified=time.time(),
                    is_dir=True
                )
            }

    def _save_file_tree(self) -> None:
        """Save file tree to vault metadata"""
        if self.vault:
            tree_data = {
                path: info.to_dict()
                for path, info in self._file_tree.items()
            }
            self.vault._vault_data['metadata']['file_tree'] = tree_data

    def _normalize_path(self, path: str) -> str:
        """Normalize virtual path"""
        # Convert to POSIX path and normalize
        normalized = str(PurePosixPath(path))

        # Ensure absolute path
        if not normalized.startswith('/'):
            normalized = '/' + normalized

        # Remove trailing slash (except for root)
        if normalized != '/' and normalized.endswith('/'):
            normalized = normalized[:-1]

        return normalized

    def _validate_path(self, path: str) -> str:
        """
        Validate and sanitize path (prevent path traversal)

        Returns:
            Normalized safe path

        Raises:
            ValueError if path is invalid
        """
        normalized = self._normalize_path(path)

        # Check for path traversal attempts
        if '..' in normalized:
            raise ValueError("Path traversal not allowed")

        return normalized

    def _get_parent_path(self, path: str) -> str:
        """Get parent directory path"""
        normalized = self._normalize_path(path)

        if normalized == '/':
            return '/'

        parent = str(PurePosixPath(normalized).parent)
        return parent if parent else '/'

    def _path_exists(self, path: str) -> bool:
        """Check if path exists in virtual filesystem"""
        normalized = self._normalize_path(path)
        return normalized in self._file_tree

    def mkdir(self, path: str, parents: bool = False) -> bool:
        """
        Create directory in virtual filesystem

        Args:
            path: Virtual directory path
            parents: Create parent directories if needed

        Returns:
            True if successful
        """
        if not self._mounted:
            raise RuntimeError("Filesystem not mounted")

        try:
            normalized = self._validate_path(path)

            # Check if already exists
            if self._path_exists(normalized):
                if self._file_tree[normalized].is_dir:
                    return True  # Already exists
                else:
                    raise FileExistsError(f"File exists: {normalized}")

            # Check parent exists
            parent = self._get_parent_path(normalized)

            if not self._path_exists(parent):
                if parents:
                    self.mkdir(parent, parents=True)
                else:
                    raise FileNotFoundError(f"Parent directory not found: {parent}")

            # Create directory
            self._file_tree[normalized] = VirtualFileInfo(
                path=normalized,
                size=0,
                created=time.time(),
                modified=time.time(),
                is_dir=True
            )

            self._save_file_tree()
            return True

        except Exception as e:
            print(f"mkdir error: {e}")
            return False

    def write_file(self, virtual_path: str, content: bytes) -> bool:
        """
        Write file to virtual filesystem

        Args:
            virtual_path: Virtual file path
            content: File content

        Returns:
            True if successful
        """
        if not self._mounted:
            raise RuntimeError("Filesystem not mounted")

        try:
            normalized = self._validate_path(virtual_path)

            # Check if it's a directory
            if self._path_exists(normalized) and self._file_tree[normalized].is_dir:
                raise IsADirectoryError(f"Is a directory: {normalized}")

            # Ensure parent directory exists
            parent = self._get_parent_path(normalized)
            if not self._path_exists(parent):
                self.mkdir(parent, parents=True)

            # Write to underlying vault
            if not self.vault.add_file(BytesIO(content), normalized):
                raise IOError("Failed to write to vault")

            # Update file tree
            now = time.time()
            if normalized in self._file_tree:
                # Update existing file
                self._file_tree[normalized].size = len(content)
                self._file_tree[normalized].modified = now
            else:
                # Create new file entry
                self._file_tree[normalized] = VirtualFileInfo(
                    path=normalized,
                    size=len(content),
                    created=now,
                    modified=now,
                    is_dir=False
                )

            self._save_file_tree()
            return True

        except Exception as e:
            print(f"write_file error: {e}")
            return False

    def read_file(self, virtual_path: str) -> Optional[bytes]:
        """
        Read file from virtual filesystem

        Args:
            virtual_path: Virtual file path

        Returns:
            File content or None if error
        """
        if not self._mounted:
            raise RuntimeError("Filesystem not mounted")

        try:
            normalized = self._validate_path(virtual_path)

            # Check exists
            if not self._path_exists(normalized):
                raise FileNotFoundError(f"File not found: {normalized}")

            # Check it's a file
            if self._file_tree[normalized].is_dir:
                raise IsADirectoryError(f"Is a directory: {normalized}")

            # Read from vault
            output = BytesIO()
            if not self.vault.extract_file(normalized, output):
                raise IOError("Failed to read from vault")

            return output.getvalue()

        except Exception as e:
            print(f"read_file error: {e}")
            return None

    def delete(self, path: str, recursive: bool = False) -> bool:
        """
        Delete file or directory

        Args:
            path: Virtual path to delete
            recursive: Delete directory and contents

        Returns:
            True if successful
        """
        if not self._mounted:
            raise RuntimeError("Filesystem not mounted")

        try:
            normalized = self._validate_path(path)

            # Check exists
            if not self._path_exists(normalized):
                raise FileNotFoundError(f"Not found: {normalized}")

            file_info = self._file_tree[normalized]

            # If directory, check if empty or recursive
            if file_info.is_dir:
                # Find children
                children = [
                    p for p in self._file_tree.keys()
                    if p.startswith(normalized + '/') and p != normalized
                ]

                if children and not recursive:
                    raise OSError(f"Directory not empty: {normalized}")

                # Delete children recursively
                for child in children:
                    self.delete(child, recursive=True)

            else:
                # Delete file from vault
                if not self.vault.remove_file(normalized):
                    raise IOError("Failed to delete from vault")

            # Remove from file tree
            del self._file_tree[normalized]

            self._save_file_tree()
            return True

        except Exception as e:
            print(f"delete error: {e}")
            return False

    def list_dir(self, path: str = '/') -> List[VirtualFileInfo]:
        """
        List directory contents

        Args:
            path: Virtual directory path

        Returns:
            List of file information objects
        """
        if not self._mounted:
            raise RuntimeError("Filesystem not mounted")

        try:
            normalized = self._validate_path(path)

            # Check exists and is directory
            if not self._path_exists(normalized):
                raise FileNotFoundError(f"Directory not found: {normalized}")

            if not self._file_tree[normalized].is_dir:
                raise NotADirectoryError(f"Not a directory: {normalized}")

            # Find direct children
            children = []
            prefix = normalized if normalized == '/' else normalized + '/'

            for file_path, file_info in self._file_tree.items():
                if file_path == normalized:
                    continue

                # Check if direct child
                if file_path.startswith(prefix):
                    relative = file_path[len(prefix):]
                    # Direct child has no more slashes
                    if '/' not in relative:
                        children.append(file_info)

            return sorted(children, key=lambda x: (not x.is_dir, x.path))

        except Exception as e:
            print(f"list_dir error: {e}")
            return []

    def move(self, src_path: str, dst_path: str) -> bool:
        """
        Move/rename file or directory

        Args:
            src_path: Source virtual path
            dst_path: Destination virtual path

        Returns:
            True if successful
        """
        if not self._mounted:
            raise RuntimeError("Filesystem not mounted")

        try:
            src_normalized = self._validate_path(src_path)
            dst_normalized = self._validate_path(dst_path)

            # Check source exists
            if not self._path_exists(src_normalized):
                raise FileNotFoundError(f"Source not found: {src_normalized}")

            # Check destination doesn't exist
            if self._path_exists(dst_normalized):
                raise FileExistsError(f"Destination exists: {dst_normalized}")

            # Ensure destination parent exists
            dst_parent = self._get_parent_path(dst_normalized)
            if not self._path_exists(dst_parent):
                raise FileNotFoundError(f"Destination parent not found: {dst_parent}")

            src_info = self._file_tree[src_normalized]

            # If directory, move all children
            if src_info.is_dir:
                # Find all children
                children = [
                    (p, info) for p, info in self._file_tree.items()
                    if p.startswith(src_normalized + '/') or p == src_normalized
                ]

                # Move each
                for child_path, child_info in children:
                    relative = child_path[len(src_normalized):]
                    new_path = dst_normalized + relative

                    # Update file tree
                    self._file_tree[new_path] = child_info
                    child_info.path = new_path
                    child_info.modified = time.time()

                    # Delete old entry
                    del self._file_tree[child_path]

            else:
                # Move file in vault
                # Read content
                content = self.read_file(src_normalized)
                if content is None:
                    raise IOError("Failed to read source file")

                # Write to new location
                if not self.write_file(dst_normalized, content):
                    raise IOError("Failed to write destination file")

                # Delete old
                self.delete(src_normalized)

            self._save_file_tree()
            return True

        except Exception as e:
            print(f"move error: {e}")
            return False

    def copy(self, src_path: str, dst_path: str) -> bool:
        """
        Copy file or directory

        Args:
            src_path: Source virtual path
            dst_path: Destination virtual path

        Returns:
            True if successful
        """
        if not self._mounted:
            raise RuntimeError("Filesystem not mounted")

        try:
            src_normalized = self._validate_path(src_path)
            dst_normalized = self._validate_path(dst_path)

            # Check source exists
            if not self._path_exists(src_normalized):
                raise FileNotFoundError(f"Source not found: {src_normalized}")

            # Check destination doesn't exist
            if self._path_exists(dst_normalized):
                raise FileExistsError(f"Destination exists: {dst_normalized}")

            src_info = self._file_tree[src_normalized]

            # If directory, copy recursively
            if src_info.is_dir:
                # Create destination directory
                self.mkdir(dst_normalized)

                # Copy children
                for child in self.list_dir(src_normalized):
                    child_src = child.path
                    child_dst = dst_normalized + '/' + os.path.basename(child.path)
                    self.copy(child_src, child_dst)

            else:
                # Copy file
                content = self.read_file(src_normalized)
                if content is None:
                    raise IOError("Failed to read source file")

                if not self.write_file(dst_normalized, content):
                    raise IOError("Failed to write destination file")

            return True

        except Exception as e:
            print(f"copy error: {e}")
            return False

    def get_info(self, path: str) -> Optional[VirtualFileInfo]:
        """
        Get file information

        Args:
            path: Virtual file path

        Returns:
            VirtualFileInfo or None
        """
        if not self._mounted:
            raise RuntimeError("Filesystem not mounted")

        try:
            normalized = self._validate_path(path)

            if not self._path_exists(normalized):
                return None

            return self._file_tree[normalized]

        except Exception:
            return None

    def get_tree_size(self) -> int:
        """
        Get total size of all files in virtual filesystem

        Returns:
            Total size in bytes
        """
        if not self._mounted:
            raise RuntimeError("Filesystem not mounted")

        total_size = sum(
            info.size for info in self._file_tree.values()
            if not info.is_dir
        )

        return total_size

    def find(self, pattern: str, path: str = '/', max_results: int = 1000) -> List[str]:
        """
        Find files matching pattern

        Args:
            pattern: Search pattern (supports wildcards)
            path: Starting directory
            max_results: Maximum results to return

        Returns:
            List of matching file paths
        """
        if not self._mounted:
            raise RuntimeError("Filesystem not mounted")

        import fnmatch

        normalized = self._validate_path(path)
        results = []

        for file_path in self._file_tree.keys():
            if not file_path.startswith(normalized):
                continue

            if fnmatch.fnmatch(os.path.basename(file_path), pattern):
                results.append(file_path)

                if len(results) >= max_results:
                    break

        return results

    def export_tree(self, output_dir: str, virtual_path: str = '/') -> bool:
        """
        Export virtual filesystem tree to real filesystem

        Args:
            output_dir: Output directory
            virtual_path: Virtual path to export

        Returns:
            True if successful
        """
        if not self._mounted:
            raise RuntimeError("Filesystem not mounted")

        try:
            normalized = self._validate_path(virtual_path)

            if not self._path_exists(normalized):
                raise FileNotFoundError(f"Path not found: {normalized}")

            file_info = self._file_tree[normalized]

            if file_info.is_dir:
                # Create directory
                output_path = os.path.join(output_dir, os.path.basename(normalized) or 'root')
                os.makedirs(output_path, exist_ok=True)

                # Export children
                for child in self.list_dir(normalized):
                    self.export_tree(output_path, child.path)

            else:
                # Export file
                content = self.read_file(normalized)
                if content:
                    output_path = os.path.join(output_dir, os.path.basename(normalized))
                    with open(output_path, 'wb') as f:
                        f.write(content)

                    # Restore timestamps
                    os.utime(output_path, (file_info.modified, file_info.modified))

            return True

        except Exception as e:
            print(f"export_tree error: {e}")
            return False

    def import_tree(self, source_dir: str, virtual_path: str = '/') -> bool:
        """
        Import real filesystem tree into virtual filesystem

        Args:
            source_dir: Source directory
            virtual_path: Virtual destination path

        Returns:
            True if successful
        """
        if not self._mounted:
            raise RuntimeError("Filesystem not mounted")

        try:
            normalized = self._validate_path(virtual_path)

            # Create destination directory if needed
            if not self._path_exists(normalized):
                self.mkdir(normalized, parents=True)

            # Import files and directories
            for root, dirs, files in os.walk(source_dir):
                # Calculate relative path
                rel_path = os.path.relpath(root, source_dir)

                if rel_path == '.':
                    current_vpath = normalized
                else:
                    current_vpath = os.path.join(normalized, rel_path).replace('\\', '/')

                # Create directories
                for dir_name in dirs:
                    vdir_path = os.path.join(current_vpath, dir_name).replace('\\', '/')
                    self.mkdir(vdir_path)

                # Import files
                for file_name in files:
                    real_file = os.path.join(root, file_name)
                    vfile_path = os.path.join(current_vpath, file_name).replace('\\', '/')

                    with open(real_file, 'rb') as f:
                        content = f.read()

                    self.write_file(vfile_path, content)

            return True

        except Exception as e:
            print(f"import_tree error: {e}")
            return False

"""
Conflict resolution system for file operations.
Handles file name conflicts with multiple resolution strategies.
"""

import os
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Callable
from pathlib import Path


class ConflictAction(Enum):
    """Actions to take when file conflicts occur."""
    SKIP = "skip"  # Skip the file
    OVERWRITE = "overwrite"  # Overwrite existing file
    OVERWRITE_OLDER = "overwrite_older"  # Overwrite only if source is newer
    RENAME = "rename"  # Rename to avoid conflict
    ASK = "ask"  # Ask user for each conflict


@dataclass
class ConflictResolution:
    """Resolution for a file conflict."""
    action: ConflictAction
    new_path: Optional[str] = None  # For RENAME action
    apply_to_all: bool = False  # Apply to all future conflicts


class ConflictResolver:
    """
    Handles file name conflicts during copy/move operations.
    Supports multiple resolution strategies and batch operations.
    """

    def __init__(
        self,
        default_action: ConflictAction = ConflictAction.ASK,
        rename_pattern: str = "{stem} ({counter}){suffix}"
    ):
        """
        Initialize conflict resolver.

        Args:
            default_action: Default action for conflicts
            rename_pattern: Pattern for renamed files. Variables:
                           {stem}: filename without extension
                           {suffix}: file extension with dot
                           {counter}: incrementing number
                           {timestamp}: current timestamp
        """
        self.default_action = default_action
        self.rename_pattern = rename_pattern
        self._apply_to_all: Optional[ConflictAction] = None
        self._callback: Optional[Callable] = None

    def set_callback(self, callback: Callable) -> None:
        """
        Set callback function for ASK action.

        Callback signature: callback(source: str, dest: str) -> ConflictResolution
        """
        self._callback = callback

    def resolve(
        self,
        source_path: str,
        dest_path: str
    ) -> ConflictResolution:
        """
        Resolve a file conflict.

        Args:
            source_path: Source file path
            dest_path: Destination file path

        Returns:
            ConflictResolution with action and new path if needed
        """
        # Check if "apply to all" is set
        if self._apply_to_all:
            action = self._apply_to_all
        else:
            action = self.default_action

        # Handle based on action
        if action == ConflictAction.SKIP:
            return ConflictResolution(action=ConflictAction.SKIP)

        elif action == ConflictAction.OVERWRITE:
            return ConflictResolution(action=ConflictAction.OVERWRITE)

        elif action == ConflictAction.OVERWRITE_OLDER:
            if self._should_overwrite_older(source_path, dest_path):
                return ConflictResolution(action=ConflictAction.OVERWRITE)
            else:
                return ConflictResolution(action=ConflictAction.SKIP)

        elif action == ConflictAction.RENAME:
            new_path = self._generate_unique_name(dest_path)
            return ConflictResolution(
                action=ConflictAction.RENAME,
                new_path=new_path
            )

        elif action == ConflictAction.ASK:
            if self._callback:
                return self._callback(source_path, dest_path)
            else:
                # Fallback to rename if no callback
                new_path = self._generate_unique_name(dest_path)
                return ConflictResolution(
                    action=ConflictAction.RENAME,
                    new_path=new_path
                )

        # Fallback
        return ConflictResolution(action=ConflictAction.SKIP)

    def set_apply_to_all(self, action: Optional[ConflictAction]) -> None:
        """Set action to apply to all future conflicts."""
        self._apply_to_all = action

    def reset_apply_to_all(self) -> None:
        """Reset "apply to all" setting."""
        self._apply_to_all = None

    def _should_overwrite_older(
        self,
        source_path: str,
        dest_path: str
    ) -> bool:
        """Check if source file is newer than destination."""
        try:
            source_mtime = os.path.getmtime(source_path)
            dest_mtime = os.path.getmtime(dest_path)
            return source_mtime > dest_mtime
        except (OSError, FileNotFoundError):
            return False

    def _generate_unique_name(self, dest_path: str) -> str:
        """
        Generate a unique file name using the rename pattern.

        Args:
            dest_path: Original destination path

        Returns:
            Unique file path
        """
        path = Path(dest_path)
        stem = path.stem
        suffix = path.suffix
        parent = path.parent

        counter = 1
        while True:
            # Format the new name
            new_name = self.rename_pattern.format(
                stem=stem,
                suffix=suffix,
                counter=counter
            )
            new_path = parent / new_name

            if not new_path.exists():
                return str(new_path)

            counter += 1
            if counter > 9999:  # Safety limit
                raise ValueError(f"Could not generate unique name for {dest_path}")

    def get_rename_preview(
        self,
        dest_path: str,
        max_suggestions: int = 5
    ) -> list[str]:
        """
        Get preview of potential rename options.

        Args:
            dest_path: Original destination path
            max_suggestions: Maximum number of suggestions

        Returns:
            List of suggested file names
        """
        path = Path(dest_path)
        stem = path.stem
        suffix = path.suffix
        parent = path.parent

        suggestions = []
        counter = 1

        while len(suggestions) < max_suggestions and counter < 100:
            new_name = self.rename_pattern.format(
                stem=stem,
                suffix=suffix,
                counter=counter
            )
            new_path = parent / new_name

            if not new_path.exists():
                suggestions.append(str(new_path))

            counter += 1

        return suggestions

    def custom_rename(
        self,
        dest_path: str,
        new_name: str
    ) -> str:
        """
        Create custom renamed path.

        Args:
            dest_path: Original destination path
            new_name: New file name (without directory)

        Returns:
            Full path with new name
        """
        path = Path(dest_path)
        return str(path.parent / new_name)

    def batch_rename_with_pattern(
        self,
        paths: list[str],
        pattern: str
    ) -> dict[str, str]:
        """
        Generate renamed paths for multiple files.

        Args:
            paths: List of file paths
            pattern: Rename pattern (supports {stem}, {suffix}, {counter}, {index})

        Returns:
            Dictionary mapping original paths to new paths
        """
        renamed = {}

        for index, path in enumerate(paths, 1):
            p = Path(path)
            stem = p.stem
            suffix = p.suffix

            counter = 1
            while True:
                new_name = pattern.format(
                    stem=stem,
                    suffix=suffix,
                    counter=counter,
                    index=index
                )
                new_path = p.parent / new_name

                if str(new_path) not in renamed.values() and not new_path.exists():
                    renamed[path] = str(new_path)
                    break

                counter += 1
                if counter > 9999:
                    raise ValueError(f"Could not generate unique name for {path}")

        return renamed

    def validate_destination(self, dest_path: str) -> tuple[bool, Optional[str]]:
        """
        Validate destination path for conflicts.

        Args:
            dest_path: Destination path to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        path = Path(dest_path)

        # Check if destination exists
        if path.exists():
            return False, f"File already exists: {dest_path}"

        # Check if parent directory exists
        if not path.parent.exists():
            return False, f"Parent directory does not exist: {path.parent}"

        # Check if parent is writable
        if not os.access(path.parent, os.W_OK):
            return False, f"Parent directory is not writable: {path.parent}"

        return True, None

    def get_conflict_info(
        self,
        source_path: str,
        dest_path: str
    ) -> dict:
        """
        Get detailed information about a file conflict.

        Args:
            source_path: Source file path
            dest_path: Destination file path

        Returns:
            Dictionary with conflict information
        """
        info = {
            'source_path': source_path,
            'dest_path': dest_path,
            'source_exists': os.path.exists(source_path),
            'dest_exists': os.path.exists(dest_path),
        }

        try:
            if info['source_exists']:
                source_stat = os.stat(source_path)
                info['source_size'] = source_stat.st_size
                info['source_mtime'] = source_stat.st_mtime

            if info['dest_exists']:
                dest_stat = os.stat(dest_path)
                info['dest_size'] = dest_stat.st_size
                info['dest_mtime'] = dest_stat.st_mtime

                # Compare files
                if info['source_exists']:
                    info['source_newer'] = info['source_mtime'] > info['dest_mtime']
                    info['source_larger'] = info['source_size'] > info['dest_size']
                    info['same_size'] = info['source_size'] == info['dest_size']

        except (OSError, FileNotFoundError) as e:
            info['error'] = str(e)

        return info

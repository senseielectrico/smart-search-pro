"""
Safe deletion actions for duplicate files.

Features:
- Move to recycle bin (send2trash)
- Move to designated folder
- Permanent delete (with confirmation)
- Hard link replacement (same volume)
- Symlink replacement
- Audit logging for all operations
- Rollback support for some operations
"""

import json
import logging
import os
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Union

try:
    from send2trash import send2trash
    HAS_SEND2TRASH = True
except ImportError:
    HAS_SEND2TRASH = False


class ActionType(Enum):
    """Types of actions that can be performed on duplicates."""
    RECYCLE_BIN = "recycle_bin"
    MOVE_TO_FOLDER = "move_to_folder"
    PERMANENT_DELETE = "permanent_delete"
    HARD_LINK = "hard_link"
    SYMLINK = "symlink"


@dataclass
class ActionResult:
    """Result of a duplicate action operation."""
    success: bool
    action_type: ActionType
    source_path: Path
    target_path: Optional[Path] = None
    error: Optional[str] = None
    bytes_freed: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary for logging."""
        return {
            'success': self.success,
            'action_type': self.action_type.value,
            'source_path': str(self.source_path),
            'target_path': str(self.target_path) if self.target_path else None,
            'error': self.error,
            'bytes_freed': self.bytes_freed,
            'timestamp': self.timestamp.isoformat(),
        }

    def __repr__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        return f"ActionResult({status}, {self.action_type.value}, {self.source_path})"


class AuditLogger:
    """
    Audit logger for tracking all duplicate file operations.

    Logs all actions to a JSON file for accountability and rollback support.
    """

    def __init__(self, log_path: Union[str, Path]):
        """
        Initialize audit logger.

        Args:
            log_path: Path to the audit log file
        """
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        # Also set up Python logging
        self.logger = logging.getLogger('duplicates.actions')
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_path.with_suffix('.log'))
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def log_action(self, result: ActionResult) -> None:
        """
        Log an action result.

        Args:
            result: The action result to log
        """
        # Write to JSON audit log
        try:
            # Read existing logs
            if self.log_path.exists():
                with open(self.log_path, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []

            # Append new log
            logs.append(result.to_dict())

            # Write back
            with open(self.log_path, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to write audit log: {e}")

        # Also log to text log
        if result.success:
            self.logger.info(
                f"{result.action_type.value}: {result.source_path} -> "
                f"{result.target_path or 'deleted'} ({result.bytes_freed} bytes freed)"
            )
        else:
            self.logger.error(
                f"{result.action_type.value} FAILED: {result.source_path} - {result.error}"
            )

    def get_recent_actions(self, count: int = 100) -> list[dict]:
        """
        Get recent actions from the audit log.

        Args:
            count: Number of recent actions to retrieve

        Returns:
            List of action dictionaries
        """
        try:
            if not self.log_path.exists():
                return []

            with open(self.log_path, 'r', encoding='utf-8') as f:
                logs = json.load(f)

            return logs[-count:]

        except Exception:
            return []


class DuplicateAction(ABC):
    """
    Abstract base class for duplicate file actions.

    All actions must implement the execute method and provide
    proper error handling and logging.
    """

    def __init__(self, audit_logger: Optional[AuditLogger] = None):
        """
        Initialize duplicate action.

        Args:
            audit_logger: Optional audit logger for tracking operations
        """
        self.audit_logger = audit_logger

    @abstractmethod
    def execute(
        self,
        source_path: Union[str, Path],
        target_path: Optional[Union[str, Path]] = None,
        **kwargs
    ) -> ActionResult:
        """
        Execute the action.

        Args:
            source_path: Path to the duplicate file to act on
            target_path: Optional target path (for move/link operations)
            **kwargs: Additional action-specific parameters

        Returns:
            ActionResult with operation details
        """
        pass

    def _log_result(self, result: ActionResult) -> None:
        """Log action result if logger is configured."""
        if self.audit_logger:
            self.audit_logger.log_action(result)


class RecycleBinAction(DuplicateAction):
    """
    Move files to the system recycle bin.

    This is the safest deletion method as files can be recovered.
    Requires send2trash library.
    """

    def execute(
        self,
        source_path: Union[str, Path],
        target_path: Optional[Union[str, Path]] = None,
        **kwargs
    ) -> ActionResult:
        """
        Move file to recycle bin.

        Args:
            source_path: Path to the file to recycle

        Returns:
            ActionResult
        """
        source = Path(source_path)
        result = ActionResult(
            success=False,
            action_type=ActionType.RECYCLE_BIN,
            source_path=source
        )

        try:
            if not HAS_SEND2TRASH:
                result.error = "send2trash library not available"
                self._log_result(result)
                return result

            if not source.exists():
                result.error = "File does not exist"
                self._log_result(result)
                return result

            # Get file size before deletion
            file_size = source.stat().st_size

            # Send to trash
            send2trash(str(source))

            result.success = True
            result.bytes_freed = file_size

        except Exception as e:
            result.error = str(e)

        self._log_result(result)
        return result


class MoveToFolderAction(DuplicateAction):
    """
    Move files to a designated folder.

    Useful for manual review before permanent deletion.
    """

    def execute(
        self,
        source_path: Union[str, Path],
        target_path: Optional[Union[str, Path]] = None,
        **kwargs
    ) -> ActionResult:
        """
        Move file to specified folder.

        Args:
            source_path: Path to the file to move
            target_path: Destination folder

        Returns:
            ActionResult
        """
        source = Path(source_path)
        result = ActionResult(
            success=False,
            action_type=ActionType.MOVE_TO_FOLDER,
            source_path=source
        )

        try:
            if target_path is None:
                result.error = "Target folder not specified"
                self._log_result(result)
                return result

            target_folder = Path(target_path)

            if not source.exists():
                result.error = "Source file does not exist"
                self._log_result(result)
                return result

            # Create target folder if needed
            target_folder.mkdir(parents=True, exist_ok=True)

            # Determine target file path
            target_file = target_folder / source.name

            # Handle name conflicts
            counter = 1
            while target_file.exists():
                stem = source.stem
                suffix = source.suffix
                target_file = target_folder / f"{stem}_{counter}{suffix}"
                counter += 1

            # Get file size
            file_size = source.stat().st_size

            # Move file
            shutil.move(str(source), str(target_file))

            result.success = True
            result.target_path = target_file
            result.bytes_freed = file_size

        except Exception as e:
            result.error = str(e)

        self._log_result(result)
        return result


class PermanentDeleteAction(DuplicateAction):
    """
    Permanently delete files.

    WARNING: This cannot be undone. Use with caution.
    """

    def __init__(
        self,
        audit_logger: Optional[AuditLogger] = None,
        require_confirmation: bool = True
    ):
        """
        Initialize permanent delete action.

        Args:
            audit_logger: Optional audit logger
            require_confirmation: Require explicit confirmation
        """
        super().__init__(audit_logger)
        self.require_confirmation = require_confirmation

    def execute(
        self,
        source_path: Union[str, Path],
        target_path: Optional[Union[str, Path]] = None,
        confirmed: bool = False,
        **kwargs
    ) -> ActionResult:
        """
        Permanently delete file.

        Args:
            source_path: Path to the file to delete
            confirmed: Confirmation flag (required if require_confirmation=True)

        Returns:
            ActionResult
        """
        source = Path(source_path)
        result = ActionResult(
            success=False,
            action_type=ActionType.PERMANENT_DELETE,
            source_path=source
        )

        try:
            if self.require_confirmation and not confirmed:
                result.error = "Deletion not confirmed"
                self._log_result(result)
                return result

            if not source.exists():
                result.error = "File does not exist"
                self._log_result(result)
                return result

            # Get file size
            file_size = source.stat().st_size

            # Delete file
            source.unlink()

            result.success = True
            result.bytes_freed = file_size

        except Exception as e:
            result.error = str(e)

        self._log_result(result)
        return result


class HardLinkAction(DuplicateAction):
    """
    Replace duplicate with hard link to original.

    This saves space while keeping the file accessible at both locations.
    Only works on the same filesystem/volume.
    """

    def execute(
        self,
        source_path: Union[str, Path],
        target_path: Optional[Union[str, Path]] = None,
        **kwargs
    ) -> ActionResult:
        """
        Replace source file with hard link to target.

        Args:
            source_path: Path to duplicate file (will be replaced)
            target_path: Path to original file (will be linked to)

        Returns:
            ActionResult
        """
        source = Path(source_path)
        result = ActionResult(
            success=False,
            action_type=ActionType.HARD_LINK,
            source_path=source
        )

        try:
            if target_path is None:
                result.error = "Target file not specified"
                self._log_result(result)
                return result

            target = Path(target_path)

            if not source.exists():
                result.error = "Source file does not exist"
                self._log_result(result)
                return result

            if not target.exists():
                result.error = "Target file does not exist"
                self._log_result(result)
                return result

            # Check if already hard linked
            if source.stat().st_ino == target.stat().st_ino:
                result.error = "Files are already hard linked"
                self._log_result(result)
                return result

            # Get file size
            file_size = source.stat().st_size

            # Create temporary backup
            backup_path = source.with_suffix(source.suffix + '.bak')
            shutil.copy2(str(source), str(backup_path))

            try:
                # Remove original
                source.unlink()

                # Create hard link
                os.link(str(target), str(source))

                # Remove backup
                backup_path.unlink()

                result.success = True
                result.target_path = target
                result.bytes_freed = file_size

            except Exception as e:
                # Restore from backup
                if backup_path.exists():
                    shutil.move(str(backup_path), str(source))
                raise

        except Exception as e:
            result.error = str(e)

        self._log_result(result)
        return result


class SymlinkAction(DuplicateAction):
    """
    Replace duplicate with symbolic link to original.

    Similar to hard links but works across filesystems.
    The symlink will break if the target is moved or deleted.
    """

    def execute(
        self,
        source_path: Union[str, Path],
        target_path: Optional[Union[str, Path]] = None,
        **kwargs
    ) -> ActionResult:
        """
        Replace source file with symlink to target.

        Args:
            source_path: Path to duplicate file (will be replaced)
            target_path: Path to original file (will be linked to)

        Returns:
            ActionResult
        """
        source = Path(source_path)
        result = ActionResult(
            success=False,
            action_type=ActionType.SYMLINK,
            source_path=source
        )

        try:
            if target_path is None:
                result.error = "Target file not specified"
                self._log_result(result)
                return result

            target = Path(target_path)

            if not source.exists():
                result.error = "Source file does not exist"
                self._log_result(result)
                return result

            if not target.exists():
                result.error = "Target file does not exist"
                self._log_result(result)
                return result

            # Get file size
            file_size = source.stat().st_size

            # Create temporary backup
            backup_path = source.with_suffix(source.suffix + '.bak')
            shutil.copy2(str(source), str(backup_path))

            try:
                # Remove original
                source.unlink()

                # Create symlink
                source.symlink_to(target)

                # Remove backup
                backup_path.unlink()

                result.success = True
                result.target_path = target
                result.bytes_freed = file_size

            except Exception as e:
                # Restore from backup
                if backup_path.exists():
                    shutil.move(str(backup_path), str(source))
                raise

        except Exception as e:
            result.error = str(e)

        self._log_result(result)
        return result


def execute_batch_action(
    action: DuplicateAction,
    file_paths: list[Union[str, Path]],
    target_path: Optional[Union[str, Path]] = None,
    **kwargs
) -> list[ActionResult]:
    """
    Execute an action on multiple files.

    Args:
        action: The action to execute
        file_paths: List of file paths to process
        target_path: Optional target path for the action
        **kwargs: Additional action parameters

    Returns:
        List of ActionResults
    """
    results = []

    for file_path in file_paths:
        result = action.execute(file_path, target_path, **kwargs)
        results.append(result)

    return results


def get_action_summary(results: list[ActionResult]) -> dict:
    """
    Get summary statistics from action results.

    Args:
        results: List of action results

    Returns:
        Dict with summary statistics
    """
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]

    return {
        'total': len(results),
        'successful': len(successful),
        'failed': len(failed),
        'total_bytes_freed': sum(r.bytes_freed for r in successful),
        'success_rate': (len(successful) / len(results) * 100) if results else 0,
        'errors': [r.error for r in failed if r.error],
    }

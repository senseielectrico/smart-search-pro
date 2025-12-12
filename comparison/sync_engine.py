"""
Sync Engine - Synchronize directories with conflict resolution and undo capability.

Features:
- Copy missing files from source to target
- Delete extra files from target
- Bidirectional sync
- Preview changes before executing
- Conflict resolution strategies
- Progress callbacks
- Operation logging for undo
"""

import json
import shutil
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

# Add parent directory to path for core imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.logger import get_logger
from .folder_comparator import (
    FolderComparator,
    ComparisonResult,
    FileComparison,
    FileStatus,
    ComparisonMode
)

logger = get_logger(__name__)


class SyncAction(Enum):
    """Actions that can be performed during sync."""
    COPY_TO_TARGET = "copy_to_target"       # Copy file to target
    COPY_TO_SOURCE = "copy_to_source"       # Copy file to source (bidirectional)
    DELETE_FROM_TARGET = "delete_target"    # Delete from target
    DELETE_FROM_SOURCE = "delete_source"    # Delete from source (bidirectional)
    UPDATE_TARGET = "update_target"         # Update file in target (newer)
    UPDATE_SOURCE = "update_source"         # Update file in source (newer)
    SKIP = "skip"                           # Skip this file


class ConflictResolution(Enum):
    """Strategies for resolving conflicts."""
    NEWER_WINS = "newer"       # Use file with newer modification time
    LARGER_WINS = "larger"     # Use larger file
    SOURCE_WINS = "source"     # Always prefer source
    TARGET_WINS = "target"     # Always prefer target
    MANUAL = "manual"          # Require manual resolution
    SKIP = "skip"              # Skip conflicting files


@dataclass
class SyncConflict:
    """Represents a sync conflict requiring resolution."""
    relative_path: str
    source_path: Optional[Path] = None
    target_path: Optional[Path] = None
    source_size: int = 0
    target_size: int = 0
    source_modified: Optional[datetime] = None
    target_modified: Optional[datetime] = None
    reason: str = ""
    suggested_action: Optional[SyncAction] = None
    resolved_action: Optional[SyncAction] = None


@dataclass
class SyncOperation:
    """Single sync operation to be performed."""
    action: SyncAction
    relative_path: str
    source_path: Optional[Path] = None
    target_path: Optional[Path] = None
    size: int = 0
    executed: bool = False
    success: bool = False
    error: Optional[str] = None
    timestamp: Optional[datetime] = None


@dataclass
class SyncResult:
    """Result of sync operation."""
    source_dir: Path
    target_dir: Path
    operations: List[SyncOperation] = field(default_factory=list)
    conflicts: List[SyncConflict] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    dry_run: bool = False

    @property
    def duration(self) -> float:
        """Get sync duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def total_operations(self) -> int:
        """Total number of operations."""
        return len(self.operations)

    @property
    def successful_operations(self) -> int:
        """Number of successful operations."""
        return sum(1 for op in self.operations if op.success)

    @property
    def failed_operations(self) -> int:
        """Number of failed operations."""
        return sum(1 for op in self.operations if op.executed and not op.success)

    @property
    def total_bytes_transferred(self) -> int:
        """Total bytes transferred in successful operations."""
        return sum(
            op.size for op in self.operations
            if op.success and op.action in [
                SyncAction.COPY_TO_TARGET,
                SyncAction.COPY_TO_SOURCE,
                SyncAction.UPDATE_TARGET,
                SyncAction.UPDATE_SOURCE
            ]
        )


class SyncEngine:
    """
    Engine for synchronizing directories with conflict resolution.

    Features:
    - Preview mode (dry run)
    - Conflict resolution
    - Progress tracking
    - Operation logging
    - Undo capability

    Example:
        >>> engine = SyncEngine(conflict_resolution=ConflictResolution.NEWER_WINS)
        >>> result = engine.sync(
        ...     source='/path/to/source',
        ...     target='/path/to/target',
        ...     copy_missing=True,
        ...     delete_extra=False,
        ...     dry_run=True  # Preview first
        ... )
        >>> print(f"Operations: {result.total_operations}")
    """

    def __init__(
        self,
        conflict_resolution: ConflictResolution = ConflictResolution.NEWER_WINS,
        log_file: Optional[Path] = None
    ):
        """
        Initialize sync engine.

        Args:
            conflict_resolution: Strategy for resolving conflicts
            log_file: Path to operation log file (for undo capability)
        """
        self.conflict_resolution = conflict_resolution
        self.log_file = log_file or (
            Path.home() / '.cache' / 'smart_search' / 'sync_operations.jsonl'
        )
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def _resolve_conflict(
        self,
        comparison: FileComparison,
        strategy: ConflictResolution
    ) -> SyncAction:
        """
        Resolve conflict based on strategy.

        Args:
            comparison: File comparison with conflict
            strategy: Resolution strategy

        Returns:
            Recommended sync action
        """
        if strategy == ConflictResolution.SOURCE_WINS:
            return SyncAction.UPDATE_TARGET

        elif strategy == ConflictResolution.TARGET_WINS:
            return SyncAction.UPDATE_SOURCE

        elif strategy == ConflictResolution.NEWER_WINS:
            if comparison.source_modified and comparison.target_modified:
                if comparison.source_modified > comparison.target_modified:
                    return SyncAction.UPDATE_TARGET
                elif comparison.target_modified > comparison.source_modified:
                    return SyncAction.UPDATE_SOURCE
            return SyncAction.SKIP

        elif strategy == ConflictResolution.LARGER_WINS:
            if comparison.source_size > comparison.target_size:
                return SyncAction.UPDATE_TARGET
            elif comparison.target_size > comparison.source_size:
                return SyncAction.UPDATE_SOURCE
            return SyncAction.SKIP

        elif strategy == ConflictResolution.SKIP:
            return SyncAction.SKIP

        elif strategy == ConflictResolution.MANUAL:
            # Mark for manual resolution
            return SyncAction.SKIP

        return SyncAction.SKIP

    def _create_operations(
        self,
        comparison_result: ComparisonResult,
        copy_missing: bool = True,
        delete_extra: bool = False,
        update_different: bool = True,
        bidirectional: bool = False
    ) -> Tuple[List[SyncOperation], List[SyncConflict]]:
        """
        Create sync operations from comparison result.

        Args:
            comparison_result: Result of folder comparison
            copy_missing: Copy files missing in target
            delete_extra: Delete extra files from target
            update_different: Update different files
            bidirectional: Enable bidirectional sync

        Returns:
            Tuple of (operations, conflicts)
        """
        operations = []
        conflicts = []

        for comp in comparison_result.comparisons:
            if comp.status == FileStatus.MISSING_IN_TARGET and copy_missing:
                # Copy to target
                operations.append(SyncOperation(
                    action=SyncAction.COPY_TO_TARGET,
                    relative_path=comp.relative_path,
                    source_path=comp.source_path,
                    target_path=comparison_result.target_dir / comp.relative_path,
                    size=comp.source_size
                ))

            elif comp.status == FileStatus.EXTRA_IN_TARGET:
                if delete_extra:
                    # Delete from target
                    operations.append(SyncOperation(
                        action=SyncAction.DELETE_FROM_TARGET,
                        relative_path=comp.relative_path,
                        target_path=comp.target_path,
                        size=comp.target_size
                    ))
                elif bidirectional:
                    # Copy to source (bidirectional)
                    operations.append(SyncOperation(
                        action=SyncAction.COPY_TO_SOURCE,
                        relative_path=comp.relative_path,
                        source_path=comparison_result.source_dir / comp.relative_path,
                        target_path=comp.target_path,
                        size=comp.target_size
                    ))

            elif comp.status == FileStatus.DIFFERENT and update_different:
                # Conflict - needs resolution
                conflict = SyncConflict(
                    relative_path=comp.relative_path,
                    source_path=comp.source_path,
                    target_path=comp.target_path,
                    source_size=comp.source_size,
                    target_size=comp.target_size,
                    source_modified=comp.source_modified,
                    target_modified=comp.target_modified,
                    reason="Files are different"
                )

                # Resolve conflict
                resolved_action = self._resolve_conflict(comp, self.conflict_resolution)
                conflict.suggested_action = resolved_action
                conflict.resolved_action = resolved_action

                if resolved_action == SyncAction.UPDATE_TARGET:
                    operations.append(SyncOperation(
                        action=SyncAction.UPDATE_TARGET,
                        relative_path=comp.relative_path,
                        source_path=comp.source_path,
                        target_path=comp.target_path,
                        size=comp.source_size
                    ))
                elif resolved_action == SyncAction.UPDATE_SOURCE and bidirectional:
                    operations.append(SyncOperation(
                        action=SyncAction.UPDATE_SOURCE,
                        relative_path=comp.relative_path,
                        source_path=comp.source_path,
                        target_path=comp.target_path,
                        size=comp.target_size
                    ))
                else:
                    # Skip or manual resolution needed
                    conflicts.append(conflict)

        return operations, conflicts

    def _execute_operation(self, operation: SyncOperation) -> None:
        """
        Execute a single sync operation.

        Args:
            operation: Operation to execute

        Raises:
            Exception on operation failure
        """
        operation.executed = True
        operation.timestamp = datetime.now()

        try:
            if operation.action == SyncAction.COPY_TO_TARGET:
                # Copy source to target
                if operation.target_path:
                    operation.target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(operation.source_path, operation.target_path)

            elif operation.action == SyncAction.COPY_TO_SOURCE:
                # Copy target to source
                if operation.source_path:
                    operation.source_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(operation.target_path, operation.source_path)

            elif operation.action == SyncAction.DELETE_FROM_TARGET:
                # Delete from target
                if operation.target_path and operation.target_path.exists():
                    operation.target_path.unlink()

            elif operation.action == SyncAction.DELETE_FROM_SOURCE:
                # Delete from source
                if operation.source_path and operation.source_path.exists():
                    operation.source_path.unlink()

            elif operation.action == SyncAction.UPDATE_TARGET:
                # Update target with source
                if operation.target_path:
                    operation.target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(operation.source_path, operation.target_path)

            elif operation.action == SyncAction.UPDATE_SOURCE:
                # Update source with target
                if operation.source_path:
                    operation.source_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(operation.target_path, operation.source_path)

            operation.success = True

        except Exception as e:
            operation.success = False
            operation.error = str(e)
            logger.error(f"Failed to execute operation: {operation.action.value} - {e}")
            raise

    def _log_operation(self, operation: SyncOperation, result: SyncResult) -> None:
        """
        Log operation to file for undo capability.

        Args:
            operation: Executed operation
            result: Sync result context
        """
        try:
            log_entry = {
                'timestamp': operation.timestamp.isoformat() if operation.timestamp else None,
                'source_dir': str(result.source_dir),
                'target_dir': str(result.target_dir),
                'action': operation.action.value,
                'relative_path': operation.relative_path,
                'source_path': str(operation.source_path) if operation.source_path else None,
                'target_path': str(operation.target_path) if operation.target_path else None,
                'size': operation.size,
                'success': operation.success,
                'error': operation.error
            }

            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

        except Exception as e:
            logger.error(f"Failed to log operation: {e}")

    def sync(
        self,
        source: str | Path,
        target: str | Path,
        copy_missing: bool = True,
        delete_extra: bool = False,
        update_different: bool = True,
        bidirectional: bool = False,
        dry_run: bool = False,
        comparison_mode: ComparisonMode = ComparisonMode.CONTENT_HASH,
        recursive: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> SyncResult:
        """
        Synchronize two directories.

        Args:
            source: Source directory path
            target: Target directory path
            copy_missing: Copy files missing in target
            delete_extra: Delete extra files from target
            update_different: Update files that are different
            bidirectional: Enable bidirectional sync
            dry_run: Preview operations without executing
            comparison_mode: Mode for comparing files
            recursive: Recursively sync subdirectories
            progress_callback: Optional callback(completed, total)

        Returns:
            SyncResult with operation details
        """
        source_dir = Path(source)
        target_dir = Path(target)

        result = SyncResult(
            source_dir=source_dir,
            target_dir=target_dir,
            start_time=datetime.now(),
            dry_run=dry_run
        )

        try:
            # Step 1: Compare directories
            comparator = FolderComparator(mode=comparison_mode)
            comparison_result = comparator.compare(
                source=source_dir,
                target=target_dir,
                recursive=recursive
            )

            if comparison_result.error:
                result.error = comparison_result.error
                return result

            # Step 2: Create sync operations
            operations, conflicts = self._create_operations(
                comparison_result,
                copy_missing=copy_missing,
                delete_extra=delete_extra,
                update_different=update_different,
                bidirectional=bidirectional
            )

            result.operations = operations
            result.conflicts = conflicts

            # Step 3: Execute operations (if not dry run)
            if not dry_run:
                total = len(operations)
                for idx, operation in enumerate(operations):
                    try:
                        self._execute_operation(operation)
                        self._log_operation(operation, result)

                        if progress_callback:
                            progress_callback(idx + 1, total)

                    except Exception as e:
                        # Continue with remaining operations even if one fails
                        logger.error(f"Operation failed: {operation.relative_path} - {e}")

        except Exception as e:
            result.error = str(e)
            logger.error(f"Sync failed: {e}")

        result.end_time = datetime.now()
        return result

    def get_undo_operations(
        self,
        since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get logged operations for undo capability.

        Args:
            since: Only get operations after this time
            limit: Maximum number of operations to return

        Returns:
            List of operation log entries
        """
        operations = []

        try:
            if not self.log_file.exists():
                return operations

            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())

                        # Filter by timestamp
                        if since:
                            entry_time = datetime.fromisoformat(entry['timestamp'])
                            if entry_time < since:
                                continue

                        operations.append(entry)

                    except (json.JSONDecodeError, KeyError):
                        continue

            # Sort by timestamp descending (newest first)
            operations.sort(
                key=lambda x: x.get('timestamp', ''),
                reverse=True
            )

            # Apply limit
            if limit:
                operations = operations[:limit]

        except Exception as e:
            logger.error(f"Failed to read operation log: {e}")

        return operations


def format_sync_summary(result: SyncResult) -> str:
    """
    Format sync result as a summary string.

    Args:
        result: Sync result to format

    Returns:
        Formatted summary string
    """
    lines = [
        "=" * 80,
        "SYNC SUMMARY",
        "=" * 80,
        f"Source:      {result.source_dir}",
        f"Target:      {result.target_dir}",
        f"Mode:        {'DRY RUN' if result.dry_run else 'EXECUTE'}",
        f"Duration:    {result.duration:.2f}s",
        "-" * 80,
        f"Total Operations:      {result.total_operations}",
        f"  Successful:          {result.successful_operations}",
        f"  Failed:              {result.failed_operations}",
        f"Conflicts:             {len(result.conflicts)}",
        f"Bytes Transferred:     {result.total_bytes_transferred:,}",
        "=" * 80
    ]

    # Group operations by type
    if result.operations:
        action_counts = defaultdict(int)
        for op in result.operations:
            action_counts[op.action] += 1

        lines.append("\nOperations by Type:")
        for action, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {action.value}: {count}")

    return '\n'.join(lines)

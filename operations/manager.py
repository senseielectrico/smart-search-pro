"""
Operations manager with queue system for file operations.
Manages multiple concurrent operations with pause/resume/cancel capabilities.
"""

import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Callable
from datetime import datetime
from queue import Queue, PriorityQueue
from threading import Thread, Lock, Event
import json
from pathlib import Path

from .copier import FileCopier
from .mover import FileMover
from .verifier import FileVerifier, HashAlgorithm
from .conflicts import ConflictResolver, ConflictAction, ConflictResolution
from .progress import ProgressTracker, OperationProgress


class OperationType(Enum):
    """Types of file operations."""
    COPY = "copy"
    MOVE = "move"
    DELETE = "delete"
    VERIFY = "verify"


class OperationStatus(Enum):
    """Status of an operation."""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OperationPriority(Enum):
    """Priority levels for operations."""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0


@dataclass
class FileOperation:
    """Represents a file operation."""
    operation_id: str
    operation_type: OperationType
    source_paths: List[str]
    dest_paths: List[str]
    status: OperationStatus = OperationStatus.QUEUED
    priority: OperationPriority = OperationPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    verify: bool = False
    preserve_metadata: bool = True
    conflict_action: ConflictAction = ConflictAction.ASK

    # Progress tracking
    total_size: int = 0
    processed_size: int = 0
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0

    def __lt__(self, other):
        """Compare operations by priority for queue ordering."""
        return self.priority.value < other.priority.value

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'operation_id': self.operation_id,
            'operation_type': self.operation_type.value,
            'source_paths': self.source_paths,
            'dest_paths': self.dest_paths,
            'status': self.status.value,
            'priority': self.priority.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error': self.error,
            'verify': self.verify,
            'preserve_metadata': self.preserve_metadata,
            'conflict_action': self.conflict_action.value,
            'total_size': self.total_size,
            'processed_size': self.processed_size,
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'failed_files': self.failed_files,
        }


class OperationsManager:
    """
    Manages file operations with queue system, audit trail, and history.
    Supports pause/resume/cancel for all operations.
    """

    def __init__(
        self,
        max_concurrent_operations: int = 2,
        history_file: Optional[str] = None,
        auto_save_history: bool = True
    ):
        """
        Initialize operations manager.

        Args:
            max_concurrent_operations: Maximum concurrent operations
            history_file: Path to save operation history
            auto_save_history: Automatically save history after each operation
        """
        self.max_concurrent_operations = max_concurrent_operations
        self.history_file = history_file
        self.auto_save_history = auto_save_history

        # Operation tracking
        self._operations: Dict[str, FileOperation] = {}
        self._operation_queue: PriorityQueue = PriorityQueue()
        self._active_operations: Dict[str, Thread] = {}
        self._lock = Lock()

        # Progress tracking
        self._progress_tracker = ProgressTracker()

        # Components
        self._copier = FileCopier(max_workers=4)
        self._mover = FileMover()
        self._verifier = FileVerifier()
        self._conflict_resolver = ConflictResolver()

        # Worker threads
        self._workers: List[Thread] = []
        self._shutdown_event = Event()
        self._start_workers()

        # Load history if available
        if history_file and Path(history_file).exists():
            self.load_history()

    def _start_workers(self) -> None:
        """Start worker threads to process queue."""
        for i in range(self.max_concurrent_operations):
            worker = Thread(
                target=self._worker_loop,
                name=f"OperationWorker-{i}",
                daemon=True
            )
            worker.start()
            self._workers.append(worker)

    def _worker_loop(self) -> None:
        """Worker thread main loop."""
        while not self._shutdown_event.is_set():
            try:
                # Get next operation from queue (with timeout)
                priority, operation_id = self._operation_queue.get(timeout=1.0)

                with self._lock:
                    if operation_id not in self._operations:
                        continue

                    operation = self._operations[operation_id]

                    # Skip if already processed
                    if operation.status != OperationStatus.QUEUED:
                        continue

                    # Mark as in progress
                    operation.status = OperationStatus.IN_PROGRESS
                    operation.started_at = datetime.now()

                # Execute operation
                self._execute_operation(operation)

                # Mark queue task as done
                self._operation_queue.task_done()

            except Exception:
                # Timeout or other error - continue
                continue

    def _execute_operation(self, operation: FileOperation) -> None:
        """
        Execute a file operation.

        Args:
            operation: Operation to execute
        """
        try:
            # Start progress tracking
            file_sizes = []
            for path in operation.source_paths:
                try:
                    if Path(path).is_file():
                        file_sizes.append(Path(path).stat().st_size)
                    else:
                        file_sizes.append(0)
                except:
                    file_sizes.append(0)

            self._progress_tracker.start_operation(
                operation.operation_id,
                operation.source_paths,
                file_sizes
            )

            # Execute based on operation type
            if operation.operation_type == OperationType.COPY:
                self._execute_copy(operation)
            elif operation.operation_type == OperationType.MOVE:
                self._execute_move(operation)
            elif operation.operation_type == OperationType.VERIFY:
                self._execute_verify(operation)
            elif operation.operation_type == OperationType.DELETE:
                self._execute_delete(operation)

            # Mark as completed
            with self._lock:
                operation.status = OperationStatus.COMPLETED
                operation.completed_at = datetime.now()

            self._progress_tracker.complete_operation(operation.operation_id)

        except Exception as e:
            # Mark as failed
            with self._lock:
                operation.status = OperationStatus.FAILED
                operation.error = str(e)
                operation.completed_at = datetime.now()

        finally:
            # Save history if enabled
            if self.auto_save_history and self.history_file:
                self.save_history()

    def _execute_copy(self, operation: FileOperation) -> None:
        """Execute copy operation."""
        file_pairs = list(zip(operation.source_paths, operation.dest_paths))

        def progress_callback(file_path: str, copied: int, total: int):
            self._progress_tracker.update_file(
                operation.operation_id,
                file_path,
                copied
            )

        results = self._copier.copy_files_batch(
            file_pairs,
            progress_callback,
            operation.preserve_metadata
        )

        # Update operation stats
        for dest, (success, error) in results.items():
            if success:
                operation.processed_files += 1
            else:
                operation.failed_files += 1
            self._progress_tracker.complete_file(
                operation.operation_id,
                dest,
                error
            )

    def _execute_move(self, operation: FileOperation) -> None:
        """Execute move operation."""
        file_pairs = list(zip(operation.source_paths, operation.dest_paths))

        def progress_callback(file_path: str, copied: int, total: int):
            self._progress_tracker.update_file(
                operation.operation_id,
                file_path,
                copied
            )

        results = self._mover.move_files_batch(file_pairs, progress_callback)

        # Update operation stats
        for dest, (success, error) in results.items():
            if success:
                operation.processed_files += 1
            else:
                operation.failed_files += 1
            self._progress_tracker.complete_file(
                operation.operation_id,
                dest,
                error
            )

    def _execute_verify(self, operation: FileOperation) -> None:
        """Execute verify operation."""
        file_pairs = list(zip(operation.source_paths, operation.dest_paths))
        results = self._verifier.verify_batch(file_pairs)

        # Update operation stats
        for dest, (is_valid, error) in results.items():
            if is_valid:
                operation.processed_files += 1
            else:
                operation.failed_files += 1
            self._progress_tracker.complete_file(
                operation.operation_id,
                dest,
                None if is_valid else error
            )

    def _execute_delete(self, operation: FileOperation) -> None:
        """Execute delete operation."""
        for path in operation.source_paths:
            try:
                if Path(path).is_file():
                    Path(path).unlink()
                elif Path(path).is_dir():
                    import shutil
                    shutil.rmtree(path)
                operation.processed_files += 1
            except Exception as e:
                operation.failed_files += 1
                operation.error = str(e)

            self._progress_tracker.complete_file(
                operation.operation_id,
                path,
                operation.error
            )

    def queue_copy(
        self,
        source_paths: List[str],
        dest_paths: List[str],
        priority: OperationPriority = OperationPriority.NORMAL,
        verify: bool = False,
        preserve_metadata: bool = True,
        conflict_action: ConflictAction = ConflictAction.ASK
    ) -> str:
        """
        Queue a copy operation.

        Returns:
            Operation ID
        """
        operation_id = str(uuid.uuid4())

        operation = FileOperation(
            operation_id=operation_id,
            operation_type=OperationType.COPY,
            source_paths=source_paths,
            dest_paths=dest_paths,
            priority=priority,
            verify=verify,
            preserve_metadata=preserve_metadata,
            conflict_action=conflict_action,
            total_files=len(source_paths)
        )

        with self._lock:
            self._operations[operation_id] = operation
            self._operation_queue.put((priority.value, operation_id))

        return operation_id

    def queue_move(
        self,
        source_paths: List[str],
        dest_paths: List[str],
        priority: OperationPriority = OperationPriority.NORMAL,
        verify: bool = False,
        preserve_metadata: bool = True
    ) -> str:
        """
        Queue a move operation.

        Returns:
            Operation ID
        """
        operation_id = str(uuid.uuid4())

        operation = FileOperation(
            operation_id=operation_id,
            operation_type=OperationType.MOVE,
            source_paths=source_paths,
            dest_paths=dest_paths,
            priority=priority,
            verify=verify,
            preserve_metadata=preserve_metadata,
            total_files=len(source_paths)
        )

        with self._lock:
            self._operations[operation_id] = operation
            self._operation_queue.put((priority.value, operation_id))

        return operation_id

    def queue_verify(
        self,
        source_paths: List[str],
        dest_paths: List[str],
        priority: OperationPriority = OperationPriority.NORMAL
    ) -> str:
        """
        Queue a verification operation.

        Returns:
            Operation ID
        """
        operation_id = str(uuid.uuid4())

        operation = FileOperation(
            operation_id=operation_id,
            operation_type=OperationType.VERIFY,
            source_paths=source_paths,
            dest_paths=dest_paths,
            priority=priority,
            total_files=len(source_paths)
        )

        with self._lock:
            self._operations[operation_id] = operation
            self._operation_queue.put((priority.value, operation_id))

        return operation_id

    def pause_operation(self, operation_id: str) -> bool:
        """Pause an operation."""
        with self._lock:
            if operation_id in self._operations:
                operation = self._operations[operation_id]
                if operation.status == OperationStatus.IN_PROGRESS:
                    operation.status = OperationStatus.PAUSED
                    self._progress_tracker.pause_operation(operation_id)
                    return True
        return False

    def resume_operation(self, operation_id: str) -> bool:
        """Resume a paused operation."""
        with self._lock:
            if operation_id in self._operations:
                operation = self._operations[operation_id]
                if operation.status == OperationStatus.PAUSED:
                    operation.status = OperationStatus.IN_PROGRESS
                    self._progress_tracker.resume_operation(operation_id)
                    return True
        return False

    def cancel_operation(self, operation_id: str) -> bool:
        """Cancel an operation."""
        with self._lock:
            if operation_id in self._operations:
                operation = self._operations[operation_id]
                if operation.status in (OperationStatus.QUEUED, OperationStatus.IN_PROGRESS):
                    operation.status = OperationStatus.CANCELLED
                    operation.completed_at = datetime.now()
                    return True
        return False

    def get_operation(self, operation_id: str) -> Optional[FileOperation]:
        """Get operation by ID."""
        with self._lock:
            return self._operations.get(operation_id)

    def get_all_operations(self) -> List[FileOperation]:
        """Get all operations."""
        with self._lock:
            return list(self._operations.values())

    def get_active_operations(self) -> List[FileOperation]:
        """Get currently active operations."""
        with self._lock:
            return [
                op for op in self._operations.values()
                if op.status == OperationStatus.IN_PROGRESS
            ]

    def get_queued_operations(self) -> List[FileOperation]:
        """Get queued operations."""
        with self._lock:
            return [
                op for op in self._operations.values()
                if op.status == OperationStatus.QUEUED
            ]

    def get_progress(self, operation_id: str) -> Optional[OperationProgress]:
        """Get progress for an operation."""
        return self._progress_tracker.get_progress(operation_id)

    def clear_completed(self) -> int:
        """Clear completed operations from memory."""
        with self._lock:
            completed_ids = [
                op_id for op_id, op in self._operations.items()
                if op.status in (OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.CANCELLED)
            ]
            for op_id in completed_ids:
                del self._operations[op_id]
                self._progress_tracker.remove_operation(op_id)
            return len(completed_ids)

    def save_history(self) -> None:
        """Save operation history to file."""
        if not self.history_file:
            return

        with self._lock:
            history_data = {
                'operations': [op.to_dict() for op in self._operations.values()],
                'saved_at': datetime.now().isoformat()
            }

        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=2)

    def load_history(self) -> None:
        """Load operation history from file."""
        if not self.history_file or not Path(self.history_file).exists():
            return

        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)

            # Only load completed/failed operations (not active ones)
            for op_data in history_data.get('operations', []):
                status = OperationStatus(op_data['status'])
                if status in (OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.CANCELLED):
                    operation = FileOperation(
                        operation_id=op_data['operation_id'],
                        operation_type=OperationType(op_data['operation_type']),
                        source_paths=op_data['source_paths'],
                        dest_paths=op_data['dest_paths'],
                        status=status,
                        priority=OperationPriority(op_data['priority']),
                        created_at=datetime.fromisoformat(op_data['created_at']),
                        started_at=datetime.fromisoformat(op_data['started_at']) if op_data.get('started_at') else None,
                        completed_at=datetime.fromisoformat(op_data['completed_at']) if op_data.get('completed_at') else None,
                        error=op_data.get('error'),
                        verify=op_data.get('verify', False),
                        preserve_metadata=op_data.get('preserve_metadata', True),
                        conflict_action=ConflictAction(op_data.get('conflict_action', 'ask')),
                        total_size=op_data.get('total_size', 0),
                        processed_size=op_data.get('processed_size', 0),
                        total_files=op_data.get('total_files', 0),
                        processed_files=op_data.get('processed_files', 0),
                        failed_files=op_data.get('failed_files', 0),
                    )
                    with self._lock:
                        self._operations[operation.operation_id] = operation

        except Exception as e:
            print(f"Error loading history: {e}")

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the manager."""
        self._shutdown_event.set()

        if wait:
            # Wait for workers to finish
            for worker in self._workers:
                worker.join(timeout=5.0)

        # Save history
        if self.history_file:
            self.save_history()

        # Cleanup components
        self._copier.shutdown()
        self._mover.cleanup()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()

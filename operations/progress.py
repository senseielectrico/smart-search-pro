"""
Progress tracking system for file operations.
Tracks per-file and overall progress with speed calculation and ETA.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import deque
from threading import Lock


@dataclass
class FileProgress:
    """Progress tracking for a single file."""
    path: str
    size: int
    copied: int = 0
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    speed: float = 0.0  # bytes per second
    error: Optional[str] = None

    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage."""
        return (self.copied / self.size * 100.0) if self.size > 0 else 0.0

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time

    @property
    def eta_seconds(self) -> Optional[float]:
        """Calculate estimated time remaining."""
        if self.speed <= 0 or self.copied >= self.size:
            return None
        remaining_bytes = self.size - self.copied
        return remaining_bytes / self.speed

    def update(self, bytes_copied: int) -> None:
        """Update progress and recalculate speed."""
        self.copied = bytes_copied
        elapsed = self.elapsed_time
        if elapsed > 0:
            self.speed = self.copied / elapsed

    def complete(self, error: Optional[str] = None) -> None:
        """Mark file as complete."""
        self.end_time = time.time()
        self.error = error
        if not error:
            self.copied = self.size


@dataclass
class OperationProgress:
    """Overall progress tracking for a batch operation."""
    operation_id: str
    total_files: int
    total_size: int
    files: Dict[str, FileProgress] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    paused: bool = False
    pause_time: Optional[float] = None
    total_pause_duration: float = 0.0

    # Speed tracking with rolling average
    _speed_samples: deque = field(default_factory=lambda: deque(maxlen=10))
    _last_bytes: int = 0
    _last_update: float = field(default_factory=time.time)

    @property
    def completed_files(self) -> int:
        """Count of completed files."""
        return sum(1 for f in self.files.values() if f.end_time is not None)

    @property
    def failed_files(self) -> int:
        """Count of failed files."""
        return sum(1 for f in self.files.values() if f.error is not None)

    @property
    def copied_size(self) -> int:
        """Total bytes copied so far."""
        return sum(f.copied for f in self.files.values())

    @property
    def progress_percent(self) -> float:
        """Calculate overall progress percentage."""
        return (self.copied_size / self.total_size * 100.0) if self.total_size > 0 else 0.0

    @property
    def current_speed(self) -> float:
        """Get current speed (bytes/sec) using rolling average."""
        if not self._speed_samples:
            return 0.0
        return sum(self._speed_samples) / len(self._speed_samples)

    @property
    def average_speed(self) -> float:
        """Get average speed over entire operation."""
        elapsed = self.elapsed_time
        if elapsed > 0:
            return self.copied_size / elapsed
        return 0.0

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time excluding pauses."""
        end = self.end_time if self.end_time else time.time()
        if self.paused and self.pause_time:
            end = self.pause_time
        return (end - self.start_time) - self.total_pause_duration

    @property
    def eta_seconds(self) -> Optional[float]:
        """Calculate estimated time remaining."""
        speed = self.current_speed if self.current_speed > 0 else self.average_speed
        if speed <= 0:
            return None
        remaining_bytes = self.total_size - self.copied_size
        return remaining_bytes / speed

    def update_speed(self) -> None:
        """Update speed calculation with new sample."""
        now = time.time()
        current_bytes = self.copied_size
        elapsed = now - self._last_update

        if elapsed >= 0.5:  # Update every 0.5 seconds
            bytes_diff = current_bytes - self._last_bytes
            if elapsed > 0:
                speed = bytes_diff / elapsed
                self._speed_samples.append(speed)

            self._last_bytes = current_bytes
            self._last_update = now

    def pause(self) -> None:
        """Pause the operation."""
        if not self.paused:
            self.paused = True
            self.pause_time = time.time()

    def resume(self) -> None:
        """Resume the operation."""
        if self.paused and self.pause_time:
            pause_duration = time.time() - self.pause_time
            self.total_pause_duration += pause_duration
            self.paused = False
            self.pause_time = None
            self._last_update = time.time()  # Reset speed tracking

    def complete(self) -> None:
        """Mark operation as complete."""
        self.end_time = time.time()


class ProgressTracker:
    """
    Thread-safe progress tracking for file operations.
    Manages multiple concurrent operations with speed graphs and ETA.
    """

    def __init__(self):
        self._operations: Dict[str, OperationProgress] = {}
        self._lock = Lock()

    def start_operation(
        self,
        operation_id: str,
        files: List[str],
        sizes: List[int]
    ) -> OperationProgress:
        """Start tracking a new operation."""
        with self._lock:
            progress = OperationProgress(
                operation_id=operation_id,
                total_files=len(files),
                total_size=sum(sizes)
            )

            # Initialize file progress
            for path, size in zip(files, sizes):
                progress.files[path] = FileProgress(path=path, size=size)

            self._operations[operation_id] = progress
            return progress

    def update_file(
        self,
        operation_id: str,
        file_path: str,
        bytes_copied: int
    ) -> None:
        """Update progress for a specific file."""
        with self._lock:
            if operation_id in self._operations:
                progress = self._operations[operation_id]
                if file_path in progress.files:
                    progress.files[file_path].update(bytes_copied)
                    progress.update_speed()

    def complete_file(
        self,
        operation_id: str,
        file_path: str,
        error: Optional[str] = None
    ) -> None:
        """Mark a file as complete."""
        with self._lock:
            if operation_id in self._operations:
                progress = self._operations[operation_id]
                if file_path in progress.files:
                    progress.files[file_path].complete(error)
                    progress.update_speed()

    def get_progress(self, operation_id: str) -> Optional[OperationProgress]:
        """Get current progress for an operation."""
        with self._lock:
            return self._operations.get(operation_id)

    def pause_operation(self, operation_id: str) -> None:
        """Pause an operation."""
        with self._lock:
            if operation_id in self._operations:
                self._operations[operation_id].pause()

    def resume_operation(self, operation_id: str) -> None:
        """Resume a paused operation."""
        with self._lock:
            if operation_id in self._operations:
                self._operations[operation_id].resume()

    def complete_operation(self, operation_id: str) -> None:
        """Mark an operation as complete."""
        with self._lock:
            if operation_id in self._operations:
                self._operations[operation_id].complete()

    def remove_operation(self, operation_id: str) -> None:
        """Remove operation from tracking."""
        with self._lock:
            self._operations.pop(operation_id, None)

    def get_all_operations(self) -> Dict[str, OperationProgress]:
        """Get all tracked operations."""
        with self._lock:
            return dict(self._operations)

    def get_speed_graph_data(
        self,
        operation_id: str,
        max_points: int = 60
    ) -> List[float]:
        """Get speed data points for graphing."""
        with self._lock:
            if operation_id in self._operations:
                progress = self._operations[operation_id]
                return list(progress._speed_samples)[-max_points:]
            return []

    def format_time(self, seconds: Optional[float]) -> str:
        """Format time duration as human-readable string."""
        if seconds is None:
            return "Unknown"

        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"

    def format_speed(self, bytes_per_sec: float) -> str:
        """Format speed as human-readable string."""
        if bytes_per_sec < 1024:
            return f"{bytes_per_sec:.0f} B/s"
        elif bytes_per_sec < 1024 ** 2:
            return f"{bytes_per_sec / 1024:.1f} KB/s"
        elif bytes_per_sec < 1024 ** 3:
            return f"{bytes_per_sec / (1024 ** 2):.1f} MB/s"
        else:
            return f"{bytes_per_sec / (1024 ** 3):.2f} GB/s"

    def format_size(self, size_bytes: int) -> str:
        """Format byte size as human-readable string."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 ** 3:
            return f"{size_bytes / (1024 ** 2):.1f} MB"
        else:
            return f"{size_bytes / (1024 ** 3):.2f} GB"

"""
Threading utilities with auto-detection of optimal worker counts.

Provides centralized thread pool management with automatic CPU detection
and separate configurations for I/O-bound and CPU-bound tasks.
"""

import os
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

logger = logging.getLogger(__name__)


def get_cpu_count() -> int:
    """
    Get the number of CPU cores available.

    Returns:
        Number of CPU cores (minimum 4)
    """
    try:
        count = os.cpu_count() or 4
        return max(4, count)
    except Exception:
        return 4


def get_optimal_io_workers() -> int:
    """
    Get optimal worker count for I/O-bound tasks.

    I/O-bound tasks benefit from more threads since they spend
    most time waiting for I/O operations.

    Returns:
        Optimal worker count for I/O operations
    """
    cpu_count = get_cpu_count()
    # I/O bound: 2x CPU count (up to 32)
    return min(32, max(4, cpu_count * 2))


def get_optimal_cpu_workers() -> int:
    """
    Get optimal worker count for CPU-bound tasks.

    CPU-bound tasks should use fewer threads to avoid context switching
    overhead and leave one core for system operations.

    Returns:
        Optimal worker count for CPU operations
    """
    cpu_count = get_cpu_count()
    # CPU bound: CPU count - 1 (minimum 2, max 16)
    return min(16, max(2, cpu_count - 1))


def get_optimal_mixed_workers() -> int:
    """
    Get optimal worker count for mixed I/O and CPU tasks.

    Returns:
        Optimal worker count for mixed workloads
    """
    cpu_count = get_cpu_count()
    # Mixed: 1.5x CPU count
    return min(24, max(4, int(cpu_count * 1.5)))


class ManagedThreadPoolExecutor(ThreadPoolExecutor):
    """
    ThreadPoolExecutor with automatic worker detection and better defaults.

    Features:
    - Automatic optimal worker detection
    - Workload-specific configurations
    - Proper cleanup and resource management
    """

    def __init__(
        self,
        max_workers: Optional[int] = None,
        workload_type: str = "mixed",
        thread_name_prefix: str = "",
        **kwargs
    ):
        """
        Initialize managed thread pool.

        Args:
            max_workers: Override automatic detection (None = auto)
            workload_type: Type of workload ("io", "cpu", or "mixed")
            thread_name_prefix: Prefix for thread names
            **kwargs: Additional arguments for ThreadPoolExecutor
        """
        if max_workers is None:
            if workload_type == "io":
                max_workers = get_optimal_io_workers()
            elif workload_type == "cpu":
                max_workers = get_optimal_cpu_workers()
            else:  # mixed
                max_workers = get_optimal_mixed_workers()

        self.workload_type = workload_type

        super().__init__(
            max_workers=max_workers,
            thread_name_prefix=thread_name_prefix or f"{workload_type.upper()}Worker",
            **kwargs
        )

        logger.debug(
            f"Created thread pool: {max_workers} workers for {workload_type} workload"
        )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with proper cleanup."""
        self.shutdown(wait=True)
        return False


# Convenience functions for common patterns

def create_io_executor(
    max_workers: Optional[int] = None,
    thread_name_prefix: str = "IO"
) -> ManagedThreadPoolExecutor:
    """
    Create executor optimized for I/O-bound tasks.

    Args:
        max_workers: Override automatic detection
        thread_name_prefix: Prefix for thread names

    Returns:
        Configured ThreadPoolExecutor
    """
    return ManagedThreadPoolExecutor(
        max_workers=max_workers,
        workload_type="io",
        thread_name_prefix=thread_name_prefix
    )


def create_cpu_executor(
    max_workers: Optional[int] = None,
    thread_name_prefix: str = "CPU"
) -> ManagedThreadPoolExecutor:
    """
    Create executor optimized for CPU-bound tasks.

    Args:
        max_workers: Override automatic detection
        thread_name_prefix: Prefix for thread names

    Returns:
        Configured ThreadPoolExecutor
    """
    return ManagedThreadPoolExecutor(
        max_workers=max_workers,
        workload_type="cpu",
        thread_name_prefix=thread_name_prefix
    )


def create_mixed_executor(
    max_workers: Optional[int] = None,
    thread_name_prefix: str = "Mixed"
) -> ManagedThreadPoolExecutor:
    """
    Create executor for mixed I/O and CPU workloads.

    Args:
        max_workers: Override automatic detection
        thread_name_prefix: Prefix for thread names

    Returns:
        Configured ThreadPoolExecutor
    """
    return ManagedThreadPoolExecutor(
        max_workers=max_workers,
        workload_type="mixed",
        thread_name_prefix=thread_name_prefix
    )


# Log system information on import
_cpu_count = get_cpu_count()
_io_workers = get_optimal_io_workers()
_cpu_workers = get_optimal_cpu_workers()
_mixed_workers = get_optimal_mixed_workers()

logger.info(
    f"Threading initialized: {_cpu_count} CPUs detected | "
    f"I/O workers: {_io_workers} | CPU workers: {_cpu_workers} | "
    f"Mixed workers: {_mixed_workers}"
)

"""
Performance monitoring and optimization utilities.

Provides:
- Startup time tracking
- Search latency monitoring
- Memory usage tracking
- Performance metrics reporting
- Lazy import management
"""

import time
import logging
import weakref
import psutil
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Single performance measurement"""
    name: str
    duration_ms: float
    timestamp: datetime
    memory_delta_mb: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceReport:
    """Complete performance report"""
    startup_time_ms: float
    average_search_latency_ms: float
    memory_usage_mb: float
    peak_memory_mb: float
    metrics: List[PerformanceMetric] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'startup_time_ms': self.startup_time_ms,
            'average_search_latency_ms': self.average_search_latency_ms,
            'memory_usage_mb': self.memory_usage_mb,
            'peak_memory_mb': self.peak_memory_mb,
            'metrics_count': len(self.metrics),
            'timestamp': datetime.now().isoformat()
        }


class PerformanceMonitor:
    """
    Global performance monitor for tracking application metrics.

    Features:
    - Startup time tracking
    - Operation timing
    - Memory monitoring
    - Weak references for cache cleanup
    - Metric aggregation and reporting
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.metrics: List[PerformanceMetric] = []
        self.startup_time: Optional[float] = None
        self.startup_start: Optional[float] = None
        self._process = psutil.Process()
        self._initial_memory = self._get_memory_mb()
        self._peak_memory = self._initial_memory

        # Weak reference caches for automatic cleanup
        self._weak_caches: List[weakref.ref] = []

        logger.info(f"Performance monitor initialized. Initial memory: {self._initial_memory:.2f} MB")

    def _get_memory_mb(self) -> float:
        """Get current memory usage in MB"""
        try:
            return self._process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0

    def start_startup_tracking(self):
        """Begin tracking application startup time"""
        self.startup_start = time.perf_counter()
        logger.debug("Startup tracking started")

    def end_startup_tracking(self):
        """End startup tracking and record time"""
        if self.startup_start:
            self.startup_time = (time.perf_counter() - self.startup_start) * 1000
            logger.info(f"Startup completed in {self.startup_time:.2f}ms")

            # Record as metric
            self.record_metric(
                "startup",
                self.startup_time,
                metadata={'phase': 'complete'}
            )

    @contextmanager
    def track_operation(self, operation_name: str, metadata: Optional[Dict] = None):
        """
        Context manager for tracking operation performance.

        Usage:
            with monitor.track_operation("search"):
                perform_search()
        """
        start_time = time.perf_counter()
        start_memory = self._get_memory_mb()

        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            memory_delta = self._get_memory_mb() - start_memory

            self.record_metric(
                operation_name,
                duration_ms,
                memory_delta_mb=memory_delta,
                metadata=metadata or {}
            )

    def record_metric(
        self,
        name: str,
        duration_ms: float,
        memory_delta_mb: float = 0.0,
        metadata: Optional[Dict] = None
    ):
        """Record a performance metric"""
        current_memory = self._get_memory_mb()
        self._peak_memory = max(self._peak_memory, current_memory)

        metric = PerformanceMetric(
            name=name,
            duration_ms=duration_ms,
            timestamp=datetime.now(),
            memory_delta_mb=memory_delta_mb,
            metadata=metadata or {}
        )

        self.metrics.append(metric)

        # Log slow operations
        if duration_ms > 100:
            logger.warning(f"Slow operation: {name} took {duration_ms:.2f}ms")

    def register_cache(self, cache_obj: Any):
        """Register a cache object for automatic cleanup using weak references"""
        self._weak_caches.append(weakref.ref(cache_obj))

    def cleanup_dead_caches(self):
        """Remove dead weak references"""
        self._weak_caches = [ref for ref in self._weak_caches if ref() is not None]

    def get_search_metrics(self) -> Dict[str, float]:
        """Get search-specific metrics"""
        search_metrics = [m for m in self.metrics if m.name == "search"]

        if not search_metrics:
            return {
                'count': 0,
                'average_ms': 0.0,
                'min_ms': 0.0,
                'max_ms': 0.0
            }

        durations = [m.duration_ms for m in search_metrics]
        return {
            'count': len(durations),
            'average_ms': sum(durations) / len(durations),
            'min_ms': min(durations),
            'max_ms': max(durations),
            'p95_ms': sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 20 else max(durations)
        }

    def generate_report(self) -> PerformanceReport:
        """Generate comprehensive performance report"""
        search_metrics = self.get_search_metrics()
        current_memory = self._get_memory_mb()

        report = PerformanceReport(
            startup_time_ms=self.startup_time or 0.0,
            average_search_latency_ms=search_metrics.get('average_ms', 0.0),
            memory_usage_mb=current_memory,
            peak_memory_mb=self._peak_memory,
            metrics=self.metrics
        )

        return report

    def export_report(self, output_path: Path):
        """Export performance report to JSON"""
        report = self.generate_report()

        # Create detailed report
        detailed_report = report.to_dict()
        detailed_report['search_metrics'] = self.get_search_metrics()
        detailed_report['top_slow_operations'] = [
            {
                'name': m.name,
                'duration_ms': m.duration_ms,
                'timestamp': m.timestamp.isoformat()
            }
            for m in sorted(self.metrics, key=lambda x: x.duration_ms, reverse=True)[:10]
        ]

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(detailed_report, f, indent=2)

        logger.info(f"Performance report exported to {output_path}")

    def log_summary(self):
        """Log performance summary"""
        report = self.generate_report()
        search_metrics = self.get_search_metrics()

        logger.info("=" * 60)
        logger.info("PERFORMANCE SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Startup Time: {report.startup_time_ms:.2f}ms")
        logger.info(f"Search Count: {search_metrics.get('count', 0)}")
        logger.info(f"Avg Search Latency: {report.average_search_latency_ms:.2f}ms")
        logger.info(f"Current Memory: {report.memory_usage_mb:.2f}MB")
        logger.info(f"Peak Memory: {report.peak_memory_mb:.2f}MB")
        logger.info(f"Total Metrics: {len(self.metrics)}")
        logger.info("=" * 60)


class LazyImporter:
    """
    Lazy import manager to defer heavy imports until needed.

    Reduces startup time by only importing modules when first used.
    """

    def __init__(self):
        self._imports: Dict[str, Any] = {}
        self._import_times: Dict[str, float] = {}
        self.monitor = PerformanceMonitor()

    def register(self, name: str, import_func: Callable[[], Any]):
        """
        Register a lazy import.

        Args:
            name: Import identifier
            import_func: Function that performs the import
        """
        self._imports[name] = import_func

    def get(self, name: str) -> Any:
        """
        Get imported module, importing if necessary.

        Args:
            name: Import identifier

        Returns:
            Imported module/object
        """
        # If already imported, return cached
        if name in self._import_times:
            return self._imports[name]

        # Import and track time
        import_func = self._imports.get(name)
        if not import_func:
            raise KeyError(f"Lazy import '{name}' not registered")

        with self.monitor.track_operation(f"lazy_import_{name}"):
            result = import_func()
            self._imports[name] = result
            self._import_times[name] = time.time()

        logger.debug(f"Lazy imported: {name}")
        return result

    def is_imported(self, name: str) -> bool:
        """Check if module has been imported"""
        return name in self._import_times


# Global singleton instances
_performance_monitor = PerformanceMonitor()
_lazy_importer = LazyImporter()


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance"""
    return _performance_monitor


def get_lazy_importer() -> LazyImporter:
    """Get global lazy importer instance"""
    return _lazy_importer


# Decorator for tracking function performance
def track_performance(operation_name: Optional[str] = None):
    """
    Decorator to track function performance.

    Usage:
        @track_performance("my_operation")
        def my_function():
            pass
    """
    def decorator(func):
        nonlocal operation_name
        if operation_name is None:
            operation_name = func.__name__

        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            with monitor.track_operation(operation_name):
                return func(*args, **kwargs)

        return wrapper
    return decorator

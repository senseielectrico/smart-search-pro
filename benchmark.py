"""
Smart Search Performance Benchmark Suite
========================================

Ejecuta benchmarks completos de todas las optimizaciones y genera un reporte.

Uso:
    python benchmark.py

Output:
    - Reporte en consola
    - Archivo benchmark_results.json con métricas detalladas
"""

import time
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any
import random
import string

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from optimizations import (
    ResultsCache, LazyDirectoryLoader, SearchIndexer,
    WorkerPool, MemoryManager, QueryOptimizer
)


class BenchmarkSuite:
    """Suite completo de benchmarks"""

    def __init__(self):
        self.results: Dict[str, Any] = {
            'timestamp': datetime.now().isoformat(),
            'benchmarks': {}
        }

    def run_all(self):
        """Ejecuta todos los benchmarks"""
        print("=" * 70)
        print("SMART SEARCH PERFORMANCE BENCHMARK SUITE")
        print("=" * 70)
        print()

        self.benchmark_cache()
        self.benchmark_indexer()
        self.benchmark_worker_pool()
        self.benchmark_memory_manager()
        self.benchmark_query_optimizer()

        # Save results
        self.save_results()

        # Print summary
        self.print_summary()

    def benchmark_cache(self):
        """Benchmark del sistema de cache"""
        print("1. RESULTS CACHE BENCHMARK")
        print("-" * 70)

        cache = ResultsCache(max_size=1000, max_memory_mb=50, ttl_seconds=300)

        # Generate test queries
        num_queries = 100
        queries = []
        for i in range(num_queries):
            query = {
                'query': f'test{i % 20}',  # 20 unique queries, repeated 5x
                'path': f'C:\\Users\\Documents',
                'search_content': i % 2 == 0
            }
            queries.append(query)

        # Test 1: Cache misses (first access)
        start = time.time()
        miss_count = 0
        for query in queries:
            key = ResultsCache.generate_key(query)
            result = cache.get(key)
            if result is None:
                miss_count += 1
                # Simulate search result
                fake_result = [f'file{j}.txt' for j in range(10)]
                cache.put(key, fake_result)
        miss_time = (time.time() - start) * 1000  # ms

        # Test 2: Cache hits (second access)
        start = time.time()
        hit_count = 0
        for query in queries:
            key = ResultsCache.generate_key(query)
            result = cache.get(key)
            if result is not None:
                hit_count += 1
        hit_time = (time.time() - start) * 1000  # ms

        # Calculate metrics
        stats = cache.get_stats()
        speedup = miss_time / hit_time if hit_time > 0 else 0

        results = {
            'queries_tested': num_queries,
            'unique_queries': 20,
            'miss_time_ms': round(miss_time, 2),
            'hit_time_ms': round(hit_time, 2),
            'speedup': round(speedup, 2),
            'hit_rate': round(stats['hit_rate'], 2),
            'cache_size': stats['size'],
            'memory_used_mb': round(stats['memory_used_mb'], 4)
        }

        self.results['benchmarks']['cache'] = results

        print(f"  Queries tested:        {results['queries_tested']}")
        print(f"  Unique queries:        {results['unique_queries']}")
        print(f"  First pass (misses):   {results['miss_time_ms']:.2f}ms")
        print(f"  Second pass (hits):    {results['hit_time_ms']:.2f}ms")
        print(f"  Speedup:               {results['speedup']:.2f}x")
        print(f"  Hit rate:              {results['hit_rate']:.1f}%")
        print(f"  Memory used:           {results['memory_used_mb']:.4f}MB")
        print()

    def benchmark_indexer(self):
        """Benchmark del indexador de búsqueda"""
        print("2. SEARCH INDEXER BENCHMARK")
        print("-" * 70)

        indexer = SearchIndexer()

        # Test 1: Indexing performance
        num_docs = 1000
        start = time.time()
        for i in range(num_docs):
            doc = {
                'name': f'file{i}.txt',
                'path': f'C:\\Users\\Documents\\file{i}.txt',
                'content': f'content {i % 100} test data example document'
            }
            indexer.add_document(doc)
        index_time = (time.time() - start) * 1000

        # Test 2: Search performance (single word)
        start = time.time()
        results_single = indexer.search('test')
        search_single_time = (time.time() - start) * 1000

        # Test 3: Search performance (multiple words)
        start = time.time()
        results_multi = indexer.search('test data example')
        search_multi_time = (time.time() - start) * 1000

        results = {
            'documents_indexed': num_docs,
            'index_time_ms': round(index_time, 2),
            'index_rate_docs_per_sec': round(num_docs / (index_time / 1000), 2),
            'search_single_word_ms': round(search_single_time, 4),
            'search_single_results': len(results_single),
            'search_multi_word_ms': round(search_multi_time, 4),
            'search_multi_results': len(results_multi)
        }

        self.results['benchmarks']['indexer'] = results

        print(f"  Documents indexed:        {results['documents_indexed']}")
        print(f"  Indexing time:            {results['index_time_ms']:.2f}ms")
        print(f"  Indexing rate:            {results['index_rate_docs_per_sec']:.0f} docs/sec")
        print(f"  Search (1 word):          {results['search_single_word_ms']:.4f}ms ({results['search_single_results']} results)")
        print(f"  Search (3 words):         {results['search_multi_word_ms']:.4f}ms ({results['search_multi_results']} results)")
        print()

    def benchmark_worker_pool(self):
        """Benchmark del pool de workers"""
        print("3. WORKER POOL BENCHMARK")
        print("-" * 70)

        def cpu_task(n):
            """Simulate CPU-intensive task"""
            total = 0
            for i in range(n):
                total += i ** 2
            return total

        num_tasks = 100
        task_size = 10000

        # Test 1: Sequential execution
        start = time.time()
        sequential_results = []
        for i in range(num_tasks):
            result = cpu_task(task_size)
            sequential_results.append(result)
        sequential_time = (time.time() - start) * 1000

        # Test 2: Parallel execution (2 workers)
        pool2 = WorkerPool(num_workers=2)
        start = time.time()
        tasks2 = []
        for i in range(num_tasks):
            task = pool2.submit(cpu_task, task_size)
            tasks2.append(task)
        for task in tasks2:
            task.completed.wait()
        parallel2_time = (time.time() - start) * 1000
        pool2.shutdown()

        # Test 3: Parallel execution (4 workers)
        pool4 = WorkerPool(num_workers=4)
        start = time.time()
        tasks4 = []
        for i in range(num_tasks):
            task = pool4.submit(cpu_task, task_size)
            tasks4.append(task)
        for task in tasks4:
            task.completed.wait()
        parallel4_time = (time.time() - start) * 1000
        pool4.shutdown()

        # Test 4: Parallel execution (8 workers)
        pool8 = WorkerPool(num_workers=8)
        start = time.time()
        tasks8 = []
        for i in range(num_tasks):
            task = pool8.submit(cpu_task, task_size)
            tasks8.append(task)
        for task in tasks8:
            task.completed.wait()
        parallel8_time = (time.time() - start) * 1000
        pool8.shutdown()

        results = {
            'tasks': num_tasks,
            'sequential_time_ms': round(sequential_time, 2),
            'parallel_2_workers_ms': round(parallel2_time, 2),
            'parallel_4_workers_ms': round(parallel4_time, 2),
            'parallel_8_workers_ms': round(parallel8_time, 2),
            'speedup_2_workers': round(sequential_time / parallel2_time, 2),
            'speedup_4_workers': round(sequential_time / parallel4_time, 2),
            'speedup_8_workers': round(sequential_time / parallel8_time, 2),
        }

        self.results['benchmarks']['worker_pool'] = results

        print(f"  Tasks executed:          {results['tasks']}")
        print(f"  Sequential:              {results['sequential_time_ms']:.2f}ms")
        print(f"  Parallel (2 workers):    {results['parallel_2_workers_ms']:.2f}ms (speedup: {results['speedup_2_workers']:.2f}x)")
        print(f"  Parallel (4 workers):    {results['parallel_4_workers_ms']:.2f}ms (speedup: {results['speedup_4_workers']:.2f}x)")
        print(f"  Parallel (8 workers):    {results['parallel_8_workers_ms']:.2f}ms (speedup: {results['speedup_8_workers']:.2f}x)")
        print()

    def benchmark_memory_manager(self):
        """Benchmark del gestor de memoria"""
        print("4. MEMORY MANAGER BENCHMARK")
        print("-" * 70)

        mem_manager = MemoryManager(threshold_mb=100)

        # Get initial memory
        initial_memory = mem_manager.get_memory_usage()

        # Create some data structures
        cleanup_count = [0]
        def test_cleanup():
            cleanup_count[0] += 1

        mem_manager.register_cleanup(test_cleanup)

        # Simulate memory growth
        large_data = []
        for i in range(100):
            large_data.append([random.random() for _ in range(1000)])

        current_memory = mem_manager.get_memory_usage()

        # Test cleanup
        start = time.time()
        mem_manager.cleanup()
        cleanup_time = (time.time() - start) * 1000

        after_cleanup_memory = mem_manager.get_memory_usage()

        results = {
            'initial_memory_mb': round(initial_memory / 1024 / 1024, 2),
            'after_allocation_mb': round(current_memory / 1024 / 1024, 2),
            'after_cleanup_mb': round(after_cleanup_memory / 1024 / 1024, 2),
            'cleanup_time_ms': round(cleanup_time, 2),
            'cleanup_callbacks_executed': cleanup_count[0]
        }

        self.results['benchmarks']['memory_manager'] = results

        print(f"  Initial memory:          {results['initial_memory_mb']:.2f}MB")
        print(f"  After allocation:        {results['after_allocation_mb']:.2f}MB")
        print(f"  After cleanup:           {results['after_cleanup_mb']:.2f}MB")
        print(f"  Cleanup time:            {results['cleanup_time_ms']:.2f}ms")
        print(f"  Callbacks executed:      {results['cleanup_callbacks_executed']}")
        print()

    def benchmark_query_optimizer(self):
        """Benchmark del optimizador de queries"""
        print("5. QUERY OPTIMIZER BENCHMARK")
        print("-" * 70)

        optimizer = QueryOptimizer()

        # Test queries
        test_queries = [
            """
            SELECT System.ItemPathDisplay, System.FileName
            FROM SystemIndex
            WHERE System.FileName LIKE '%test%'
            """,
            """
            SELECT System.ItemPathDisplay, System.Size
            FROM SystemIndex
            WHERE System.Size > 1024
            """,
            """
            SELECT System.ItemPathDisplay
            FROM SystemIndex
            WHERE System.FileExtension = '.txt'
            """
        ]

        # Test 1: First optimization (not cached)
        start = time.time()
        for query in test_queries:
            optimized = optimizer.optimize_query(query)
        first_time = (time.time() - start) * 1000

        # Test 2: Second optimization (cached)
        start = time.time()
        for query in test_queries:
            optimized = optimizer.optimize_query(query)
        cached_time = (time.time() - start) * 1000

        # Test 3: Large batch
        num_queries = 1000
        start = time.time()
        for i in range(num_queries):
            query = f"SELECT * FROM SystemIndex WHERE System.FileName LIKE '%file{i}%'"
            optimized = optimizer.optimize_query(query)
        batch_time = (time.time() - start) * 1000

        results = {
            'test_queries': len(test_queries),
            'first_optimization_ms': round(first_time, 4),
            'cached_optimization_ms': round(cached_time, 4),
            'speedup': round(first_time / cached_time, 2) if cached_time > 0 else 0,
            'batch_queries': num_queries,
            'batch_time_ms': round(batch_time, 2),
            'batch_rate_queries_per_sec': round(num_queries / (batch_time / 1000), 2)
        }

        self.results['benchmarks']['query_optimizer'] = results

        print(f"  Test queries:            {results['test_queries']}")
        print(f"  First optimization:      {results['first_optimization_ms']:.4f}ms")
        print(f"  Cached optimization:     {results['cached_optimization_ms']:.4f}ms")
        print(f"  Speedup:                 {results['speedup']:.2f}x")
        print(f"  Batch ({results['batch_queries']} queries):  {results['batch_time_ms']:.2f}ms")
        print(f"  Rate:                    {results['batch_rate_queries_per_sec']:.0f} queries/sec")
        print()

    def save_results(self):
        """Guarda los resultados en un archivo JSON"""
        output_file = os.path.join(os.path.dirname(__file__), 'benchmark_results.json')

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"Results saved to: {output_file}")
        print()

    def print_summary(self):
        """Imprime un resumen de los resultados"""
        print("=" * 70)
        print("BENCHMARK SUMMARY")
        print("=" * 70)
        print()

        benchmarks = self.results['benchmarks']

        print("KEY METRICS:")
        print(f"  Cache Hit Rate:          {benchmarks['cache']['hit_rate']:.1f}%")
        print(f"  Cache Speedup:           {benchmarks['cache']['speedup']:.2f}x")
        print(f"  Indexing Rate:           {benchmarks['indexer']['index_rate_docs_per_sec']:.0f} docs/sec")
        print(f"  Search Speed (1 word):   {benchmarks['indexer']['search_single_word_ms']:.4f}ms")
        print(f"  Worker Pool Speedup:     {benchmarks['worker_pool']['speedup_4_workers']:.2f}x (4 workers)")
        print(f"  Query Optimization:      {benchmarks['query_optimizer']['speedup']:.2f}x speedup")
        print()

        print("RECOMMENDATIONS:")

        # Cache recommendations
        cache_hit_rate = benchmarks['cache']['hit_rate']
        if cache_hit_rate > 70:
            print("  [OK] Cache performance is excellent")
        elif cache_hit_rate > 40:
            print("  [WARN] Cache performance is good, consider increasing cache size")
        else:
            print("  [FAIL] Cache performance is low, review query patterns and TTL")

        # Worker pool recommendations
        speedup = benchmarks['worker_pool']['speedup_4_workers']
        if speedup > 3.5:
            print("  [OK] Worker pool showing excellent parallelization")
        elif speedup > 2.5:
            print("  [WARN] Worker pool showing good parallelization")
        else:
            print("  [FAIL] Worker pool underperforming, check task granularity")

        # Indexer recommendations
        index_rate = benchmarks['indexer']['index_rate_docs_per_sec']
        if index_rate > 5000:
            print("  [OK] Indexing performance is excellent")
        elif index_rate > 2000:
            print("  [WARN] Indexing performance is acceptable")
        else:
            print("  [FAIL] Indexing performance is low, consider optimization")

        print()
        print("=" * 70)


def main():
    """Función principal"""
    suite = BenchmarkSuite()
    suite.run_all()


if __name__ == '__main__':
    main()

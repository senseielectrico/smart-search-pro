# SMART SEARCH PRO v3.0 - PERFORMANCE OPTIMIZATION IMPLEMENTATION CHECKLIST

## PHASE 1: CRITICAL OPTIMIZATIONS (P0) - 18 Hours

### Task 1: Async Virtual Scrolling [6 hours]

**Description:** Replace synchronous `fetchMore()` with async background loading

**Files to Modify:**
- `ui/results_panel.py` - VirtualTableModel, DraggableTableView

**Subtasks:**

- [ ] **1.1** Create `AsyncRowLoader` class
  - Location: `ui/async_loader.py` (new file)
  - Implements: `load_rows_async()`, `cancel_pending()`, `shutdown()`
  - Reference: `PERFORMANCE_OPTIMIZATIONS.py` lines 68-110

- [ ] **1.2** Create `QRunnable` task class for row loading
  - Name: `RowLoaderTask`
  - Handles: Background row loading without blocking UI
  - Integration: Called from `fetchMore()` via `QThreadPool`

- [ ] **1.3** Modify `VirtualTableModel.fetchMore()`
  - Change from: Synchronous `beginInsertRows()` → `endInsertRows()`
  - Change to: Async `QThreadPool.globalInstance().start(RowLoaderTask)`
  - Add: `_fetch_in_progress` flag to prevent concurrent fetches

- [ ] **1.4** Update results panel to handle async loading
  - Add visual feedback (spinner) during load
  - Add method: `_on_async_load_complete()`
  - Emit signal when rows loaded

- [ ] **1.5** Test async loading
  - Test with 1M results
  - Verify no UI lag during scroll
  - Verify proper memory cleanup

**Acceptance Criteria:**
- Scroll latency <50ms (was 500ms)
- UI responsive during large loads
- No UI freezing observed
- Memory released after scroll stops

---

### Task 2: Bounded Virtual Model with Memory Spilling [6 hours]

**Description:** Limit in-memory results to MAX_IN_MEMORY, spill to SQLite

**Files to Modify/Create:**
- `ui/results_panel.py` - Replace VirtualTableModel
- `core/bounded_model.py` (new file)

**Subtasks:**

- [ ] **2.1** Create `ResultsOverflowDatabase` class
  - Location: `core/bounded_model.py`
  - Schema: `results` table with row_id, data (JSON), stored_at
  - Methods: `write_batch()`, `read_item()`, `cleanup_old()`
  - Reference: `PERFORMANCE_OPTIMIZATIONS.py` lines 219-280

- [ ] **2.2** Create `BoundedVirtualModel` class
  - Replaces: Current `_all_data` list in VirtualTableModel
  - Properties:
    - MAX_IN_MEMORY = 50000
    - Transparent read from memory/disk
  - Methods:
    - `add_results()`
    - `get_row()`
    - `get_range()`
    - `memory_usage_mb` property
  - Reference: `PERFORMANCE_OPTIMIZATIONS.py` lines 282-377

- [ ] **2.3** Integrate BoundedVirtualModel into ResultsPanel
  - Replace: `self._all_data: List[Dict]`
  - With: `self.model = BoundedVirtualModel()`
  - Update all data access patterns

- [ ] **2.4** Implement lazy loading for disk-based results
  - When `get_row()` retrieves from disk, load asynchronously
  - Don't block UI during disk reads

- [ ] **2.5** Add automatic cleanup
  - Remove results older than 7 days from overflow DB
  - Schedule: Run on app shutdown or periodic (1 hour)

- [ ] **2.6** Monitor and test memory usage
  - Run test with 1M results
  - Verify memory <300MB (was 800MB)
  - Test switching between multiple 50K-result searches

**Acceptance Criteria:**
- Memory usage <300MB for 1M results (was 500-800MB)
- Transparent access (code doesn't know about disk/memory split)
- Zero performance penalty for in-memory results
- <100ms latency to retrieve disk-based results

---

### Task 3: Predictive Scroll Cache Loading [4 hours]

**Description:** Predict scroll direction/velocity and preload rows ahead

**Files to Modify/Create:**
- `ui/results_panel.py` - VirtualTableModel
- `ui/scroll_predictor.py` (new file)

**Subtasks:**

- [ ] **3.1** Create `ScrollDirection` enum
  - Values: UP, DOWN, UNKNOWN
  - Location: `ui/scroll_predictor.py`

- [ ] **3.2** Create `ScrollVelocity` class
  - Tracks: rows_per_ms, direction, last_update
  - Methods: `update()`, properties: `is_fast_scroll`, `is_stale`
  - Reference: `PERFORMANCE_OPTIMIZATIONS.py` lines 25-54

- [ ] **3.3** Modify `VirtualTableModel` to track scroll
  - Add: `_scroll_velocity` tracking
  - Override: Scroll event handling to call `_track_scroll()`
  - Method: `_smart_prune()` - intelligent cache pruning
  - Reference: `PERFORMANCE_OPTIMIZATIONS.py` lines 190-216

- [ ] **3.4** Implement `_smart_prune()` logic
  - If scrolling DOWN: keep more rows below cursor
  - If scrolling UP: keep more rows above cursor
  - Adaptive cache size: 1.5x if fast scroll, 1x if slow
  - Example:
    ```python
    if direction == DOWN:
        min_row = current - cache_size // 4
        max_row = current + cache_size * 3 // 4
    else:
        min_row = current - cache_size * 3 // 4
        max_row = current + cache_size // 4
    ```

- [ ] **3.5** Implement predictive loading
  - Method: `_predictive_load(current_row)`
  - Lookahead: 100ms ahead based on velocity
  - Pre-load rows user will see next
  - Use AsyncRowLoader for background loading

- [ ] **3.6** Test predictive loading
  - Test fast scroll (>5 rows/ms)
  - Test slow scroll (<1 row/ms)
  - Verify: 50% reduction in cache misses
  - Verify: Smooth scrolling without jerks

**Acceptance Criteria:**
- Cache miss rate <30% (was 40-45%)
- Smooth scrolling at any speed
- Fast scroll detection working
- Lookahead correctly predicts next visible rows

---

### Task 4: Async Cache Eviction [2 hours]

**Description:** Non-blocking LRU eviction for hash cache

**Files to Modify:**
- `duplicates/cache.py` - HashCache class

**Subtasks:**

- [ ] **4.1** Create `AsyncCacheEviction` helper class
  - Location: `duplicates/cache.py` or separate module
  - Methods: `start_async_eviction()`, properties: `is_in_progress`
  - Reference: `PERFORMANCE_OPTIMIZATIONS.py` lines 392-439

- [ ] **4.2** Modify `HashCache._check_and_evict()`
  - Change from: Calling `_evict_lru()` synchronously
  - Change to: Calling `start_async_eviction()` in background
  - Keep: Thread-safe with `_eviction_in_progress` flag

- [ ] **4.3** Implement background eviction worker
  - Small sleep (50ms) to avoid thundering herd
  - Use separate DB connection (no lock conflicts)
  - Delete in batches (1000 at a time)
  - Yield to other threads between batches

- [ ] **4.4** Test async eviction
  - Monitor: Lock hold time
  - Verify: Main thread not blocked
  - Measure: Eviction latency (should be invisible)

**Acceptance Criteria:**
- Cache operations not blocked during eviction
- Eviction latency <10ms (was 5-10ms with blocking)
- No visible slowdown when cache full

---

## PHASE 2: IMPORTANT OPTIMIZATIONS (P1) - 12 Hours

### Task 5: Comprehensive Performance Metrics [3 hours]

**Files to Create/Modify:**
- `core/performance_metrics.py` (new file)
- `core/performance.py` - Enhance existing

**Subtasks:**

- [ ] **5.1** Create `PerformanceSnapshot` dataclass
  - Fields: timestamp, query, timing breakdown, result count, memory, cache stats
  - Computed properties: cache_hit_rate, p95_gc_pause_ms
  - Reference: `PERFORMANCE_OPTIMIZATIONS.py` lines 445-479

- [ ] **5.2** Create `PerformanceMetricsCollector` class
  - Singleton pattern (like current PerformanceMonitor)
  - Methods: `record_search()`, `get_statistics()`, `export_csv()`
  - Keep last 1000 snapshots (bounded deque)
  - Reference: `PERFORMANCE_OPTIMIZATIONS.py` lines 481-569

- [ ] **5.3** Integration points
  - Call `record_search()` after each search completion
  - Parameters: query, timings, result count, cache stats, memory
  - Create helper: Capture memory before/after search

- [ ] **5.4** Statistics calculation
  - Implement: percentiles (p50, p95, p99)
  - Metrics: search time, cache hit rate, memory delta, GC pauses
  - Export: CSV format for analysis in Excel/Grafana

- [ ] **5.5** Dashboard/visualization (optional)
  - Simple text-based output
  - Or: Integration with monitoring tools

**Acceptance Criteria:**
- Metrics collected for every search
- P95/P99 latencies calculated correctly
- CSV export working
- <5% overhead from metric collection

---

### Task 6: Cache stat() Optimization [2 hours]

**Files to Modify:**
- `duplicates/cache.py` - HashCache.get_hash()

**Subtasks:**

- [ ] **6.1** Create file stat cache
  - Class: `FileStatCache` with TTL
  - TTL: 60 seconds
  - Store: (stat.st_size, stat.st_mtime)

- [ ] **6.2** Modify `get_hash()` to use cached stats
  - Before: `stat = path.stat()` for every call (I/O)
  - After: Check FileStatCache first
  - Only call real stat() if cache miss or expired

- [ ] **6.3** Invalidate cache on write operations
  - When: `set_hash()` called
  - When: `invalidate()` called

- [ ] **6.4** Test stat caching
  - Measure: stat() call frequency reduction
  - Target: 80% reduction in stat() calls

**Acceptance Criteria:**
- stat() latency reduced 80% (1-2ms → 0.2-0.4ms)
- Cache coherency maintained
- No stale data served

---

### Task 7: Query Pushdown Filtering [4 hours]

**Files to Modify:**
- `search/engine.py` - SearchEngine class
- `search/everything_sdk.py` - EverythingSDK.search()

**Subtasks:**

- [ ] **7.1** Analyze current filtering
  - Current: Fetch all results, then apply filters in Python
  - Problem: Unnecessary data transfer

- [ ] **7.2** Extend EverythingSDK to support filters
  - Size filter: Pass to Everything API if available
  - Date filter: Pass to Everything API if available
  - Type filter: Pass via Everything query syntax

- [ ] **7.3** Modify SearchEngine.search()
  - Build Everything query string including filters
  - Example: `"*.txt" AND size:>1MB AND modified:>2024-01-01`
  - Reduce Python-side filtering

- [ ] **7.4** Fallback for unsupported filters
  - Content filter: Still done in Python
  - Custom filters: Still done in Python

- [ ] **7.5** Test pushdown filtering
  - Measure: Reduction in data transferred
  - Target: 30-50% fewer results to filter in Python
  - Verify: Same final results

**Acceptance Criteria:**
- Search throughput improved 30-50%
- Query complexity not increased
- Fallback working correctly for all filter types

---

### Task 8: GC Tuning and Monitoring [3 hours]

**Files to Create/Modify:**
- `core/gc_monitor.py` (new file)
- `core/performance.py` - Integration

**Subtasks:**

- [ ] **8.1** Create GC pause monitor
  - Track: pause times and frequency
  - Threshold: Alert if P95 > 10ms
  - Reference: Hook into gc module callbacks

- [ ] **8.2** Python GC tuning
  - Adjust: gc.set_threshold() for generation 0
  - Goal: Reduce pause times without increasing CPU

- [ ] **8.3** Memory pool allocation
  - For large searches: Pre-allocate result lists
  - Reduce: GC pressure during result accumulation

- [ ] **8.4** Test GC impact
  - Measure: Pause time before/after tuning
  - Target: P95 GC pause <5ms

**Acceptance Criteria:**
- GC pause tracking working
- P95 pause <5ms (was 10-50ms variable)
- No increase in CPU usage

---

## PHASE 3: OPTIMIZATIONS (P2) - Nice-to-have

### Task 9: Incremental Result Streaming [4 hours]

**Concept:** Display first 1K results immediately, then 10K, 100K, 1M...

**Subtasks:**

- [ ] **9.1** Modify SearchEngine to yield results in batches
- [ ] **9.2** Update UI to show "Loading X results..." with progress
- [ ] **9.3** Test UX perception of "faster" response

---

### Task 10: Result Compression [3 hours]

**Concept:** Compress overflow results with zstd before writing to SQLite

**Subtasks:**

- [ ] **10.1** Add compression to ResultsOverflowDatabase
- [ ] **10.2** Measure size reduction
- [ ] **10.3** Verify decompression performance

---

## TESTING & VALIDATION

### Unit Tests

- [ ] **test_async_loader.py** - AsyncRowLoader functionality
- [ ] **test_bounded_model.py** - Memory spilling, transparency
- [ ] **test_scroll_predictor.py** - Velocity calculation, prediction
- [ ] **test_metrics_collector.py** - Percentile calculation
- [ ] **test_cache_eviction.py** - Async eviction correctness

### Integration Tests

- [ ] Search with 100K results + async scroll
- [ ] Search with 1M results + memory monitoring
- [ ] Multiple searches in sequence (memory cleanup)
- [ ] Fast scroll (>10 rows/ms) + predictive load
- [ ] Slow scroll + cache efficiency

### Performance Tests

- [ ] Benchmark: Scroll latency (target <50ms)
- [ ] Benchmark: Memory usage (target <300MB for 1M)
- [ ] Benchmark: Cache hit rate (target >80%)
- [ ] Benchmark: Search latency (target <120ms for 1M)
- [ ] Benchmark: GC pause time (target p95 <5ms)

### Regression Tests

- [ ] Basic search still works
- [ ] Filters still apply correctly
- [ ] Sorting still works
- [ ] Selection still works
- [ ] Export/copy still works

---

## DEPLOYMENT CHECKLIST

### Pre-Release

- [ ] All P0 tasks completed
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Performance benchmarks met or exceeded
- [ ] Code review completed
- [ ] Documentation updated
- [ ] PERFORMANCE_EVALUATION.md updated with new scores

### Release Notes

```
v3.1 - Performance Optimization Release

New Features:
- Async virtual scrolling for 1M+ results
- Memory-bounded results model (max 300MB)
- Predictive cache loading based on scroll velocity
- Comprehensive performance metrics and dashboards

Improvements:
- 10x reduction in scroll latency (500ms → 50ms)
- 60% memory reduction for large result sets
- 50% improvement in cache hit rate
- Non-blocking cache eviction

Bug Fixes:
- Fixed memory leaks in unbounded _all_data
- Fixed UI freezing on large searches
- Fixed cache bloat issues
```

### Rollback Plan

If issues found:
1. Revert PERFORMANCE_OPTIMIZATIONS.py changes
2. Keep BoundedVirtualModel (safe, tested)
3. Disable AsyncRowLoader if issues found
4. Fall back to sync loading

---

## EFFORT SUMMARY

| Phase | Duration | Score Improvement |
|-------|----------|------------------|
| P0 (Critical) | 18 hours | 7.5 → 8.5 |
| P1 (Important) | 12 hours | 8.5 → 9.2 |
| P2 (Nice-to-have) | 15 hours | 9.2 → 9.5 |
| **TOTAL** | **45 hours** | **7.5 → 9.5** |

---

## SUCCESS CRITERIA (v3.1 Final)

- [x] Scroll latency <50ms (all result sizes)
- [x] Memory usage <300MB (1M results)
- [x] Cache hit rate >80% (repeated searches)
- [x] Search latency <120ms (1M results)
- [x] GC pause p95 <5ms
- [x] No UI freezing
- [x] Comprehensive metrics available
- [x] Enterprise SLA ready

---

## NOTES FOR TEAM

1. **Start with Task 1 (Async Scrolling)** - Highest impact on UX
2. **Parallel work possible** - Tasks 2, 3, 4 can be done in parallel
3. **Test frequently** - Each task should have unit tests
4. **Monitor metrics** - Use PerformanceMetricsCollector from day 1
5. **Code review rigorously** - These are critical path items
6. **Update benchmarks** - As each task completes

---

End of Implementation Checklist

"""
Example usage of enhanced cache system with TTL by type, statistics, and prewarming.

This demonstrates best practices for using the improved caching system in Smart Search Pro.
"""

import sys
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.cache import LRUCache, get_cache


def example_search_results_cache():
    """Example: Caching search results with different TTLs."""
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Search Results Cache")
    print("=" * 60)

    # Create cache with type-specific TTLs
    search_cache = LRUCache(
        max_size=5000,
        max_bytes=50 * 1024 * 1024,  # 50 MB
        ttl_by_type={
            "recent": 300,       # 5 minutes for recent searches
            "frequent": 1800,    # 30 minutes for frequent queries
            "pinned": None,      # No expiration for pinned results
        },
        enable_stats=True
    )

    # Simulate search operations
    print("\nSimulating search operations...")

    # Recent search - short TTL
    search_cache.set(
        "query:documents",
        ["doc1.pdf", "doc2.pdf", "doc3.pdf"],
        cache_type="recent"
    )

    # Frequent search - longer TTL
    search_cache.set(
        "query:*.py",
        ["main.py", "utils.py", "config.py"],
        cache_type="frequent"
    )

    # Pinned search - no expiration
    search_cache.set(
        "query:important",
        ["important1.txt", "important2.txt"],
        cache_type="pinned"
    )

    print(f"  Cached 3 different search types")

    # Access results
    result1 = search_cache.get("query:documents")
    result2 = search_cache.get("query:*.py")
    result3 = search_cache.get("query:important")

    print(f"  Retrieved {len(result1) + len(result2) + len(result3)} files from cache")

    # Show statistics
    stats = search_cache.get_detailed_stats()
    print(f"\nCache Statistics:")
    print(f"  Hit Rate: {stats.hit_rate:.2%}")
    print(f"  Total Requests: {stats.total_requests}")
    print(f"  Cache Size: {stats.size}/{stats.max_size}")
    print(f"  Memory Used: {stats.bytes_used:,} bytes")


def example_thumbnail_cache():
    """Example: Caching thumbnails with prewarming."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Thumbnail Cache with Prewarming")
    print("=" * 60)

    # Create thumbnail cache
    thumbnail_cache = LRUCache(
        max_size=10000,
        max_bytes=100 * 1024 * 1024,  # 100 MB
        default_ttl=3600,  # 1 hour
        enable_stats=True
    )

    # Prewarm with commonly accessed thumbnails
    print("\nPrewarming cache with common thumbnails...")

    common_thumbnails = {
        f"thumb_{i}.jpg": b"JPEG_DATA_HERE" * 100  # Simulate thumbnail data
        for i in range(50)
    }

    prewarmed = thumbnail_cache.prewarm(
        common_thumbnails,
        cache_type="thumbnail",
        ttl=7200  # 2 hours for prewarmed thumbnails
    )

    print(f"  Prewarmed {prewarmed} thumbnails")

    # Simulate usage
    for i in range(10):
        thumbnail_cache.get(f"thumb_{i}.jpg")

    stats = thumbnail_cache.get_detailed_stats()
    print(f"\nCache Performance:")
    print(f"  Hit Rate: {stats.hit_rate:.2%}")
    print(f"  Fill Rate: {stats.fill_rate:.2%}")
    print(f"  Cache Size: {stats.size}/{stats.max_size}")


def example_file_hash_cache():
    """Example: File hash cache with selective invalidation."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: File Hash Cache with Selective Invalidation")
    print("=" * 60)

    # Create hash cache with different TTLs for quick vs full hashes
    hash_cache = LRUCache(
        max_size=50000,
        max_bytes=200 * 1024 * 1024,  # 200 MB
        ttl_by_type={
            "quick": 1800,    # 30 minutes for quick hashes
            "full": 7200,     # 2 hours for full hashes
            "verified": None, # No expiration for verified hashes
        },
        enable_stats=True
    )

    print("\nCaching file hashes...")

    # Cache different types of hashes
    hash_cache.set("file1.dat:quick", "abc123", cache_type="quick")
    hash_cache.set("file1.dat:full", "def456789", cache_type="full")
    hash_cache.set("file2.dat:quick", "ghi789", cache_type="quick")
    hash_cache.set("file2.dat:full", "jkl012345", cache_type="full")
    hash_cache.set("verified:file3.dat", "mno678", cache_type="verified")

    print(f"  Cached {hash_cache.size()} hashes")

    # Invalidate only quick hashes (e.g., after file modifications)
    print("\nInvalidating quick hashes after file modification...")
    removed = hash_cache.invalidate_by_type("quick")
    print(f"  Removed {removed} quick hashes")
    print(f"  Remaining: {hash_cache.size()} hashes (full and verified)")

    # Pattern-based invalidation
    hash_cache.set("temp:file4.dat", "pqr901", cache_type="full")
    hash_cache.set("temp:file5.dat", "stu234", cache_type="full")

    print("\nInvalidating temporary hashes...")
    removed = hash_cache.invalidate_by_pattern(lambda k: str(k).startswith("temp:"))
    print(f"  Removed {removed} temporary hashes")

    stats = hash_cache.get_detailed_stats()
    print(f"\nFinal State:")
    print(f"  Total Hashes: {stats.size}")
    print(f"  Total Sets: {stats.sets}")
    print(f"  Total Deletes: {stats.deletes}")


def example_global_cache_manager():
    """Example: Using global cache manager for multiple caches."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Global Cache Manager")
    print("=" * 60)

    # Get named caches (automatically created if they don't exist)
    search_cache = get_cache(
        "search_results",
        max_size=5000,
        default_ttl=600
    )

    thumbnail_cache = get_cache(
        "thumbnails",
        max_size=10000,
        default_ttl=3600
    )

    hash_cache = get_cache(
        "file_hashes",
        max_size=50000,
        default_ttl=7200
    )

    print("\nCreated 3 named caches via cache manager")

    # Add some data
    search_cache.set("query1", ["result1", "result2"])
    thumbnail_cache.set("thumb1", b"data")
    hash_cache.set("hash1", "abc123")

    # Get statistics for all caches
    from core.cache import _cache_manager

    all_stats = _cache_manager.stats_all()

    print("\nAll Cache Statistics:")
    for name, stats in all_stats.items():
        print(f"\n  {name}:")
        print(f"    Size: {stats['size']}/{stats['max_size']}")
        print(f"    Hits: {stats['hits']}, Misses: {stats['misses']}")
        print(f"    Hit Rate: {stats['hit_rate']:.2%}")

    # Cleanup all caches
    print("\nCleaning up expired entries in all caches...")
    _cache_manager.cleanup_all()


def example_cache_monitoring():
    """Example: Monitoring cache performance over time."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Cache Performance Monitoring")
    print("=" * 60)

    cache = LRUCache(
        max_size=100,
        default_ttl=60,
        enable_stats=True
    )

    print("\nSimulating workload...")

    # Simulate realistic usage pattern
    for i in range(200):
        # 70% read, 30% write
        if i % 10 < 7:
            # Read (some hits, some misses)
            key = f"key_{i % 50}"  # Reuse some keys
            cache.get(key)
        else:
            # Write
            cache.set(f"key_{i}", f"value_{i}")

    # Show detailed statistics
    stats = cache.get_detailed_stats()

    print(f"\nPerformance Metrics:")
    print(f"  Total Requests: {stats.total_requests}")
    print(f"  Hits: {stats.hits}")
    print(f"  Misses: {stats.misses}")
    print(f"  Hit Rate: {stats.hit_rate:.2%}")
    print(f"  Miss Rate: {stats.miss_rate:.2%}")
    print(f"\nCache State:")
    print(f"  Size: {stats.size}/{stats.max_size}")
    print(f"  Fill Rate: {stats.fill_rate:.2%}")
    print(f"  Memory Used: {stats.bytes_used:,} bytes")
    print(f"\nOperations:")
    print(f"  Sets: {stats.sets}")
    print(f"  Deletes: {stats.deletes}")
    print(f"  Evictions: {stats.evictions}")
    print(f"  Expirations: {stats.expirations}")

    # Export statistics for monitoring system
    stats_dict = stats.to_dict()
    print(f"\nExportable Stats (for monitoring): {len(stats_dict)} metrics available")


def main():
    """Run all examples."""
    print("\n")
    print("*" * 60)
    print("SMART SEARCH PRO - ENHANCED CACHE USAGE EXAMPLES")
    print("*" * 60)

    try:
        example_search_results_cache()
        example_thumbnail_cache()
        example_file_hash_cache()
        example_global_cache_manager()
        example_cache_monitoring()

        print("\n" + "=" * 60)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nKey Takeaways:")
        print("  1. Use type-specific TTLs for different data types")
        print("  2. Prewarm caches on startup for better initial performance")
        print("  3. Use selective invalidation instead of clearing entire cache")
        print("  4. Monitor cache statistics to optimize configuration")
        print("  5. Use global cache manager for centralized cache handling")
        print()

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
Example usage of the Smart Search Pro duplicate finder module.

This script demonstrates all the key features:
- Multi-pass scanning with progress reporting
- Hash caching
- Different selection strategies
- Various deletion actions
- Statistics and reporting
"""

from pathlib import Path
from duplicates import (
    DuplicateScanner,
    HashAlgorithm,
    SelectionStrategy,
    RecycleBinAction,
    MoveToFolderAction,
    HardLinkAction,
    AuditLogger,
    execute_batch_action,
    get_action_summary,
)


def example_basic_scan():
    """Basic duplicate scan example."""
    print("=" * 60)
    print("EXAMPLE 1: Basic Duplicate Scan")
    print("=" * 60)

    # Create scanner
    scanner = DuplicateScanner(
        algorithm=HashAlgorithm.SHA256,
        use_cache=True,
        max_workers=4
    )

    # Define progress callback
    def progress_callback(progress):
        print(f"Pass {progress.current_pass}/3: {progress.current_phase} - "
              f"{progress.progress_percent:.1f}% complete "
              f"({progress.current_file}/{progress.total_files} files)")

    # Scan for duplicates
    print("\nScanning for duplicates...")
    groups = scanner.scan(
        paths=[str(Path.home() / 'Documents')],
        recursive=True,
        progress_callback=progress_callback
    )

    # Display results
    print(f"\nFound {len(groups.groups)} duplicate groups")

    stats = groups.get_total_statistics()
    print(f"Total duplicate files: {stats['total_duplicate_files']}")
    print(f"Wasted space: {stats['total_wasted_space'] / (1024*1024):.2f} MB")

    # Show top 5 most wasteful groups
    print("\nTop 5 most wasteful duplicate groups:")
    sorted_groups = groups.sort_by_wasted_space()[:5]
    for i, group in enumerate(sorted_groups, 1):
        print(f"{i}. {group.file_count} files, "
              f"{group.wasted_space / (1024*1024):.2f} MB wasted")
        for file in group.files:
            print(f"   - {file.path}")

    # Show scan statistics
    scan_stats = scanner.get_stats()
    print(f"\nScan statistics:")
    print(f"  Duration: {scan_stats.scan_duration:.2f}s")
    print(f"  Cache hit rate: {scan_stats.cache_hits / (scan_stats.cache_hits + scan_stats.cache_misses) * 100:.1f}%")


def example_selection_strategies():
    """Demonstrate different selection strategies."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Selection Strategies")
    print("=" * 60)

    scanner = DuplicateScanner(use_cache=True)
    groups = scanner.scan([str(Path.home() / 'Pictures')], recursive=True)

    if not groups.groups:
        print("No duplicates found")
        return

    # Strategy 1: Keep oldest
    print("\nStrategy 1: Keep Oldest File")
    groups.apply_strategy_to_all(SelectionStrategy.KEEP_OLDEST)
    print(f"Selected {len(groups.get_all_selected_for_deletion())} files for deletion")
    print(f"Would recover {groups.get_total_statistics()['total_recoverable_space'] / (1024*1024):.2f} MB")

    # Strategy 2: Keep newest
    print("\nStrategy 2: Keep Newest File")
    groups.apply_strategy_to_all(SelectionStrategy.KEEP_NEWEST)
    print(f"Selected {len(groups.get_all_selected_for_deletion())} files for deletion")

    # Strategy 3: Folder priority
    print("\nStrategy 3: Folder Priority")
    priority_folders = [
        str(Path.home() / 'Pictures' / 'Favorites'),
        str(Path.home() / 'Pictures' / 'Archive'),
    ]
    groups.apply_strategy_to_all(
        SelectionStrategy.FOLDER_PRIORITY,
        folder_priorities=priority_folders
    )
    print(f"Selected {len(groups.get_all_selected_for_deletion())} files for deletion")

    # Show what would be deleted
    print("\nFiles selected for deletion (top 10):")
    selected = groups.get_all_selected_for_deletion()[:10]
    for path in selected:
        print(f"  - {path}")


def example_safe_deletion():
    """Demonstrate safe deletion actions."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Safe Deletion Actions")
    print("=" * 60)

    # Setup audit logging
    audit_log_path = Path.home() / '.cache' / 'smart_search' / 'audit.json'
    audit_logger = AuditLogger(audit_log_path)

    # Scan for duplicates
    scanner = DuplicateScanner(use_cache=True)
    groups = scanner.scan([str(Path.home() / 'Downloads')], recursive=True)

    if not groups.groups:
        print("No duplicates found")
        return

    # Select files to delete (keep oldest)
    groups.apply_strategy_to_all(SelectionStrategy.KEEP_OLDEST)
    files_to_delete = groups.get_all_selected_for_deletion()

    print(f"Found {len(files_to_delete)} files to delete")

    # Action 1: Move to recycle bin (safest)
    print("\nAction 1: Move to Recycle Bin")
    recycle_action = RecycleBinAction(audit_logger=audit_logger)

    # Process first 5 files
    results = execute_batch_action(
        action=recycle_action,
        file_paths=files_to_delete[:5]
    )

    summary = get_action_summary(results)
    print(f"  Success: {summary['successful']}/{summary['total']}")
    print(f"  Space freed: {summary['total_bytes_freed'] / (1024*1024):.2f} MB")

    # Action 2: Move to folder for review
    print("\nAction 2: Move to Review Folder")
    review_folder = Path.home() / 'DuplicatesReview'
    move_action = MoveToFolderAction(audit_logger=audit_logger)

    results = execute_batch_action(
        action=move_action,
        file_paths=files_to_delete[5:10],
        target_path=review_folder
    )

    summary = get_action_summary(results)
    print(f"  Success: {summary['successful']}/{summary['total']}")
    print(f"  Files moved to: {review_folder}")


def example_hard_links():
    """Demonstrate hard link replacement to save space."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Hard Link Replacement")
    print("=" * 60)

    # Scan for duplicates
    scanner = DuplicateScanner(use_cache=True)
    groups = scanner.scan([str(Path.home() / 'Music')], recursive=True)

    if not groups.groups:
        print("No duplicates found")
        return

    # Setup audit logger
    audit_logger = AuditLogger(Path.home() / '.cache' / 'smart_search' / 'audit.json')
    hardlink_action = HardLinkAction(audit_logger=audit_logger)

    total_saved = 0
    operations = 0

    # For each duplicate group, replace duplicates with hard links
    for group in groups.groups:
        if len(group.files) < 2:
            continue

        # Keep first file, replace others with hard links
        original = group.files[0].path

        for file in group.files[1:]:
            result = hardlink_action.execute(
                source_path=file.path,
                target_path=original
            )

            if result.success:
                total_saved += result.bytes_freed
                operations += 1
                print(f"  Linked: {file.path.name} -> {original.name}")
            else:
                print(f"  Failed: {file.path.name} - {result.error}")

    print(f"\nCompleted {operations} hard link operations")
    print(f"Total space saved: {total_saved / (1024*1024):.2f} MB")


def example_custom_selection():
    """Demonstrate custom selection logic."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Custom Selection Logic")
    print("=" * 60)

    scanner = DuplicateScanner(use_cache=True)
    groups = scanner.scan([str(Path.home() / 'Documents')], recursive=True)

    if not groups.groups:
        print("No duplicates found")
        return

    # Custom selector: Keep files in specific folders, delete others
    def custom_selector(files):
        """Keep files with 'important' or 'backup' in path, delete others."""
        to_delete = []
        important_keywords = ['important', 'backup', 'archive']

        # Check if any file is in an important location
        has_important = any(
            any(keyword in str(f.path).lower() for keyword in important_keywords)
            for f in files
        )

        if has_important:
            # Keep important files, delete others
            for f in files:
                if not any(keyword in str(f.path).lower() for keyword in important_keywords):
                    to_delete.append(f)
        else:
            # No important files, keep oldest
            oldest = min(files, key=lambda f: f.mtime)
            to_delete = [f for f in files if f != oldest]

        return to_delete

    # Apply custom selection
    groups.apply_strategy_to_all(
        SelectionStrategy.CUSTOM,
        custom_selector=custom_selector
    )

    print(f"Selected {len(groups.get_all_selected_for_deletion())} files for deletion")
    print(f"Would recover {groups.get_total_statistics()['total_recoverable_space'] / (1024*1024):.2f} MB")


def example_export_report():
    """Demonstrate exporting detailed duplicate report."""
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Export Duplicate Report")
    print("=" * 60)

    scanner = DuplicateScanner(use_cache=True)
    groups = scanner.scan([str(Path.home() / 'Desktop')], recursive=True)

    # Export report
    report = groups.export_report(include_files=True)

    # Save to JSON file
    import json
    report_path = Path.home() / 'duplicate_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"Report saved to: {report_path}")
    print(f"Report contains {report['summary']['total_groups']} duplicate groups")
    print(f"Total wasted space: {report['summary']['total_wasted_space'] / (1024*1024):.2f} MB")


def example_size_filtering():
    """Demonstrate filtering duplicates by size."""
    print("\n" + "=" * 60)
    print("EXAMPLE 7: Size Filtering")
    print("=" * 60)

    # Scan only large files (> 10 MB)
    scanner = DuplicateScanner(
        use_cache=True,
        min_file_size=10 * 1024 * 1024  # 10 MB
    )

    groups = scanner.scan([str(Path.home() / 'Videos')], recursive=True)

    print(f"Found {len(groups.groups)} duplicate groups of large files")

    # Further filter by size range
    large_groups = groups.filter_by_size(
        min_size=100 * 1024 * 1024,  # 100 MB
        max_size=1024 * 1024 * 1024  # 1 GB
    )

    print(f"Groups with files between 100 MB and 1 GB: {len(large_groups)}")

    # Show largest duplicates
    if large_groups:
        largest = max(large_groups, key=lambda g: g.files[0].size)
        print(f"\nLargest duplicate file: {largest.files[0].size / (1024*1024):.2f} MB")
        print(f"Found {largest.file_count} copies")


if __name__ == '__main__':
    # Run all examples
    # NOTE: These examples use real directories. Adjust paths as needed.

    print("Smart Search Pro - Duplicate Finder Examples")
    print("=" * 60)

    # Uncomment the examples you want to run:

    # example_basic_scan()
    # example_selection_strategies()
    # example_safe_deletion()
    # example_hard_links()
    # example_custom_selection()
    # example_export_report()
    # example_size_filtering()

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)

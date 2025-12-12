"""
Examples for using the Folder Comparison Module

This file demonstrates various use cases for the comparison system.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from comparison import (
    FolderComparator,
    ComparisonMode,
    SyncEngine,
    ConflictResolution,
    FileStatus,
    format_size
)


def example_basic_comparison():
    """Basic directory comparison."""
    print("=" * 80)
    print("Example 1: Basic Comparison")
    print("=" * 80)

    # Create comparator
    comparator = FolderComparator(mode=ComparisonMode.CONTENT_HASH)

    # Compare directories
    result = comparator.compare(
        source=Path.home() / 'Documents',
        target=Path.home() / 'Backup' / 'Documents',
        recursive=True
    )

    # Display results
    print(f"\nComparison completed in {result.duration:.2f}s")
    print(f"Total files: {result.stats.total_files}")
    print(f"Same: {result.stats.same_files}")
    print(f"Different: {result.stats.different_files}")
    print(f"Missing in target: {result.stats.missing_in_target}")
    print(f"Extra in target: {result.stats.extra_in_target}")
    print(f"\nSpace savings potential: {format_size(result.stats.space_savings_potential)}")


def example_filtered_comparison():
    """Comparison with file filtering."""
    print("\n" + "=" * 80)
    print("Example 2: Filtered Comparison (Images only, last 30 days)")
    print("=" * 80)

    # Create comparator with filters
    comparator = FolderComparator(
        mode=ComparisonMode.SIZE_NAME,
        extensions=['.jpg', '.jpeg', '.png', '.gif', '.webp'],
        min_size=10 * 1024,  # At least 10KB
        max_size=50 * 1024 * 1024,  # Max 50MB
        modified_after=datetime.now() - timedelta(days=30)
    )

    # Compare
    result = comparator.compare(
        source=Path.home() / 'Pictures',
        target=Path.home() / 'Backup' / 'Pictures',
        recursive=True
    )

    # Show missing images
    missing = result.get_missing_files()
    print(f"\n{len(missing)} images missing in backup:")
    for comp in missing[:10]:  # Show first 10
        print(f"  - {comp.relative_path} ({format_size(comp.source_size)})")


def example_with_progress():
    """Comparison with progress tracking."""
    print("\n" + "=" * 80)
    print("Example 3: Comparison with Progress")
    print("=" * 80)

    comparator = FolderComparator(mode=ComparisonMode.CONTENT_HASH)

    def progress_callback(current, total):
        percent = (current / total * 100) if total > 0 else 0
        print(f"\rProgress: {current}/{total} ({percent:.1f}%)", end='', flush=True)

    result = comparator.compare(
        source=Path.home() / 'Documents',
        target=Path.home() / 'Backup' / 'Documents',
        recursive=True,
        progress_callback=progress_callback
    )

    print(f"\n\nComparison complete!")


def example_sync_preview():
    """Preview sync operations without executing."""
    print("\n" + "=" * 80)
    print("Example 4: Sync Preview (Dry Run)")
    print("=" * 80)

    engine = SyncEngine(conflict_resolution=ConflictResolution.NEWER_WINS)

    # Preview sync
    result = engine.sync(
        source=Path.home() / 'Documents',
        target=Path.home() / 'Backup' / 'Documents',
        copy_missing=True,
        delete_extra=False,
        update_different=True,
        dry_run=True  # Preview only
    )

    print(f"\nOperations to perform: {result.total_operations}")
    print(f"Conflicts detected: {len(result.conflicts)}")

    # Show operations by type
    from collections import Counter
    action_counts = Counter(op.action for op in result.operations)

    print("\nOperations by type:")
    for action, count in action_counts.items():
        print(f"  {action.value}: {count}")


def example_sync_execute():
    """Execute synchronization."""
    print("\n" + "=" * 80)
    print("Example 5: Execute Sync")
    print("=" * 80)

    engine = SyncEngine(conflict_resolution=ConflictResolution.NEWER_WINS)

    def progress_callback(current, total):
        percent = (current / total * 100) if total > 0 else 0
        print(f"\rSyncing: {current}/{total} ({percent:.1f}%)", end='', flush=True)

    # Execute sync
    result = engine.sync(
        source=Path.home() / 'Documents',
        target=Path.home() / 'Backup' / 'Documents',
        copy_missing=True,
        delete_extra=False,
        update_different=True,
        dry_run=False,  # Execute
        progress_callback=progress_callback
    )

    print(f"\n\nSync complete!")
    print(f"Successful operations: {result.successful_operations}")
    print(f"Failed operations: {result.failed_operations}")
    print(f"Bytes transferred: {format_size(result.total_bytes_transferred)}")


def example_bidirectional_sync():
    """Bidirectional synchronization."""
    print("\n" + "=" * 80)
    print("Example 6: Bidirectional Sync")
    print("=" * 80)

    engine = SyncEngine(conflict_resolution=ConflictResolution.NEWER_WINS)

    # Sync in both directions
    result = engine.sync(
        source=Path.home() / 'Documents',
        target=Path.home() / 'Backup' / 'Documents',
        copy_missing=True,
        delete_extra=False,
        update_different=True,
        bidirectional=True,  # Sync both ways
        dry_run=True
    )

    print(f"Operations: {result.total_operations}")
    print("This will sync files in both directions")


def example_different_modes():
    """Compare using different modes."""
    print("\n" + "=" * 80)
    print("Example 7: Comparison Mode Comparison")
    print("=" * 80)

    source = Path.home() / 'Documents'
    target = Path.home() / 'Backup' / 'Documents'

    modes = [
        (ComparisonMode.CONTENT_HASH, "Content Hash"),
        (ComparisonMode.SIZE_NAME, "Size + Name"),
        (ComparisonMode.NAME_ONLY, "Name Only")
    ]

    for mode, name in modes:
        comparator = FolderComparator(mode=mode)
        result = comparator.compare(source, target, recursive=False)

        print(f"\n{name}:")
        print(f"  Duration: {result.duration:.2f}s")
        print(f"  Files: {result.stats.total_files}")
        print(f"  Different: {result.stats.different_files}")


def example_export_report():
    """Export comparison report."""
    print("\n" + "=" * 80)
    print("Example 8: Export Reports")
    print("=" * 80)

    comparator = FolderComparator(mode=ComparisonMode.CONTENT_HASH)

    result = comparator.compare(
        source=Path.home() / 'Documents',
        target=Path.home() / 'Backup' / 'Documents',
        recursive=True
    )

    # Export to CSV
    csv_file = Path.home() / 'comparison_report.csv'
    export_to_csv(result, csv_file)
    print(f"CSV report saved to: {csv_file}")

    # Export to HTML
    html_file = Path.home() / 'comparison_report.html'
    export_to_html(result, html_file)
    print(f"HTML report saved to: {html_file}")


def export_to_csv(result, file_path: Path):
    """Export result to CSV."""
    import csv

    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Status', 'Relative Path', 'Size', 'Modified'])

        for comp in result.comparisons:
            writer.writerow([
                comp.status.value,
                comp.relative_path,
                comp.source_size or comp.target_size,
                (comp.source_modified or comp.target_modified).isoformat() if (comp.source_modified or comp.target_modified) else ''
            ])


def export_to_html(result, file_path: Path):
    """Export result to HTML."""
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Comparison Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #0078D4; color: white; }}
        .same {{ background-color: #d4edda; }}
        .different {{ background-color: #fff3cd; }}
        .missing {{ background-color: #f8d7da; }}
        .extra {{ background-color: #d1ecf1; }}
    </style>
</head>
<body>
    <h1>Folder Comparison Report</h1>
    <p><strong>Source:</strong> {result.source_dir}</p>
    <p><strong>Target:</strong> {result.target_dir}</p>
    <h2>Statistics</h2>
    <ul>
        <li>Total: {result.stats.total_files}</li>
        <li>Same: {result.stats.same_files}</li>
        <li>Different: {result.stats.different_files}</li>
        <li>Missing: {result.stats.missing_in_target}</li>
        <li>Extra: {result.stats.extra_in_target}</li>
    </ul>
    <table>
        <tr><th>Status</th><th>File</th><th>Size</th></tr>
"""

    for comp in result.comparisons:
        row_class = {
            FileStatus.SAME: 'same',
            FileStatus.DIFFERENT: 'different',
            FileStatus.MISSING_IN_TARGET: 'missing',
            FileStatus.EXTRA_IN_TARGET: 'extra'
        }[comp.status]

        html += f"""
        <tr class="{row_class}">
            <td>{comp.status.value}</td>
            <td>{comp.relative_path}</td>
            <td>{format_size(comp.source_size or comp.target_size)}</td>
        </tr>
"""

    html += """
    </table>
</body>
</html>
"""

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html)


def example_operation_logs():
    """View operation logs."""
    print("\n" + "=" * 80)
    print("Example 9: Operation Logs (for undo)")
    print("=" * 80)

    engine = SyncEngine()

    # Get recent operations
    operations = engine.get_undo_operations(limit=10)

    print(f"\nLast {len(operations)} operations:")
    for op in operations:
        timestamp = op.get('timestamp', 'Unknown')
        action = op.get('action', 'Unknown')
        path = op.get('relative_path', 'Unknown')
        success = op.get('success', False)

        status = "✓" if success else "✗"
        print(f"  {status} {timestamp}: {action} - {path}")


def example_conflict_resolution():
    """Handle conflicts with different strategies."""
    print("\n" + "=" * 80)
    print("Example 10: Conflict Resolution Strategies")
    print("=" * 80)

    strategies = [
        (ConflictResolution.NEWER_WINS, "Newer Wins"),
        (ConflictResolution.LARGER_WINS, "Larger Wins"),
        (ConflictResolution.SOURCE_WINS, "Source Wins"),
    ]

    for strategy, name in strategies:
        engine = SyncEngine(conflict_resolution=strategy)

        result = engine.sync(
            source=Path.home() / 'Documents',
            target=Path.home() / 'Backup' / 'Documents',
            update_different=True,
            dry_run=True
        )

        print(f"\n{name}:")
        print(f"  Operations: {result.total_operations}")
        print(f"  Conflicts: {len(result.conflicts)}")


def main():
    """Run all examples."""
    print("Folder Comparison Module - Examples")
    print("=" * 80)
    print("\nNOTE: These examples use placeholder paths.")
    print("Update the paths to match your actual directories.\n")

    # Uncomment the examples you want to run:

    # example_basic_comparison()
    # example_filtered_comparison()
    # example_with_progress()
    # example_sync_preview()
    # example_sync_execute()  # Be careful - this modifies files!
    # example_bidirectional_sync()
    # example_different_modes()
    # example_export_report()
    # example_operation_logs()
    # example_conflict_resolution()

    print("\n" + "=" * 80)
    print("To run examples, uncomment them in the main() function")
    print("=" * 80)


if __name__ == '__main__':
    main()

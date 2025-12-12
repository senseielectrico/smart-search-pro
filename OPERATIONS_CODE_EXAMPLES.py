"""
Operations Panel - Code Examples
Quick reference for common integration patterns
"""

# ============================================================================
# EXAMPLE 1: Basic Integration in Main Window
# ============================================================================

def example_1_basic_integration():
    """Add operations panel to main window"""
    from PyQt6.QtWidgets import QMainWindow, QTabWidget
    from ui.operations_panel import OperationsPanel
    from operations.manager import OperationsManager
    from pathlib import Path

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()

            # Create operations manager (shared)
            history_file = Path.home() / ".smart_search" / "operations_history.json"
            history_file.parent.mkdir(parents=True, exist_ok=True)

            self.operations_manager = OperationsManager(
                max_concurrent_operations=2,
                history_file=str(history_file),
                auto_save_history=True
            )

            # Create tabs
            tabs = QTabWidget()

            # Add operations panel
            self.operations_panel = OperationsPanel(
                parent=self,
                operations_manager=self.operations_manager
            )
            tabs.addTab(self.operations_panel, "File Operations")

            self.setCentralWidget(tabs)

        def closeEvent(self, event):
            """Cleanup on close"""
            if self.operations_panel.has_active_operations():
                # Ask user before closing
                pass

            self.operations_manager.shutdown()
            event.accept()


# ============================================================================
# EXAMPLE 2: Copy Files from Search Results
# ============================================================================

def example_2_copy_from_search():
    """Copy files from search results"""
    from operations.manager import OperationPriority
    from pathlib import Path

    def copy_search_results(operations_manager, file_paths, destination):
        """Copy selected search results to destination"""

        # Build destination paths
        dest_paths = []
        for source in file_paths:
            filename = Path(source).name
            dest_path = str(Path(destination) / filename)
            dest_paths.append(dest_path)

        # Queue copy operation
        operation_id = operations_manager.queue_copy(
            source_paths=file_paths,
            dest_paths=dest_paths,
            priority=OperationPriority.NORMAL,
            verify=True,  # Enable hash verification
            preserve_metadata=True
        )

        print(f"Operation queued: {operation_id}")
        return operation_id


# ============================================================================
# EXAMPLE 3: Move Files with Confirmation
# ============================================================================

def example_3_move_with_confirmation():
    """Move files with user confirmation"""
    from PyQt6.QtWidgets import QMessageBox
    from operations.manager import OperationPriority

    def move_files_confirmed(parent, operations_manager, sources, destination):
        """Move files after confirmation"""

        # Ask user
        reply = QMessageBox.question(
            parent,
            "Move Files",
            f"Move {len(sources)} file(s) to {destination}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Build paths
            from pathlib import Path
            dest_paths = [
                str(Path(destination) / Path(src).name)
                for src in sources
            ]

            # Queue move
            op_id = operations_manager.queue_move(
                source_paths=sources,
                dest_paths=dest_paths,
                priority=OperationPriority.NORMAL,
                verify=True
            )

            return op_id

        return None


# ============================================================================
# EXAMPLE 4: Monitor Operation Progress
# ============================================================================

def example_4_monitor_progress():
    """Monitor operation progress programmatically"""

    def monitor_operation(operations_manager, operation_id):
        """Print progress updates"""
        import time

        while True:
            # Get progress
            progress = operations_manager.get_progress(operation_id)

            if progress:
                percent = progress.progress_percent
                speed = progress.current_speed
                eta = progress.eta_seconds

                print(f"Progress: {percent:.1f}% | "
                      f"Speed: {format_speed(speed)} | "
                      f"ETA: {format_time(eta)}")

                # Check if complete
                if percent >= 100:
                    break

            time.sleep(1)

    def format_speed(bytes_per_sec):
        """Format speed"""
        if bytes_per_sec < 1024:
            return f"{bytes_per_sec:.0f} B/s"
        elif bytes_per_sec < 1024 ** 2:
            return f"{bytes_per_sec / 1024:.1f} KB/s"
        elif bytes_per_sec < 1024 ** 3:
            return f"{bytes_per_sec / (1024 ** 2):.1f} MB/s"
        else:
            return f"{bytes_per_sec / (1024 ** 3):.2f} GB/s"

    def format_time(seconds):
        """Format time"""
        if seconds is None:
            return "Unknown"
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds / 60:.1f}m"
        else:
            return f"{seconds / 3600:.1f}h"


# ============================================================================
# EXAMPLE 5: Copy with Custom Progress Callback
# ============================================================================

def example_5_custom_progress():
    """Use FileCopier directly with custom callback"""
    from operations.copier import FileCopier

    def copy_with_callback(source, destination):
        """Copy file with custom progress handling"""

        def on_progress(bytes_copied, total_bytes):
            """Custom progress callback"""
            percent = (bytes_copied / total_bytes) * 100
            print(f"Copying: {percent:.1f}% ({bytes_copied}/{total_bytes} bytes)")

        # Create copier
        copier = FileCopier(
            max_workers=4,
            verify_after_copy=True,
            verify_algorithm='md5',
            retry_attempts=3
        )

        try:
            # Copy file
            success = copier.copy_file(
                source=source,
                destination=destination,
                progress_callback=on_progress,
                preserve_metadata=True
            )

            if success:
                print(f"Copy successful: {destination}")
            else:
                print("Copy failed")

            return success

        finally:
            copier.shutdown()


# ============================================================================
# EXAMPLE 6: Batch Copy with Results
# ============================================================================

def example_6_batch_copy():
    """Copy multiple files and get results"""
    from operations.copier import FileCopier
    from pathlib import Path

    def batch_copy_files(file_pairs):
        """Copy multiple files in parallel"""

        copier = FileCopier(max_workers=4)

        def progress_callback(file_path, copied, total):
            """Per-file progress"""
            print(f"{Path(file_path).name}: {copied}/{total} bytes")

        try:
            # Copy all files
            results = copier.copy_files_batch(
                file_pairs=file_pairs,
                progress_callback=progress_callback,
                preserve_metadata=True
            )

            # Print results
            for dest, (success, error) in results.items():
                if success:
                    print(f"OK: {dest}")
                else:
                    print(f"FAIL: {dest} - {error}")

            return results

        finally:
            copier.shutdown()


# ============================================================================
# EXAMPLE 7: Same-Volume Move Optimization
# ============================================================================

def example_7_optimized_move():
    """Move files with volume detection"""
    from operations.mover import FileMover

    def smart_move(source, destination):
        """Move with automatic optimization"""

        mover = FileMover(
            verify_after_move=True,
            preserve_metadata=True
        )

        try:
            # Check strategy
            strategy = mover.get_move_strategy(source, destination)
            print(f"Using strategy: {strategy}")

            # Move file
            success, error = mover.move_file(source, destination)

            if success:
                print(f"Moved successfully: {destination}")
            else:
                print(f"Move failed: {error}")

            return success

        finally:
            mover.cleanup()


# ============================================================================
# EXAMPLE 8: Verify Files
# ============================================================================

def example_8_verify_files():
    """Verify copied files"""
    from operations.verifier import FileVerifier, HashAlgorithm

    def verify_copy(source, destination):
        """Verify files match"""

        verifier = FileVerifier(algorithm=HashAlgorithm.MD5)

        # Verify
        is_valid, error = verifier.verify_copy(source, destination)

        if is_valid:
            print(f"Verification PASSED: {destination}")
        else:
            print(f"Verification FAILED: {error}")

        return is_valid


# ============================================================================
# EXAMPLE 9: Operation History
# ============================================================================

def example_9_operation_history():
    """Load and display operation history"""
    from operations.manager import OperationsManager
    from pathlib import Path

    def show_history():
        """Display operation history"""

        history_file = Path.home() / ".smart_search" / "operations_history.json"

        manager = OperationsManager(
            history_file=str(history_file)
        )

        try:
            # Get all operations (including history)
            all_ops = manager.get_all_operations()

            print(f"Total operations: {len(all_ops)}")

            for op in all_ops:
                print(f"\n{op.operation_type.value.upper()}: {op.operation_id}")
                print(f"  Status: {op.status.value}")
                print(f"  Files: {op.total_files}")
                print(f"  Created: {op.created_at}")
                if op.completed_at:
                    duration = (op.completed_at - op.started_at).total_seconds()
                    print(f"  Duration: {duration:.1f}s")
                if op.error:
                    print(f"  Error: {op.error}")

        finally:
            manager.shutdown()


# ============================================================================
# EXAMPLE 10: Pause/Resume Operation
# ============================================================================

def example_10_pause_resume():
    """Pause and resume operation"""
    import time
    from operations.manager import OperationsManager, OperationStatus

    def pause_resume_demo(operations_manager, operation_id):
        """Demo pause/resume"""

        # Let it run
        time.sleep(2)

        # Pause
        print("Pausing operation...")
        operations_manager.pause_operation(operation_id)

        # Check status
        op = operations_manager.get_operation(operation_id)
        print(f"Status: {op.status.value}")

        # Wait
        time.sleep(2)

        # Resume
        print("Resuming operation...")
        operations_manager.resume_operation(operation_id)

        # Check status
        op = operations_manager.get_operation(operation_id)
        print(f"Status: {op.status.value}")


# ============================================================================
# EXAMPLE 11: Check Disk Space
# ============================================================================

def example_11_check_space():
    """Check available disk space"""
    from operations.copier import FileCopier
    from pathlib import Path

    def check_space_before_copy(files, destination):
        """Check if enough space available"""

        # Calculate total size
        total_size = sum(Path(f).stat().st_size for f in files)

        # Check available space
        is_available, free_bytes = FileCopier.check_space_available(
            destination,
            total_size
        )

        gb_required = total_size / (1024 ** 3)
        gb_free = free_bytes / (1024 ** 3)

        print(f"Required: {gb_required:.2f} GB")
        print(f"Available: {gb_free:.2f} GB")

        if is_available:
            print("Sufficient space available")
        else:
            print("NOT ENOUGH SPACE!")

        return is_available


# ============================================================================
# EXAMPLE 12: Custom Priority
# ============================================================================

def example_12_priority_queue():
    """Queue operations with different priorities"""
    from operations.manager import OperationPriority

    def queue_with_priority(operations_manager, urgent_files, normal_files, dest):
        """Queue files with different priorities"""
        from pathlib import Path

        # Queue urgent files (CRITICAL priority)
        urgent_dests = [str(Path(dest) / Path(f).name) for f in urgent_files]
        urgent_id = operations_manager.queue_copy(
            source_paths=urgent_files,
            dest_paths=urgent_dests,
            priority=OperationPriority.CRITICAL  # Will run first
        )
        print(f"Urgent operation: {urgent_id}")

        # Queue normal files (NORMAL priority)
        normal_dests = [str(Path(dest) / Path(f).name) for f in normal_files]
        normal_id = operations_manager.queue_copy(
            source_paths=normal_files,
            dest_paths=normal_dests,
            priority=OperationPriority.NORMAL
        )
        print(f"Normal operation: {normal_id}")

        # Urgent will be processed first
        return urgent_id, normal_id


# ============================================================================
# USAGE
# ============================================================================

if __name__ == "__main__":
    print("Operations Panel - Code Examples")
    print("=" * 70)
    print("\nThese examples show common integration patterns.")
    print("Copy the relevant example into your code and adapt as needed.")
    print("\nAvailable examples:")
    print("  1. Basic integration in main window")
    print("  2. Copy files from search results")
    print("  3. Move files with confirmation")
    print("  4. Monitor operation progress")
    print("  5. Copy with custom progress callback")
    print("  6. Batch copy with results")
    print("  7. Optimized move (same/cross volume)")
    print("  8. Verify copied files")
    print("  9. View operation history")
    print(" 10. Pause/resume operations")
    print(" 11. Check disk space before copy")
    print(" 12. Priority queue operations")
    print("\nFor full documentation, see:")
    print("  - OPERATIONS_UI_INTEGRATION.md")
    print("  - OPERATIONS_QUICKSTART.md")
    print("\nTo test the panel:")
    print("  python ui/test_operations_integration.py")

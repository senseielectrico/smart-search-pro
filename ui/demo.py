"""
UI Module Demo - Demonstrates all features
"""

import sys
import random
from datetime import datetime, timedelta
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from .main_window import MainWindow


def generate_sample_results(count: int = 100):
    """Generate sample file results for demonstration"""
    extensions = [
        '.txt', '.pdf', '.docx', '.jpg', '.png', '.mp4',
        '.zip', '.py', '.js', '.html', '.css', '.json'
    ]

    names = [
        'document', 'report', 'photo', 'video', 'archive',
        'code', 'script', 'data', 'backup', 'project'
    ]

    results = []
    base_path = Path.home()

    for i in range(count):
        name = f"{random.choice(names)}_{i}{random.choice(extensions)}"
        path = base_path / "Documents" / name
        size = random.randint(1024, 1024 * 1024 * 10)  # 1KB - 10MB
        modified = datetime.now() - timedelta(days=random.randint(0, 365))

        results.append({
            'name': name,
            'path': str(path),
            'size': size,
            'modified': modified,
        })

    return results


def simulate_search(window: MainWindow):
    """Simulate a search operation with progressive results"""
    print("Simulating search...")

    # Generate results
    results = generate_sample_results(50)

    # Add results progressively
    def add_batch(index=[0]):
        if index[0] < len(results):
            # Add 5 results at a time
            batch = results[index[0]:index[0] + 5]
            for result in batch:
                window.results_panel.add_result(result)

            index[0] += 5

            # Update status
            window.status_label.setText(f"Found {index[0]} files...")

    # Add results with timer (simulate progressive loading)
    timer = QTimer()
    timer.timeout.connect(add_batch)
    timer.start(200)  # Add batch every 200ms

    # Store timer reference to prevent garbage collection
    window._demo_timer = timer


def simulate_duplicates(window: MainWindow):
    """Simulate duplicate file detection"""
    print("Simulating duplicate detection...")

    # Generate duplicate groups
    duplicate_groups = []

    base_path = Path.home() / "Documents"

    for i in range(5):
        size = random.randint(1024, 1024 * 100)
        group = []

        for j in range(random.randint(2, 5)):
            path = base_path / f"duplicate_{i}_copy_{j}.txt"
            modified = datetime.now() - timedelta(days=random.randint(0, 100))

            group.append({
                'name': f"duplicate_{i}_copy_{j}.txt",
                'path': str(path),
                'size': size,
                'modified': modified,
            })

        duplicate_groups.append(group)

    window.duplicates_panel.set_duplicates(duplicate_groups)
    window.results_tabs.setCurrentWidget(window.duplicates_panel)


def simulate_operation(window: MainWindow):
    """Simulate a file operation"""
    print("Simulating file operation...")

    # Add operation
    operation_id = "demo_copy_1"
    window.operations_panel.add_operation(operation_id, "Copying files to backup", 100)

    # Simulate progress
    progress = [0]
    speed_values = []

    def update_progress():
        if progress[0] < 100:
            progress[0] += random.randint(1, 5)
            if progress[0] > 100:
                progress[0] = 100

            # Simulate varying speed
            speed = random.uniform(1024 * 1024 * 2, 1024 * 1024 * 10)  # 2-10 MB/s
            speed_values.append(speed)

            current_file = f"file_{progress[0]}.dat"

            window.operations_panel.update_operation(
                operation_id,
                progress=progress[0],
                current_file=current_file,
                speed=speed
            )

            if progress[0] >= 100:
                from .operations_panel import OperationStatus
                window.operations_panel.set_operation_status(
                    operation_id,
                    OperationStatus.COMPLETED
                )
                operation_timer.stop()

    # Update progress with timer
    operation_timer = QTimer()
    operation_timer.timeout.connect(update_progress)
    operation_timer.start(100)  # Update every 100ms

    # Store timer reference
    window._demo_operation_timer = operation_timer

    # Switch to operations tab
    window.results_tabs.setCurrentWidget(window.operations_panel)


def demo_all_features(window: MainWindow):
    """Run full feature demo"""
    print("\n=== Smart Search Pro UI Demo ===\n")

    # 1. Simulate search after 1 second
    QTimer.singleShot(1000, lambda: simulate_search(window))

    # 2. Simulate duplicates after 5 seconds
    QTimer.singleShot(5000, lambda: simulate_duplicates(window))

    # 3. Simulate operation after 8 seconds
    QTimer.singleShot(8000, lambda: simulate_operation(window))

    print("Demo sequence started:")
    print("  1s  - Search results loading")
    print("  5s  - Duplicate detection")
    print("  8s  - File operation")
    print("\nInteract with the UI to explore features!")


def main():
    """Main demo entry point"""
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Smart Search Pro - Demo")

    # Create main window
    window = MainWindow()
    window.setWindowTitle("Smart Search Pro - Feature Demo")
    window.show()

    # Run demo sequence
    demo_all_features(window)

    # Show welcome message
    window.status_label.setText("Demo mode - Features will activate automatically")

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

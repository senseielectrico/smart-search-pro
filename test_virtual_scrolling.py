#!/usr/bin/env python3
"""
Test Virtual Scrolling Performance
Tests the new VirtualTableModel with large datasets
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import random
import time
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel
from PyQt6.QtCore import QTimer

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from ui.results_panel import ResultsPanel


class VirtualScrollingTestWindow(QMainWindow):
    """Test window for virtual scrolling performance"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Virtual Scrolling Performance Test")
        self.setGeometry(100, 100, 1200, 800)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Control panel
        controls = QHBoxLayout()

        # Test buttons
        self.btn_1k = QPushButton("Load 1,000 items")
        self.btn_1k.clicked.connect(lambda: self.load_test_data(1000))
        controls.addWidget(self.btn_1k)

        self.btn_10k = QPushButton("Load 10,000 items")
        self.btn_10k.clicked.connect(lambda: self.load_test_data(10000))
        controls.addWidget(self.btn_10k)

        self.btn_100k = QPushButton("Load 100,000 items")
        self.btn_100k.clicked.connect(lambda: self.load_test_data(100000))
        controls.addWidget(self.btn_100k)

        self.btn_1m = QPushButton("Load 1,000,000 items")
        self.btn_1m.clicked.connect(lambda: self.load_test_data(1000000))
        controls.addWidget(self.btn_1m)

        self.btn_clear = QPushButton("Clear All")
        self.btn_clear.clicked.connect(self.clear_data)
        controls.addWidget(self.btn_clear)

        controls.addStretch()

        layout.addLayout(controls)

        # Status label
        self.status_label = QLabel("Ready. Click a button to load test data.")
        self.status_label.setStyleSheet("padding: 8px; background: #f0f0f0; border-radius: 4px;")
        layout.addWidget(self.status_label)

        # Results panel
        self.results_panel = ResultsPanel()
        layout.addWidget(self.results_panel)

        # Performance metrics
        self.metrics_label = QLabel("")
        self.metrics_label.setStyleSheet("padding: 4px; color: #666; font-size: 9pt;")
        layout.addWidget(self.metrics_label)

    def generate_test_data(self, count: int) -> list:
        """Generate test file data"""
        self.status_label.setText(f"Generating {count:,} test items...")
        QApplication.processEvents()

        extensions = ['.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                     '.zip', '.rar', '.png', '.jpg', '.mp4', '.mp3', '.py', '.js', '.html', '.css']

        paths = [
            r'C:\Users\Documents\Projects',
            r'C:\Users\Documents\Work',
            r'C:\Users\Downloads',
            r'C:\Users\Pictures',
            r'C:\Program Files',
            r'C:\Windows\System32',
            r'D:\Projects\Python',
            r'D:\Projects\React',
            r'D:\Data\Archive',
        ]

        data = []
        start_time = time.time()

        base_date = datetime.now()

        for i in range(count):
            ext = random.choice(extensions)
            base_path = random.choice(paths)
            filename = f"test_file_{i:08d}{ext}"
            full_path = f"{base_path}\\{filename}"

            file_info = {
                'path': full_path,
                'name': filename,
                'size': random.randint(1024, 1024 * 1024 * 100),  # 1KB to 100MB
                'modified': base_date - timedelta(days=random.randint(0, 365)),
            }
            data.append(file_info)

            # Update progress every 10,000 items
            if (i + 1) % 10000 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                self.status_label.setText(
                    f"Generating {count:,} test items... {i+1:,} done ({rate:.0f} items/sec)"
                )
                QApplication.processEvents()

        elapsed = time.time() - start_time
        return data, elapsed

    def load_test_data(self, count: int):
        """Load test data and measure performance"""
        # Generate data
        data, gen_time = self.generate_test_data(count)

        # Load into table
        self.status_label.setText(f"Loading {count:,} items into table...")
        QApplication.processEvents()

        load_start = time.time()
        self.results_panel.set_results(data)
        load_time = time.time() - load_start

        # Update status
        self.status_label.setText(
            f"✓ Loaded {count:,} items successfully!"
        )

        # Update metrics
        metrics_text = (
            f"Generation: {gen_time:.2f}s ({count/gen_time:.0f} items/sec) | "
            f"Load: {load_time:.3f}s ({count/load_time:.0f} items/sec) | "
            f"Total: {gen_time + load_time:.2f}s | "
            f"Memory: ~{count * 0.0001:.1f}MB"
        )
        self.metrics_label.setText(metrics_text)

    def clear_data(self):
        """Clear all data"""
        self.results_panel.clear_results()
        self.status_label.setText("Cleared all data.")
        self.metrics_label.setText("")


def run_automated_tests():
    """Run automated performance tests"""
    app = QApplication(sys.argv)
    window = VirtualScrollingTestWindow()
    window.show()

    print("\n" + "="*80)
    print("VIRTUAL SCROLLING PERFORMANCE TEST")
    print("="*80)

    # Test 1: 1,000 items
    print("\nTest 1: 1,000 items")
    data, gen_time = window.generate_test_data(1000)
    load_start = time.time()
    window.results_panel.set_results(data)
    load_time = time.time() - load_start
    print(f"  Generation: {gen_time:.3f}s")
    print(f"  Load: {load_time:.3f}s")
    print(f"  Total: {gen_time + load_time:.3f}s")
    QApplication.processEvents()
    time.sleep(0.5)

    # Test 2: 10,000 items
    print("\nTest 2: 10,000 items")
    data, gen_time = window.generate_test_data(10000)
    load_start = time.time()
    window.results_panel.set_results(data)
    load_time = time.time() - load_start
    print(f"  Generation: {gen_time:.3f}s")
    print(f"  Load: {load_time:.3f}s")
    print(f"  Total: {gen_time + load_time:.3f}s")
    QApplication.processEvents()
    time.sleep(0.5)

    # Test 3: 100,000 items
    print("\nTest 3: 100,000 items")
    data, gen_time = window.generate_test_data(100000)
    load_start = time.time()
    window.results_panel.set_results(data)
    load_time = time.time() - load_start
    print(f"  Generation: {gen_time:.3f}s")
    print(f"  Load: {load_time:.3f}s")
    print(f"  Total: {gen_time + load_time:.3f}s")
    QApplication.processEvents()
    time.sleep(0.5)

    # Test scrolling performance
    print("\nTest 4: Scrolling performance with 100,000 items")
    scroll_times = []
    for i in range(5):
        scroll_start = time.time()
        # Scroll to different positions
        window.results_panel.table.scrollTo(
            window.results_panel.model.index(i * 20000, 0)
        )
        QApplication.processEvents()
        scroll_time = time.time() - scroll_start
        scroll_times.append(scroll_time)
        print(f"  Scroll {i+1}: {scroll_time:.3f}s")
        time.sleep(0.1)

    avg_scroll = sum(scroll_times) / len(scroll_times)
    print(f"  Average scroll time: {avg_scroll:.3f}s")

    # Test sorting performance
    print("\nTest 5: Sorting performance with 100,000 items")
    sort_start = time.time()
    window.results_panel.model.sort(2, 1)  # Sort by size, descending
    QApplication.processEvents()
    sort_time = time.time() - sort_start
    print(f"  Sort time: {sort_time:.3f}s")

    print("\n" + "="*80)
    print("All tests completed! Window will remain open for manual testing.")
    print("="*80 + "\n")

    sys.exit(app.exec())


def main():
    """Main entry point"""
    if "--auto" in sys.argv:
        run_automated_tests()
    else:
        app = QApplication(sys.argv)
        window = VirtualScrollingTestWindow()
        window.show()
        sys.exit(app.exec())


if __name__ == '__main__':
    main()

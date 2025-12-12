#!/usr/bin/env python3
"""
Unit tests for instant search functionality

Tests debouncing, cancellation, and thread safety.
"""

import sys
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QEventLoop
from PyQt6.QtTest import QTest

# Ensure QApplication exists
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.search_panel import SearchPanel
from ui.main_window import MainWindow, SearchWorker


class TestSearchPanel(unittest.TestCase):
    """Test SearchPanel instant search features"""

    def setUp(self):
        """Create SearchPanel instance"""
        self.panel = SearchPanel()

    def tearDown(self):
        """Cleanup"""
        self.panel.deleteLater()

    def test_debounce_timer_initialization(self):
        """Test debounce timer is created correctly"""
        self.assertIsNotNone(self.panel.search_debounce_timer)
        self.assertTrue(self.panel.search_debounce_timer.isSingleShot())

    def test_debounce_delay_configured(self):
        """Test debounce delay is set"""
        self.assertEqual(self.panel.DEBOUNCE_DELAY_MS, 200)

    def test_instant_search_signal_exists(self):
        """Test instant search signal is defined"""
        self.assertTrue(hasattr(self.panel, 'instant_search_requested'))

    def test_search_status_methods(self):
        """Test search status indicator methods"""
        # Initially not searching
        self.assertFalse(self.panel.is_searching)

        # Set to searching
        self.panel._set_searching_status(True)
        self.assertTrue(self.panel.is_searching)
        self.assertTrue(self.panel.search_status_label.isVisible())

        # Set to not searching
        self.panel._set_searching_status(False)
        self.assertFalse(self.panel.is_searching)
        self.assertFalse(self.panel.search_status_label.isVisible())

    def test_text_change_starts_timer(self):
        """Test that typing starts debounce timer"""
        # Simulate typing
        self.panel.search_input.setText("test")

        # Timer should be active
        self.assertTrue(self.panel.search_debounce_timer.isActive())

    def test_empty_text_stops_timer(self):
        """Test that clearing text stops timer"""
        # Start timer
        self.panel.search_input.setText("test")
        self.assertTrue(self.panel.search_debounce_timer.isActive())

        # Clear text
        self.panel.search_input.setText("")

        # Timer should stop
        self.assertFalse(self.panel.search_debounce_timer.isActive())

    def test_debounce_triggers_instant_search(self):
        """Test that debounce timer triggers instant search"""
        # Connect signal spy
        signal_emitted = []

        def on_instant_search(params):
            signal_emitted.append(params)

        self.panel.instant_search_requested.connect(on_instant_search)

        # Type text
        self.panel.search_input.setText("test query")

        # Wait for debounce (200ms + margin)
        QTest.qWait(300)

        # Signal should be emitted
        self.assertEqual(len(signal_emitted), 1)
        self.assertEqual(signal_emitted[0]['query'], "test query")
        self.assertTrue(signal_emitted[0]['instant'])

    def test_rapid_typing_cancels_previous(self):
        """Test that rapid typing cancels previous timers"""
        signal_count = []

        def on_instant_search(params):
            signal_count.append(params)

        self.panel.instant_search_requested.connect(on_instant_search)

        # Type rapidly
        self.panel.search_input.setText("a")
        QTest.qWait(50)  # Less than debounce
        self.panel.search_input.setText("ab")
        QTest.qWait(50)
        self.panel.search_input.setText("abc")
        QTest.qWait(50)
        self.panel.search_input.setText("abcd")

        # Wait for final debounce
        QTest.qWait(250)

        # Should only emit once with final text
        self.assertEqual(len(signal_count), 1)
        self.assertEqual(signal_count[0]['query'], "abcd")

    def test_search_complete_clears_status(self):
        """Test that search complete clears searching status"""
        # Set searching
        self.panel._set_searching_status(True)
        self.assertTrue(self.panel.is_searching)

        # Complete search
        self.panel.set_search_complete()
        self.assertFalse(self.panel.is_searching)


class TestSearchWorker(unittest.TestCase):
    """Test SearchWorker thread"""

    def setUp(self):
        """Create SearchWorker instance"""
        self.worker = SearchWorker(search_engine=None)

    def tearDown(self):
        """Cleanup"""
        if self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()
        self.worker.deleteLater()

    def test_worker_initialization(self):
        """Test worker is created correctly"""
        self.assertIsNotNone(self.worker)
        self.assertFalse(self.worker.isRunning())
        self.assertFalse(self.worker.is_cancelled)

    def test_set_params(self):
        """Test setting search parameters"""
        params = {'query': 'test', 'max_results': 100}
        self.worker.set_params(params)

        self.assertEqual(self.worker.params, params)
        self.assertFalse(self.worker.is_cancelled)

    def test_cancel_flag(self):
        """Test cancellation flag"""
        self.assertFalse(self.worker.is_cancelled)

        self.worker.cancel()
        self.assertTrue(self.worker.is_cancelled)

    def test_worker_runs_with_params(self):
        """Test worker executes with parameters"""
        signals_received = {'complete': False, 'results': None}

        def on_complete():
            signals_received['complete'] = True

        def on_results(results):
            signals_received['results'] = results

        self.worker.search_complete.connect(on_complete)
        self.worker.results_ready.connect(on_results)

        # Set params and start
        self.worker.set_params({'query': 'test'})
        self.worker.start()

        # Wait for completion (max 2 seconds)
        self.worker.wait(2000)

        # Should receive signals
        self.assertTrue(signals_received['complete'])
        # Mock mode returns empty list
        self.assertEqual(signals_received['results'], [])

    def test_worker_cancellation(self):
        """Test worker can be cancelled"""
        # Start worker
        self.worker.set_params({'query': 'test'})
        self.worker.start()

        # Cancel immediately
        self.worker.cancel()

        # Wait for termination
        self.worker.wait(1000)

        # Should not be running
        self.assertFalse(self.worker.isRunning())


class TestMainWindowIntegration(unittest.TestCase):
    """Test MainWindow search integration"""

    def setUp(self):
        """Create MainWindow instance"""
        self.window = MainWindow()

    def tearDown(self):
        """Cleanup"""
        if self.window.search_worker.isRunning():
            self.window.search_worker.cancel()
            self.window.search_worker.wait()
        self.window.deleteLater()

    def test_search_worker_initialized(self):
        """Test search worker is created"""
        self.assertIsNotNone(self.window.search_worker)

    def test_signals_connected(self):
        """Test signals are connected"""
        # Verify search panel signals connected
        self.assertTrue(
            self.window.search_panel.search_requested.receivers() > 0
        )
        self.assertTrue(
            self.window.search_panel.instant_search_requested.receivers() > 0
        )

    def test_set_search_engine(self):
        """Test setting search engine"""
        mock_engine = MagicMock()
        self.window.set_search_engine(mock_engine)

        self.assertEqual(self.window.search_engine, mock_engine)
        self.assertEqual(self.window.search_worker.search_engine, mock_engine)

    def test_perform_instant_search(self):
        """Test instant search execution"""
        params = {'query': 'test', 'instant': True}

        # Execute instant search
        self.window._perform_instant_search(params)

        # Worker should be running
        QTest.qWait(100)  # Give it time to start

        # Wait for completion
        self.window.search_worker.wait(2000)

        # Status should update
        self.assertIn("completed", self.window.status_label.text().lower())


class TestPerformance(unittest.TestCase):
    """Performance tests for instant search"""

    def setUp(self):
        """Create test instance"""
        self.panel = SearchPanel()

    def tearDown(self):
        """Cleanup"""
        self.panel.deleteLater()

    def test_debounce_timing(self):
        """Test debounce timing accuracy"""
        start_time = time.time()
        signals = []

        def on_search(params):
            signals.append(time.time())

        self.panel.instant_search_requested.connect(on_search)

        # Trigger search
        self.panel.search_input.setText("test")

        # Wait for signal
        QTest.qWait(300)

        # Check timing
        if signals:
            elapsed = (signals[0] - start_time) * 1000  # Convert to ms
            # Should be close to 200ms (within 100ms tolerance)
            self.assertGreater(elapsed, 150)
            self.assertLess(elapsed, 350)

    def test_rapid_typing_performance(self):
        """Test performance with rapid typing"""
        signals = []

        def on_search(params):
            signals.append(params)

        self.panel.instant_search_requested.connect(on_search)

        # Simulate rapid typing
        start_time = time.time()
        for i in range(10):
            self.panel.search_input.setText(f"query{i}")
            QTest.qWait(30)  # Type every 30ms

        # Wait for final debounce
        QTest.qWait(300)

        elapsed = time.time() - start_time

        # Should complete quickly despite rapid typing
        self.assertLess(elapsed, 2.0)  # Less than 2 seconds total

        # Should only emit once or twice (not 10 times)
        self.assertLessEqual(len(signals), 3)


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSearchPanel))
    suite.addTests(loader.loadTestsFromTestCase(TestSearchWorker))
    suite.addTests(loader.loadTestsFromTestCase(TestMainWindowIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    print("=" * 60)
    print("Instant Search Test Suite")
    print("=" * 60)
    print()

    success = run_tests()

    print()
    print("=" * 60)
    if success:
        print("ALL TESTS PASSED ✓")
    else:
        print("SOME TESTS FAILED ✗")
    print("=" * 60)

    sys.exit(0 if success else 1)

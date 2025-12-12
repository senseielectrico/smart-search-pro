"""
Test script for Smart Search Pro hotkey system.

Tests:
1. Hotkey manager initialization
2. Registration of global and local hotkeys
3. Conflict detection
4. Configuration persistence
5. Qt integration
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt

from system.hotkeys import HotkeyManager, ModifierKeys, VirtualKeys


class TestWindow(QMainWindow):
    """Test window for hotkey demonstration."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hotkey System Test")
        self.setGeometry(100, 100, 600, 400)

        # Create hotkey manager
        config_file = Path.home() / ".smart_search" / "hotkeys_test.json"
        self.hotkey_manager = HotkeyManager(config_file=config_file)

        self._init_ui()
        self._setup_hotkeys()

        # Install Qt event filter
        self.hotkey_manager.install_qt_filter()

    def _init_ui(self):
        """Initialize UI."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Status label
        self.status_label = QLabel("Press hotkeys to test...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14pt; padding: 20px;")
        layout.addWidget(self.status_label)

        # Test buttons
        btn1 = QPushButton("Test Action 1 (Ctrl+1)")
        btn1.clicked.connect(lambda: self._on_action("Action 1"))
        layout.addWidget(btn1)

        btn2 = QPushButton("Test Action 2 (Ctrl+2)")
        btn2.clicked.connect(lambda: self._on_action("Action 2"))
        layout.addWidget(btn2)

        btn3 = QPushButton("Toggle Window (Ctrl+Shift+T)")
        btn3.clicked.connect(self._toggle_window)
        layout.addWidget(btn3)

        # Info
        info = QLabel(
            "Registered Hotkeys:\n"
            "- Ctrl+1: Test Action 1\n"
            "- Ctrl+2: Test Action 2\n"
            "- Ctrl+Shift+T: Toggle Window (Global)\n"
            "- F5: Refresh\n"
            "- Ctrl+S: Save Config"
        )
        info.setStyleSheet("color: gray; padding: 10px;")
        layout.addWidget(info)

        layout.addStretch()

    def _setup_hotkeys(self):
        """Setup test hotkeys."""
        # Test action 1
        self.hotkey_manager.register(
            "test_action_1",
            ModifierKeys.CTRL,
            VirtualKeys.number(1),
            lambda: self._on_action("Action 1 (Hotkey)"),
            "Test Action 1",
            is_global=False
        )

        # Test action 2
        self.hotkey_manager.register(
            "test_action_2",
            ModifierKeys.CTRL,
            VirtualKeys.number(2),
            lambda: self._on_action("Action 2 (Hotkey)"),
            "Test Action 2",
            is_global=False
        )

        # Toggle window (global)
        success = self.hotkey_manager.register(
            "toggle_window",
            ModifierKeys.CTRL | ModifierKeys.SHIFT,
            VirtualKeys.letter('T'),
            self._toggle_window,
            "Toggle Window Visibility",
            is_global=True
        )

        if success:
            logger.info("Global hotkey registered successfully")
        else:
            logger.warning("Failed to register global hotkey (may be in use)")

        # Refresh action
        self.hotkey_manager.register(
            "refresh",
            0,  # No modifiers
            VirtualKeys.VK_F5,
            lambda: self._on_action("Refresh"),
            "Refresh",
            is_global=False
        )

        # Save config
        self.hotkey_manager.register(
            "save_config",
            ModifierKeys.CTRL,
            VirtualKeys.letter('S'),
            self._save_config,
            "Save Configuration",
            is_global=False
        )

        # Test conflict detection
        conflict = self.hotkey_manager.check_conflict(
            ModifierKeys.CTRL,
            VirtualKeys.number(1)
        )
        if conflict:
            logger.info(f"Conflict detected (expected): {conflict}")

        # List all hotkeys
        all_hotkeys = self.hotkey_manager.get_all_hotkeys()
        logger.info(f"Registered {len(all_hotkeys)} hotkeys:")
        for name, key_combo, description in all_hotkeys:
            logger.info(f"  {name}: {key_combo} - {description}")

    def _on_action(self, action_name: str):
        """Handle test action."""
        self.status_label.setText(f"Triggered: {action_name}")
        logger.info(f"Action triggered: {action_name}")

    def _toggle_window(self):
        """Toggle window visibility."""
        if self.isVisible() and not self.isMinimized():
            self.hide()
            logger.info("Window hidden")
        else:
            self.show()
            self.raise_()
            self.activateWindow()
            logger.info("Window shown")

    def _save_config(self):
        """Save hotkey configuration."""
        success = self.hotkey_manager.save_config()
        if success:
            self.status_label.setText("Configuration saved!")
            logger.info("Configuration saved")
        else:
            self.status_label.setText("Failed to save configuration")
            logger.error("Failed to save configuration")

    def closeEvent(self, event):
        """Handle close event."""
        logger.info("Cleaning up hotkeys...")
        self.hotkey_manager.cleanup()
        event.accept()


def run_tests():
    """Run hotkey system tests."""
    logger.info("=" * 60)
    logger.info("Starting Hotkey System Tests")
    logger.info("=" * 60)

    # Test 1: Manager initialization
    logger.info("\nTest 1: Manager Initialization")
    manager = HotkeyManager()
    assert manager is not None
    logger.info("✓ Manager initialized successfully")

    # Test 2: Registration
    logger.info("\nTest 2: Hotkey Registration")

    def test_callback():
        logger.info("Test callback executed")

    success = manager.register(
        "test_hotkey",
        ModifierKeys.CTRL | ModifierKeys.SHIFT,
        VirtualKeys.letter('X'),
        test_callback,
        "Test hotkey",
        is_global=False
    )
    assert success
    logger.info("✓ Hotkey registered successfully")

    # Test 3: Conflict detection
    logger.info("\nTest 3: Conflict Detection")
    conflict = manager.check_conflict(
        ModifierKeys.CTRL | ModifierKeys.SHIFT,
        VirtualKeys.letter('X')
    )
    assert conflict == "test_hotkey"
    logger.info(f"✓ Conflict detected: {conflict}")

    # Test 4: List hotkeys
    logger.info("\nTest 4: List Hotkeys")
    hotkeys = manager.get_all_hotkeys()
    assert len(hotkeys) > 0
    logger.info(f"✓ Found {len(hotkeys)} registered hotkeys")

    # Test 5: Configuration persistence
    logger.info("\nTest 5: Configuration Persistence")
    test_config = Path.home() / ".smart_search" / "hotkeys_test.json"
    manager.config_file = test_config
    success = manager.save_config()
    assert success
    logger.info(f"✓ Configuration saved to {test_config}")

    # Cleanup
    manager.cleanup()
    logger.info("\n✓ All tests passed!")

    logger.info("=" * 60)
    logger.info("Tests Complete - Starting Interactive Test")
    logger.info("=" * 60)


def main():
    """Main entry point."""
    # Run automated tests
    run_tests()

    # Start interactive test
    app = QApplication(sys.argv)
    app.setApplicationName("Hotkey Test")

    window = TestWindow()
    window.show()

    logger.info("\nInteractive test window opened.")
    logger.info("Try the following:")
    logger.info("1. Press Ctrl+1 or Ctrl+2 to trigger actions")
    logger.info("2. Press F5 to refresh")
    logger.info("3. Press Ctrl+S to save config")
    logger.info("4. Press Ctrl+Shift+T to toggle window (global hotkey)")
    logger.info("5. Close the window when done")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

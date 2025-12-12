"""
Vault Unlock Dialog - Secure Password Entry
Secure unlock interface with anti-keylogger features

Features:
- Virtual keyboard option
- Password visibility toggle
- Failed attempts tracking
- Lockout mechanism
- Duress password support
"""

import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QWidget, QGridLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon


class VirtualKeyboard(QWidget):
    """Virtual keyboard to prevent keyloggers"""

    key_pressed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Setup virtual keyboard layout"""
        layout = QGridLayout(self)
        layout.setSpacing(5)

        # Define keyboard layout
        keys = [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
            ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
            ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'],
            ['z', 'x', 'c', 'v', 'b', 'n', 'm'],
            ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')'],
            ['-', '_', '=', '+', '[', ']', '{', '}'],
        ]

        # Create buttons
        for row, key_row in enumerate(keys):
            for col, key in enumerate(key_row):
                btn = QPushButton(key)
                btn.setMinimumSize(40, 40)
                btn.setFont(QFont('Segoe UI', 10, QFont.Weight.Bold))
                btn.clicked.connect(lambda checked, k=key: self.key_pressed.emit(k))
                layout.addWidget(btn, row, col)

        # Special keys
        backspace_btn = QPushButton('←')
        backspace_btn.setMinimumSize(80, 40)
        backspace_btn.clicked.connect(lambda: self.key_pressed.emit('BACKSPACE'))
        layout.addWidget(backspace_btn, 6, 0, 1, 2)

        space_btn = QPushButton('Space')
        space_btn.setMinimumSize(200, 40)
        space_btn.clicked.connect(lambda: self.key_pressed.emit(' '))
        layout.addWidget(space_btn, 6, 2, 1, 4)

        clear_btn = QPushButton('Clear')
        clear_btn.setMinimumSize(80, 40)
        clear_btn.clicked.connect(lambda: self.key_pressed.emit('CLEAR'))
        layout.addWidget(clear_btn, 6, 6, 1, 2)


class VaultUnlockDialog(QDialog):
    """
    Secure vault unlock dialog

    Features:
    - Password entry with visibility toggle
    - Virtual keyboard option
    - Failed attempts counter
    - Lockout after max attempts
    - Duress password support
    """

    def __init__(self, max_attempts: int = 5, lockout_duration: int = 300, parent=None):
        super().__init__(parent)

        self.max_attempts = max_attempts
        self.lockout_duration = lockout_duration
        self.failed_attempts = 0
        self.lockout_until = 0
        self.is_duress = False
        self.password = ""

        self._setup_ui()
        self._setup_timer()

    def _setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("Unlock Vault")
        self.setModal(True)
        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Header
        header_label = QLabel("Secure Vault")
        header_label.setFont(QFont('Segoe UI', 16, QFont.Weight.Bold))
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header_label)

        # Status label
        self.status_label = QLabel("Enter password to unlock")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Password input
        password_layout = QHBoxLayout()

        password_label = QLabel("Password:")
        password_label.setMinimumWidth(80)
        password_layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter password...")
        self.password_input.returnPressed.connect(self._on_unlock)
        password_layout.addWidget(self.password_input)

        self.show_password_btn = QPushButton("👁")
        self.show_password_btn.setCheckable(True)
        self.show_password_btn.setMaximumWidth(40)
        self.show_password_btn.toggled.connect(self._toggle_password_visibility)
        password_layout.addWidget(self.show_password_btn)

        layout.addLayout(password_layout)

        # Failed attempts counter
        self.attempts_label = QLabel("")
        self.attempts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.attempts_label.setStyleSheet("color: #d32f2f;")
        layout.addWidget(self.attempts_label)

        # Virtual keyboard toggle
        self.virtual_kb_checkbox = QCheckBox("Use Virtual Keyboard (anti-keylogger)")
        self.virtual_kb_checkbox.toggled.connect(self._toggle_virtual_keyboard)
        layout.addWidget(self.virtual_kb_checkbox)

        # Virtual keyboard
        self.virtual_keyboard = VirtualKeyboard()
        self.virtual_keyboard.key_pressed.connect(self._on_virtual_key)
        self.virtual_keyboard.hide()
        layout.addWidget(self.virtual_keyboard)

        # Buttons
        button_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        button_layout.addStretch()

        self.unlock_btn = QPushButton("Unlock")
        self.unlock_btn.setDefault(True)
        self.unlock_btn.clicked.connect(self._on_unlock)
        button_layout.addWidget(self.unlock_btn)

        layout.addLayout(button_layout)

        # Styling
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #0078d4;
            }
            QPushButton {
                background-color: #0078d4;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1084d8;
            }
            QPushButton:pressed {
                background-color: #006cbd;
            }
            QPushButton:disabled {
                background-color: #3d3d3d;
                color: #808080;
            }
            QCheckBox {
                color: #ffffff;
            }
        """)

    def _setup_timer(self):
        """Setup lockout timer"""
        self.lockout_timer = QTimer()
        self.lockout_timer.timeout.connect(self._update_lockout)
        self.lockout_timer.setInterval(1000)  # 1 second

    def _toggle_password_visibility(self, checked: bool):
        """Toggle password visibility"""
        if checked:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_password_btn.setText("🔒")
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_password_btn.setText("👁")

    def _toggle_virtual_keyboard(self, checked: bool):
        """Toggle virtual keyboard"""
        if checked:
            self.virtual_keyboard.show()
            self.password_input.setReadOnly(True)
            self.adjustSize()
        else:
            self.virtual_keyboard.hide()
            self.password_input.setReadOnly(False)
            self.password_input.setFocus()
            self.adjustSize()

    def _on_virtual_key(self, key: str):
        """Handle virtual keyboard key press"""
        if key == 'BACKSPACE':
            current = self.password_input.text()
            self.password_input.setText(current[:-1])
        elif key == 'CLEAR':
            self.password_input.clear()
        else:
            current = self.password_input.text()
            self.password_input.setText(current + key)

    def _on_unlock(self):
        """Handle unlock button click"""
        import time

        # Check lockout
        if time.time() < self.lockout_until:
            remaining = int(self.lockout_until - time.time())
            self.status_label.setText(f"Locked out. Try again in {remaining} seconds")
            self.status_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
            return

        password = self.password_input.text()

        if not password:
            self.status_label.setText("Please enter password")
            self.status_label.setStyleSheet("color: #ff9800;")
            return

        self.password = password
        self.accept()

    def failed_attempt(self):
        """Record failed unlock attempt"""
        import time

        self.failed_attempts += 1

        if self.failed_attempts >= self.max_attempts:
            # Lock out
            self.lockout_until = time.time() + self.lockout_duration
            self.failed_attempts = 0

            self.status_label.setText(f"Too many failed attempts. Locked for {self.lockout_duration // 60} minutes")
            self.status_label.setStyleSheet("color: #d32f2f; font-weight: bold;")

            self.password_input.setEnabled(False)
            self.unlock_btn.setEnabled(False)

            self.lockout_timer.start()

        else:
            remaining = self.max_attempts - self.failed_attempts
            self.attempts_label.setText(f"Failed attempts: {self.failed_attempts} / {self.max_attempts} (Remaining: {remaining})")
            self.status_label.setText("Invalid password. Try again")
            self.status_label.setStyleSheet("color: #d32f2f;")

        self.password_input.clear()
        self.password_input.setFocus()

    def _update_lockout(self):
        """Update lockout timer"""
        import time

        if time.time() >= self.lockout_until:
            # Lockout expired
            self.lockout_timer.stop()
            self.password_input.setEnabled(True)
            self.unlock_btn.setEnabled(True)
            self.status_label.setText("Enter password to unlock")
            self.status_label.setStyleSheet("")
        else:
            remaining = int(self.lockout_until - time.time())
            self.status_label.setText(f"Locked out. Try again in {remaining} seconds")

    def get_password(self) -> str:
        """Get entered password"""
        return self.password

    def is_duress_unlock(self) -> bool:
        """Check if duress password was used"""
        return self.is_duress

    @staticmethod
    def get_unlock_password(max_attempts: int = 5, lockout_duration: int = 300, parent=None) -> tuple:
        """
        Show unlock dialog and get password

        Returns:
            Tuple of (password, is_duress, accepted)
        """
        dialog = VaultUnlockDialog(max_attempts, lockout_duration, parent)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            return (dialog.get_password(), dialog.is_duress_unlock(), True)
        else:
            return ("", False, False)


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    password, is_duress, accepted = VaultUnlockDialog.get_unlock_password()

    if accepted:
        print(f"Password: {password}")
        print(f"Duress: {is_duress}")
    else:
        print("Cancelled")

    sys.exit()

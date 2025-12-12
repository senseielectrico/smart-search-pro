"""
Admin Console Widget for Smart Search Pro.

Provides an embedded terminal widget in PyQt6 with PowerShell/CMD support,
command history, auto-complete, and administrator elevation.
"""

import os
import sys
import logging
from typing import List, Optional, Dict
from pathlib import Path
from collections import deque

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QComboBox, QLabel, QTabWidget, QToolBar,
    QMessageBox, QFileDialog, QMenu, QSplitter
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QThread, QTimer, pyqtSlot, QSize
)
from PyQt6.QtGui import (
    QTextCursor, QFont, QColor, QTextCharFormat, QKeySequence,
    QAction, QIcon, QPalette
)

# Import system modules
try:
    from system.admin_console import AdminConsoleManager, ConsoleConfig, ConsoleType, ConsoleSession
    from system.elevation import ElevationManager, ShowWindow
    from system.privilege_manager import PrivilegeManager
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from system.admin_console import AdminConsoleManager, ConsoleConfig, ConsoleType, ConsoleSession
    from system.elevation import ElevationManager, ShowWindow
    from system.privilege_manager import PrivilegeManager

logger = logging.getLogger(__name__)


class CommandExecutor(QThread):
    """Worker thread for executing commands."""

    # Signals
    output_ready = pyqtSignal(str)  # stdout
    error_ready = pyqtSignal(str)   # stderr
    execution_complete = pyqtSignal(bool)  # success

    def __init__(self, parent=None):
        super().__init__(parent)
        self.console_manager = AdminConsoleManager()
        self.commands = []
        self.config = None

    def set_commands(self, commands: List[str], config: ConsoleConfig):
        """Set commands to execute."""
        self.commands = commands
        self.config = config

    def run(self):
        """Execute commands in background."""
        try:
            success, stdout, stderr = self.console_manager.execute_batch_commands(
                self.commands,
                self.config
            )

            if stdout:
                self.output_ready.emit(stdout)
            if stderr:
                self.error_ready.emit(stderr)

            self.execution_complete.emit(success)

        except Exception as e:
            self.error_ready.emit(f"Execution error: {e}")
            self.execution_complete.emit(False)


class ConsoleOutputWidget(QTextEdit):
    """Terminal-like output widget with syntax highlighting."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Configure as read-only terminal
        self.setReadOnly(True)
        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        # Terminal font
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

        # Dark terminal colors
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
            }
        """)

        # Text formats for syntax highlighting
        self.formats = {
            'normal': self._create_format('#d4d4d4'),
            'error': self._create_format('#f48771'),
            'warning': self._create_format('#dcdcaa'),
            'success': self._create_format('#4ec9b0'),
            'prompt': self._create_format('#569cd6', bold=True),
            'command': self._create_format('#9cdcfe'),
        }

    def _create_format(self, color: str, bold: bool = False) -> QTextCharFormat:
        """Create text format."""
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        return fmt

    def append_text(self, text: str, format_name: str = 'normal'):
        """Append text with specific format."""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text, self.formats.get(format_name, self.formats['normal']))
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def append_prompt(self, prompt: str = "PS> "):
        """Append command prompt."""
        self.append_text(prompt, 'prompt')

    def append_command(self, command: str):
        """Append command text."""
        self.append_text(command + '\n', 'command')

    def append_output(self, text: str):
        """Append command output."""
        self.append_text(text + '\n', 'normal')

    def append_error(self, text: str):
        """Append error text."""
        self.append_text(text + '\n', 'error')

    def clear_output(self):
        """Clear all output."""
        self.clear()


class ConsoleInputWidget(QLineEdit):
    """Command input widget with history and auto-complete."""

    # Signals
    command_submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Command history
        self.history: deque = deque(maxlen=100)
        self.history_index = -1
        self.current_command = ""

        # Auto-complete suggestions
        self.suggestions: List[str] = [
            # PowerShell cmdlets
            'Get-ChildItem', 'Get-Content', 'Get-Process', 'Get-Service',
            'Set-Location', 'Remove-Item', 'Copy-Item', 'Move-Item',
            'New-Item', 'Test-Path', 'Select-String', 'Where-Object',
            'ForEach-Object', 'Sort-Object', 'Measure-Object',
            # Common commands
            'dir', 'cd', 'ls', 'pwd', 'cat', 'rm', 'cp', 'mv',
            'mkdir', 'rmdir', 'type', 'more', 'find', 'grep',
            'echo', 'cls', 'clear', 'exit', 'help',
        ]

        # Styling
        self.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                padding: 5px;
                font-family: Consolas;
                font-size: 10pt;
            }
        """)

        # Connect signals
        self.returnPressed.connect(self._on_return_pressed)

    def keyPressEvent(self, event):
        """Handle key press for history navigation."""
        key = event.key()

        if key == Qt.Key.Key_Up:
            self._history_up()
        elif key == Qt.Key.Key_Down:
            self._history_down()
        elif key == Qt.Key.Key_Tab:
            self._auto_complete()
            event.accept()
            return
        else:
            # Reset history navigation
            if self.history_index != -1 and key not in (Qt.Key.Key_Up, Qt.Key.Key_Down):
                self.history_index = -1

        super().keyPressEvent(event)

    def _on_return_pressed(self):
        """Handle return key press."""
        command = self.text().strip()
        if command:
            # Add to history
            self.history.append(command)
            self.history_index = -1

            # Emit signal
            self.command_submitted.emit(command)

            # Clear input
            self.clear()

    def _history_up(self):
        """Navigate up in command history."""
        if not self.history:
            return

        # Save current command if at bottom
        if self.history_index == -1:
            self.current_command = self.text()

        # Move up in history
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.setText(self.history[-(self.history_index + 1)])

    def _history_down(self):
        """Navigate down in command history."""
        if self.history_index == -1:
            return

        # Move down in history
        self.history_index -= 1

        if self.history_index == -1:
            # Restore current command
            self.setText(self.current_command)
        else:
            self.setText(self.history[-(self.history_index + 1)])

    def _auto_complete(self):
        """Auto-complete command."""
        text = self.text()
        if not text:
            return

        # Find matching suggestions
        matches = [s for s in self.suggestions if s.lower().startswith(text.lower())]

        if matches:
            # Use first match
            self.setText(matches[0])


class AdminConsoleTab(QWidget):
    """Single console tab."""

    # Signals
    title_changed = pyqtSignal(str)

    def __init__(self, console_type: ConsoleType = ConsoleType.POWERSHELL, parent=None):
        super().__init__(parent)

        self.console_type = console_type
        self.console_manager = AdminConsoleManager()
        self.session: Optional[ConsoleSession] = None
        self.executor: Optional[CommandExecutor] = None

        self._init_ui()

    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Output widget
        self.output_widget = ConsoleOutputWidget()
        layout.addWidget(self.output_widget)

        # Input widget
        self.input_widget = ConsoleInputWidget()
        self.input_widget.command_submitted.connect(self._execute_command)
        layout.addWidget(self.input_widget)

        # Show initial prompt
        self._show_prompt()

    def _show_prompt(self):
        """Show command prompt."""
        if self.console_type == ConsoleType.CMD:
            self.output_widget.append_prompt("C:\\> ")
        else:
            self.output_widget.append_prompt("PS> ")

    def _execute_command(self, command: str):
        """Execute command."""
        # Show command in output
        self.output_widget.append_command(command)

        # Handle built-in commands
        if command.lower() in ('cls', 'clear'):
            self.output_widget.clear_output()
            self._show_prompt()
            return
        elif command.lower() == 'exit':
            self.title_changed.emit("Console (closed)")
            self.output_widget.append_output("Console closed.")
            self.input_widget.setEnabled(False)
            return

        # Execute command in background
        self.executor = CommandExecutor()
        self.executor.output_ready.connect(self._on_output)
        self.executor.error_ready.connect(self._on_error)
        self.executor.execution_complete.connect(self._on_complete)

        config = ConsoleConfig(
            console_type=self.console_type,
            capture_output=True,
            working_directory=os.getcwd()
        )

        self.executor.set_commands([command], config)
        self.executor.start()

        # Disable input while executing
        self.input_widget.setEnabled(False)

    @pyqtSlot(str)
    def _on_output(self, text: str):
        """Handle command output."""
        self.output_widget.append_output(text)

    @pyqtSlot(str)
    def _on_error(self, text: str):
        """Handle command error."""
        self.output_widget.append_error(text)

    @pyqtSlot(bool)
    def _on_complete(self, success: bool):
        """Handle execution complete."""
        # Re-enable input
        self.input_widget.setEnabled(True)
        self.input_widget.setFocus()

        # Show prompt
        self._show_prompt()

    def clear(self):
        """Clear console output."""
        self.output_widget.clear_output()
        self._show_prompt()

    def save_output(self, file_path: str):
        """Save console output to file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.output_widget.toPlainText())
            return True
        except Exception as e:
            logger.error(f"Error saving output: {e}")
            return False


class AdminConsoleWidget(QWidget):
    """
    Admin console widget with tabbed interface.

    Features:
    - Multiple console tabs (PowerShell, CMD)
    - Command history with up/down arrows
    - Auto-complete for common commands
    - Run as admin button with UAC shield icon
    - Syntax highlighting for output
    - Copy/paste support
    - Clear and save output options
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.console_manager = AdminConsoleManager()
        self.elevation_manager = ElevationManager()
        self.privilege_manager = PrivilegeManager()

        self._init_ui()

    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)

        # Toolbar
        self._create_toolbar(layout)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        layout.addWidget(self.tab_widget)

        # Add initial tab
        self._add_console_tab(ConsoleType.POWERSHELL)

    def _create_toolbar(self, layout):
        """Create toolbar."""
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))

        # New tab button
        new_ps_action = QAction("New PowerShell", self)
        new_ps_action.triggered.connect(lambda: self._add_console_tab(ConsoleType.POWERSHELL))
        toolbar.addAction(new_ps_action)

        new_cmd_action = QAction("New CMD", self)
        new_cmd_action.triggered.connect(lambda: self._add_console_tab(ConsoleType.CMD))
        toolbar.addAction(new_cmd_action)

        toolbar.addSeparator()

        # Run as admin button
        self.admin_button = QPushButton("Run as Administrator")
        self.admin_button.setToolTip("Launch elevated console with UAC")
        self.admin_button.clicked.connect(self._launch_elevated)
        toolbar.addWidget(self.admin_button)

        # Update admin status
        self._update_admin_status()

        toolbar.addSeparator()

        # Clear button
        clear_action = QAction("Clear", self)
        clear_action.triggered.connect(self._clear_current_console)
        toolbar.addAction(clear_action)

        # Save button
        save_action = QAction("Save Output", self)
        save_action.triggered.connect(self._save_output)
        toolbar.addAction(save_action)

        layout.addWidget(toolbar)

    def _add_console_tab(self, console_type: ConsoleType):
        """Add new console tab."""
        console_tab = AdminConsoleTab(console_type)

        # Set tab title
        title = "PowerShell" if console_type == ConsoleType.POWERSHELL else "CMD"
        index = self.tab_widget.addTab(console_tab, title)
        self.tab_widget.setCurrentIndex(index)

        # Connect title change signal
        console_tab.title_changed.connect(
            lambda t: self.tab_widget.setTabText(self.tab_widget.indexOf(console_tab), t)
        )

    def _close_tab(self, index: int):
        """Close console tab."""
        if self.tab_widget.count() > 1:
            self.tab_widget.removeTab(index)
        else:
            QMessageBox.warning(
                self,
                "Cannot Close",
                "Cannot close the last console tab."
            )

    def _clear_current_console(self):
        """Clear current console output."""
        current = self.tab_widget.currentWidget()
        if isinstance(current, AdminConsoleTab):
            current.clear()

    def _save_output(self):
        """Save current console output to file."""
        current = self.tab_widget.currentWidget()
        if not isinstance(current, AdminConsoleTab):
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Console Output",
            "",
            "Text Files (*.txt);;All Files (*.*)"
        )

        if file_path:
            if current.save_output(file_path):
                QMessageBox.information(
                    self,
                    "Saved",
                    f"Console output saved to:\n{file_path}"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    "Failed to save console output."
                )

    def _launch_elevated(self):
        """Launch elevated console."""
        # Check if already elevated
        if self.elevation_manager.is_elevated():
            QMessageBox.information(
                self,
                "Already Elevated",
                "This application is already running as administrator."
            )
            return

        # Show elevation dialog
        from ui.elevation_dialog import ElevationDialog

        dialog = ElevationDialog(
            operation="Launch Administrator Console",
            description="This will open a new console window with administrator privileges.",
            parent=self
        )

        if dialog.exec() == dialog.DialogCode.Accepted:
            # Launch elevated console
            config = ConsoleConfig(
                console_type=ConsoleType.POWERSHELL,
                elevated=True,
                title="Smart Search Pro - Admin Console (Elevated)"
            )

            session = self.console_manager.launch_console(config)
            if session:
                QMessageBox.information(
                    self,
                    "Console Launched",
                    "Administrator console has been launched in a new window."
                )
            else:
                QMessageBox.critical(
                    self,
                    "Launch Failed",
                    "Failed to launch administrator console."
                )

    def _update_admin_status(self):
        """Update admin status indicator."""
        if self.elevation_manager.is_elevated():
            self.admin_button.setText("Running as Administrator")
            self.admin_button.setEnabled(False)
            self.admin_button.setStyleSheet("color: #4ec9b0; font-weight: bold;")
        else:
            self.admin_button.setText("Run as Administrator")
            self.admin_button.setEnabled(True)


# Example usage
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    widget = AdminConsoleWidget()
    widget.setWindowTitle("Smart Search Pro - Admin Console")
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())

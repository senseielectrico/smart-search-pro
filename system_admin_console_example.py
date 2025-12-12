"""
Admin Console System - Complete Example

Demonstrates all features of the admin console system with practical examples.
"""

import sys
import os
import logging
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QComboBox, QLabel, QMessageBox,
    QDialog, QTabWidget, QGroupBox, QCheckBox, QLineEdit
)
from PyQt6.QtCore import Qt

from system.admin_console import AdminConsoleManager, ConsoleConfig, ConsoleType
from system.privilege_manager import PrivilegeManager, PrivilegeContext
from system.elevation import ElevationManager
from ui.admin_console_widget import AdminConsoleWidget
from ui.elevation_dialog import ElevationDialog, QuickElevationDialog

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class AdminConsoleExampleWindow(QMainWindow):
    """Example window demonstrating admin console features."""

    def __init__(self):
        super().__init__()

        self.console_manager = AdminConsoleManager()
        self.privilege_manager = PrivilegeManager()
        self.elevation_manager = ElevationManager()

        self.setWindowTitle("Admin Console System - Complete Example")
        self.resize(1200, 800)

        self._init_ui()
        self._update_status()

    def _init_ui(self):
        """Initialize UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Create tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: Embedded Console
        tabs.addTab(self._create_console_tab(), "Embedded Console")

        # Tab 2: Command Execution
        tabs.addTab(self._create_execution_tab(), "Execute Commands")

        # Tab 3: Privilege Management
        tabs.addTab(self._create_privilege_tab(), "Privilege Management")

        # Tab 4: Elevation Features
        tabs.addTab(self._create_elevation_tab(), "Elevation Features")

        # Tab 5: Advanced Examples
        tabs.addTab(self._create_advanced_tab(), "Advanced Examples")

        # Status bar
        self.statusBar().showMessage("Ready")

    def _create_console_tab(self):
        """Create embedded console tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Info
        info = QLabel(
            "This is a fully functional embedded PowerShell/CMD console.\n"
            "Features: Command history (Up/Down), Auto-complete (Tab), "
            "Multiple tabs, Syntax highlighting"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Console widget
        console = AdminConsoleWidget()
        layout.addWidget(console)

        return widget

    def _create_execution_tab(self):
        """Create command execution tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Command input
        cmd_group = QGroupBox("Execute Commands")
        cmd_layout = QVBoxLayout(cmd_group)

        # Console type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Console Type:"))
        self.console_type_combo = QComboBox()
        self.console_type_combo.addItem("PowerShell", ConsoleType.POWERSHELL)
        self.console_type_combo.addItem("CMD", ConsoleType.CMD)
        type_layout.addWidget(self.console_type_combo)
        type_layout.addStretch()
        cmd_layout.addLayout(type_layout)

        # Commands
        cmd_layout.addWidget(QLabel("Commands (one per line):"))
        self.commands_edit = QTextEdit()
        self.commands_edit.setPlainText(
            "# PowerShell examples:\n"
            "Get-Date\n"
            "Get-Location\n"
            "$PSVersionTable.PSVersion\n"
            "Get-Process | Select-Object -First 5"
        )
        self.commands_edit.setMaximumHeight(150)
        cmd_layout.addWidget(self.commands_edit)

        # Execute button
        execute_btn = QPushButton("Execute Commands")
        execute_btn.clicked.connect(self._execute_commands)
        cmd_layout.addWidget(execute_btn)

        layout.addWidget(cmd_group)

        # Output
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout(output_group)

        self.output_edit = QTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: Consolas;
                font-size: 10pt;
            }
        """)
        output_layout.addWidget(self.output_edit)

        layout.addWidget(output_group)

        return widget

    def _create_privilege_tab(self):
        """Create privilege management tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Status group
        status_group = QGroupBox("Privilege Status")
        status_layout = QVBoxLayout(status_group)

        self.privilege_status_edit = QTextEdit()
        self.privilege_status_edit.setReadOnly(True)
        self.privilege_status_edit.setMaximumHeight(200)
        status_layout.addWidget(self.privilege_status_edit)

        refresh_btn = QPushButton("Refresh Status")
        refresh_btn.clicked.connect(self._update_privilege_status)
        status_layout.addWidget(refresh_btn)

        layout.addWidget(status_group)

        # Operations group
        ops_group = QGroupBox("Privilege Operations")
        ops_layout = QVBoxLayout(ops_group)

        # Enable privilege
        enable_layout = QHBoxLayout()
        enable_layout.addWidget(QLabel("Enable Privilege:"))
        self.privilege_combo = QComboBox()
        self.privilege_combo.addItems([
            "SeBackupPrivilege",
            "SeRestorePrivilege",
            "SeDebugPrivilege",
            "SeShutdownPrivilege",
            "SeTakeOwnershipPrivilege"
        ])
        enable_layout.addWidget(self.privilege_combo)

        enable_btn = QPushButton("Enable")
        enable_btn.clicked.connect(self._enable_privilege)
        enable_layout.addWidget(enable_btn)

        disable_btn = QPushButton("Disable")
        disable_btn.clicked.connect(self._disable_privilege)
        enable_layout.addWidget(disable_btn)

        enable_layout.addStretch()
        ops_layout.addLayout(enable_layout)

        # Test context manager
        test_ctx_btn = QPushButton("Test Privilege Context (Backup)")
        test_ctx_btn.clicked.connect(self._test_privilege_context)
        ops_layout.addWidget(test_ctx_btn)

        layout.addWidget(ops_group)

        # Update status
        self._update_privilege_status()

        return widget

    def _create_elevation_tab(self):
        """Create elevation features tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Status
        status_group = QGroupBox("Elevation Status")
        status_layout = QVBoxLayout(status_group)

        self.elevation_status_label = QLabel()
        status_layout.addWidget(self.elevation_status_label)

        layout.addWidget(status_group)

        # Dialogs
        dialog_group = QGroupBox("Elevation Dialogs")
        dialog_layout = QVBoxLayout(dialog_group)

        full_dialog_btn = QPushButton("Show Full Elevation Dialog")
        full_dialog_btn.clicked.connect(self._show_full_elevation_dialog)
        dialog_layout.addWidget(full_dialog_btn)

        quick_dialog_btn = QPushButton("Show Quick Elevation Dialog")
        quick_dialog_btn.clicked.connect(self._show_quick_elevation_dialog)
        dialog_layout.addWidget(quick_dialog_btn)

        layout.addWidget(dialog_group)

        # Console launch
        launch_group = QGroupBox("Launch Elevated Console")
        launch_layout = QVBoxLayout(launch_group)

        launch_ps_btn = QPushButton("Launch Elevated PowerShell")
        launch_ps_btn.clicked.connect(self._launch_elevated_powershell)
        launch_layout.addWidget(launch_ps_btn)

        launch_cmd_btn = QPushButton("Launch Elevated CMD")
        launch_cmd_btn.clicked.connect(self._launch_elevated_cmd)
        launch_layout.addWidget(launch_cmd_btn)

        layout.addWidget(launch_group)

        layout.addStretch()

        # Update status
        self._update_elevation_status()

        return widget

    def _create_advanced_tab(self):
        """Create advanced examples tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Example buttons
        examples = [
            ("List System Services (Admin Required)", self._example_list_services),
            ("Read Protected Registry Key", self._example_read_registry),
            ("Enumerate Running Processes", self._example_enum_processes),
            ("Check Disk Permissions", self._example_disk_permissions),
            ("System Information Gather", self._example_system_info),
        ]

        for title, handler in examples:
            btn = QPushButton(title)
            btn.clicked.connect(handler)
            layout.addWidget(btn)

        layout.addStretch()

        # Results
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)

        self.results_edit = QTextEdit()
        self.results_edit.setReadOnly(True)
        results_layout.addWidget(self.results_edit)

        layout.addWidget(results_group)

        return widget

    def _update_status(self):
        """Update all status displays."""
        self._update_privilege_status()
        self._update_elevation_status()

    def _update_privilege_status(self):
        """Update privilege status display."""
        if not hasattr(self, 'privilege_status_edit'):
            return

        status_text = []
        status_text.append(f"Running as Admin: {self.privilege_manager.is_admin()}")
        status_text.append(f"In Admin Group: {self.privilege_manager.is_in_admin_group()}")
        status_text.append(f"Current User: {self.privilege_manager.get_token_user()}")
        status_text.append("\nEnabled Privileges:")

        for name, enabled in self.privilege_manager.get_all_privileges():
            if enabled:
                status_text.append(f"  ✓ {name}")

        self.privilege_status_edit.setPlainText("\n".join(status_text))

    def _update_elevation_status(self):
        """Update elevation status display."""
        if not hasattr(self, 'elevation_status_label'):
            return

        is_elevated = self.elevation_manager.is_elevated()
        is_admin = self.elevation_manager.is_admin()
        elev_type = self.elevation_manager.get_elevation_type()

        status_text = f"""
<b>Elevation Status:</b><br>
• Is Elevated: <span style='color: {"green" if is_elevated else "orange"};'>{is_elevated}</span><br>
• Is Admin: <span style='color: {"green" if is_admin else "orange"};'>{is_admin}</span><br>
• Type: <b>{elev_type}</b>
        """

        self.elevation_status_label.setText(status_text)

    def _execute_commands(self):
        """Execute commands."""
        # Get commands
        text = self.commands_edit.toPlainText()
        commands = [
            line.strip() for line in text.split('\n')
            if line.strip() and not line.strip().startswith('#')
        ]

        if not commands:
            QMessageBox.warning(self, "No Commands", "Please enter commands to execute.")
            return

        # Get console type
        console_type = self.console_type_combo.currentData()

        # Create config
        config = ConsoleConfig(
            console_type=console_type,
            capture_output=True
        )

        # Execute
        self.output_edit.append("Executing commands...\n")
        self.statusBar().showMessage("Executing...")

        success, stdout, stderr = self.console_manager.execute_batch_commands(
            commands, config
        )

        # Show results
        self.output_edit.append("-" * 60)
        if stdout:
            self.output_edit.append("OUTPUT:")
            self.output_edit.append(stdout)
        if stderr:
            self.output_edit.append("\nERRORS:")
            self.output_edit.append(stderr)
        self.output_edit.append("-" * 60 + "\n")

        status = "Success" if success else "Failed"
        self.statusBar().showMessage(f"Execution {status}")

    def _enable_privilege(self):
        """Enable selected privilege."""
        privilege = self.privilege_combo.currentText()

        if not self.privilege_manager.is_admin():
            QMessageBox.warning(
                self,
                "Admin Required",
                "Administrator privileges required to enable privileges."
            )
            return

        if self.privilege_manager.enable_privilege(privilege):
            QMessageBox.information(
                self,
                "Success",
                f"Privilege enabled: {privilege}"
            )
            self._update_privilege_status()
        else:
            QMessageBox.critical(
                self,
                "Failed",
                f"Failed to enable privilege: {privilege}"
            )

    def _disable_privilege(self):
        """Disable selected privilege."""
        privilege = self.privilege_combo.currentText()

        if self.privilege_manager.disable_privilege(privilege):
            QMessageBox.information(
                self,
                "Success",
                f"Privilege disabled: {privilege}"
            )
            self._update_privilege_status()
        else:
            QMessageBox.critical(
                self,
                "Failed",
                f"Failed to disable privilege: {privilege}"
            )

    def _test_privilege_context(self):
        """Test privilege context manager."""
        try:
            was_enabled = self.privilege_manager.is_privilege_enabled("SeBackupPrivilege")

            with PrivilegeContext(["SeBackupPrivilege"]):
                is_enabled = self.privilege_manager.is_privilege_enabled("SeBackupPrivilege")

            now_enabled = self.privilege_manager.is_privilege_enabled("SeBackupPrivilege")

            QMessageBox.information(
                self,
                "Context Test",
                f"Privilege Context Test:\n\n"
                f"Before: {was_enabled}\n"
                f"Inside: {is_enabled}\n"
                f"After: {now_enabled}\n\n"
                f"Success!"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Context test failed: {e}")

    def _show_full_elevation_dialog(self):
        """Show full elevation dialog."""
        dialog = ElevationDialog(
            operation="Example System Operation",
            description="This is an example of the full elevation dialog with detailed information.",
            show_remember=True,
            parent=self
        )

        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            remember = dialog.get_remember_choice()
            QMessageBox.information(
                self,
                "Elevation Approved",
                f"User approved elevation.\nRemember choice: {remember}"
            )
        else:
            QMessageBox.information(
                self,
                "Elevation Denied",
                "User declined elevation."
            )

    def _show_quick_elevation_dialog(self):
        """Show quick elevation dialog."""
        dialog = QuickElevationDialog(
            operation="Quick privilege check",
            parent=self
        )

        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Approved", "Quick elevation approved!")
        else:
            QMessageBox.information(self, "Denied", "Quick elevation denied.")

    def _launch_elevated_powershell(self):
        """Launch elevated PowerShell."""
        if self.elevation_manager.is_elevated():
            QMessageBox.information(
                self,
                "Already Elevated",
                "Application is already running as administrator."
            )
            return

        dialog = ElevationDialog(
            operation="Launch Elevated PowerShell",
            description="Open a new PowerShell window with administrator privileges.",
            parent=self
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = ConsoleConfig(
                console_type=ConsoleType.POWERSHELL,
                elevated=True,
                title="Smart Search Pro - Elevated PowerShell"
            )

            session = self.console_manager.launch_console(config)
            if session:
                QMessageBox.information(
                    self,
                    "Launched",
                    "Elevated PowerShell console has been launched."
                )

    def _launch_elevated_cmd(self):
        """Launch elevated CMD."""
        config = ConsoleConfig(
            console_type=ConsoleType.CMD,
            elevated=True,
            title="Smart Search Pro - Elevated CMD"
        )

        session = self.console_manager.launch_console(config)
        if session:
            self.statusBar().showMessage("Elevated CMD launched")

    def _example_list_services(self):
        """Example: List system services."""
        commands = [
            'Get-Service | Where-Object {$_.Status -eq "Running"} | Select-Object -First 10 Name, Status, DisplayName | Format-Table -AutoSize'
        ]

        success, stdout, stderr = self.console_manager.execute_batch_commands(commands)
        self.results_edit.setPlainText(stdout or stderr or "No output")

    def _example_read_registry(self):
        """Example: Read registry key."""
        commands = [
            'Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion" | Select-Object ProductName, CurrentVersion, BuildLabEx'
        ]

        success, stdout, stderr = self.console_manager.execute_batch_commands(commands)
        self.results_edit.setPlainText(stdout or stderr or "No output")

    def _example_enum_processes(self):
        """Example: Enumerate processes."""
        commands = [
            'Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 10 Name, Id, WorkingSet | Format-Table -AutoSize'
        ]

        success, stdout, stderr = self.console_manager.execute_batch_commands(commands)
        self.results_edit.setPlainText(stdout or stderr or "No output")

    def _example_disk_permissions(self):
        """Example: Check disk permissions."""
        commands = [
            'Get-Acl -Path "C:\\" | Format-List'
        ]

        success, stdout, stderr = self.console_manager.execute_batch_commands(commands)
        self.results_edit.setPlainText(stdout or stderr or "No output")

    def _example_system_info(self):
        """Example: Gather system information."""
        commands = [
            '$env:COMPUTERNAME',
            '$env:USERNAME',
            '[System.Environment]::OSVersion.VersionString',
            '[System.Environment]::ProcessorCount',
            '(Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory / 1GB'
        ]

        success, stdout, stderr = self.console_manager.execute_batch_commands(commands)
        self.results_edit.setPlainText(stdout or stderr or "No output")


def main():
    """Run example application."""
    app = QApplication(sys.argv)

    window = AdminConsoleExampleWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

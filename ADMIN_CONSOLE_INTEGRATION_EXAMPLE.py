"""
Admin Console System - Integration Example

Example showing how to integrate the admin console system
into the existing Smart Search Pro main window.
"""

# Example 1: Add menu action to open console
# -----------------------------------------
# Add to ui/main_window.py in _create_menu() method

def _create_menu_with_admin_console(self):
    """Create menu bar with admin console action."""
    menubar = self.menuBar()

    # ... existing menus ...

    # Add Tools menu (if not exists)
    tools_menu = menubar.addMenu("&Tools")

    # Add admin console action
    admin_console_action = QAction("Administrator Console", self)
    admin_console_action.setShortcut(QKeySequence("Ctrl+Alt+C"))
    admin_console_action.setStatusTip("Open administrator console")
    admin_console_action.triggered.connect(self.show_admin_console)
    tools_menu.addAction(admin_console_action)

    # Add privilege status action
    privilege_action = QAction("Check Privileges", self)
    privilege_action.setStatusTip("Check current privilege status")
    privilege_action.triggered.connect(self.show_privilege_status)
    tools_menu.addAction(privilege_action)


# Example 2: Implement console dialog
# -----------------------------------
# Add to ui/main_window.py as a new method

def show_admin_console(self):
    """Show admin console in a dialog."""
    from ui.admin_console_widget import AdminConsoleWidget

    dialog = QDialog(self)
    dialog.setWindowTitle("Administrator Console - Smart Search Pro")
    dialog.resize(900, 600)

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(0, 0, 0, 0)

    # Add console widget
    console = AdminConsoleWidget()
    layout.addWidget(console)

    # Show dialog
    dialog.exec()


# Example 3: Add as docked panel
# ------------------------------
# Add to ui/main_window.py in __init__() method

def _add_admin_console_dock(self):
    """Add admin console as a docked panel."""
    from PyQt6.QtWidgets import QDockWidget
    from ui.admin_console_widget import AdminConsoleWidget

    # Create dock widget
    console_dock = QDockWidget("Admin Console", self)
    console_dock.setObjectName("AdminConsoleDock")

    # Create console widget
    console_widget = AdminConsoleWidget()
    console_dock.setWidget(console_widget)

    # Add to bottom dock area (hidden by default)
    self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, console_dock)
    console_dock.hide()  # Hidden by default

    # Add view menu action to show/hide
    if hasattr(self, 'view_menu'):
        self.view_menu.addAction(console_dock.toggleViewAction())

    return console_dock


# Example 4: Privilege status dialog
# ----------------------------------
# Add to ui/main_window.py as a new method

def show_privilege_status(self):
    """Show current privilege status."""
    from system.privilege_manager import PrivilegeManager
    from PyQt6.QtWidgets import QTextEdit

    manager = PrivilegeManager()

    dialog = QDialog(self)
    dialog.setWindowTitle("Privilege Status")
    dialog.resize(600, 400)

    layout = QVBoxLayout(dialog)

    # Status text
    text_edit = QTextEdit()
    text_edit.setReadOnly(True)

    status_text = []
    status_text.append(f"Running as Administrator: {manager.is_admin()}")
    status_text.append(f"In Administrators Group: {manager.is_in_admin_group()}")
    status_text.append(f"Current User: {manager.get_token_user()}")
    status_text.append("\n" + "="*60)
    status_text.append("\nAll Privileges:")
    status_text.append("="*60 + "\n")

    for name, enabled in manager.get_all_privileges():
        status = "✓ ENABLED" if enabled else "  disabled"
        status_text.append(f"{status}  {name}")

    text_edit.setPlainText("\n".join(status_text))
    layout.addWidget(text_edit)

    # Close button
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(dialog.accept)
    layout.addWidget(close_btn)

    dialog.exec()


# Example 5: Use elevation dialog before admin operation
# -----------------------------------------------------
# Add to operations where admin access is needed

def perform_admin_file_operation(self, file_path: str):
    """Perform file operation requiring admin privileges."""
    from ui.elevation_dialog import ElevationDialog
    from system.privilege_manager import PrivilegeContext

    # Show elevation dialog
    dialog = ElevationDialog(
        operation="Modify Protected File",
        description=f"Smart Search Pro needs administrator privileges to modify:\n{file_path}",
        show_remember=True,
        parent=self
    )

    if dialog.exec() != QDialog.DialogCode.Accepted:
        self.statusBar().showMessage("Operation cancelled by user")
        return False

    # Perform operation with elevated privileges
    try:
        with PrivilegeContext(["SeBackupPrivilege", "SeRestorePrivilege"]):
            # Your operation here
            # Example: modify file
            with open(file_path, 'w') as f:
                f.write("Modified with admin privileges")

        self.statusBar().showMessage("Operation completed successfully")
        return True

    except PermissionError:
        QMessageBox.critical(
            self,
            "Permission Denied",
            "Could not complete operation. Administrator privileges required."
        )
        return False
    except Exception as e:
        QMessageBox.critical(
            self,
            "Error",
            f"Operation failed: {e}"
        )
        return False


# Example 6: Execute command and show result
# -----------------------------------------
# Add to operations that need to run shell commands

def execute_admin_command(self, command: str):
    """Execute command and show result."""
    from system.admin_console import AdminConsoleManager, ConsoleConfig, ConsoleType
    from PyQt6.QtWidgets import QProgressDialog

    # Show progress
    progress = QProgressDialog(
        "Executing command...",
        "Cancel",
        0, 0,
        self
    )
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    progress.show()

    # Execute command
    manager = AdminConsoleManager()
    config = ConsoleConfig(
        console_type=ConsoleType.POWERSHELL,
        capture_output=True
    )

    success, stdout, stderr = manager.execute_batch_commands(
        [command],
        config
    )

    progress.close()

    # Show result
    if success:
        QMessageBox.information(
            self,
            "Command Output",
            stdout or "Command completed successfully"
        )
    else:
        QMessageBox.critical(
            self,
            "Command Failed",
            stderr or "Command execution failed"
        )

    manager.cleanup()
    return success


# Example 7: Add toolbar button
# ----------------------------
# Add to ui/main_window.py in _create_toolbar() method

def _add_admin_console_toolbar_button(self, toolbar):
    """Add admin console button to toolbar."""
    from system.elevation import ElevationManager

    # Console button
    console_action = QAction("Admin Console", self)
    console_action.setStatusTip("Open administrator console")
    console_action.triggered.connect(self.show_admin_console)
    toolbar.addAction(console_action)

    # Update button text based on elevation status
    elevation_manager = ElevationManager()
    if elevation_manager.is_elevated():
        console_action.setText("Admin Console ★")
        console_action.setToolTip("Administrator console (Running as admin)")


# Example 8: Context menu integration
# ----------------------------------
# Add to results panel right-click menu

def _add_admin_operations_to_context_menu(self, menu, selected_file):
    """Add admin operations to context menu."""
    from system.elevation import ElevationManager

    elevation_manager = ElevationManager()

    # Separator
    menu.addSeparator()

    # Admin operations submenu
    admin_menu = menu.addMenu("Admin Operations")

    # Take ownership
    take_ownership_action = QAction("Take Ownership", self)
    take_ownership_action.triggered.connect(
        lambda: self.take_file_ownership(selected_file)
    )
    admin_menu.addAction(take_ownership_action)

    # Change permissions
    permissions_action = QAction("Change Permissions", self)
    permissions_action.triggered.connect(
        lambda: self.change_file_permissions(selected_file)
    )
    admin_menu.addAction(permissions_action)

    # Delete with admin
    delete_admin_action = QAction("Delete (Admin)", self)
    delete_admin_action.triggered.connect(
        lambda: self.delete_with_admin(selected_file)
    )
    admin_menu.addAction(delete_admin_action)

    # Show elevation indicator
    if not elevation_manager.is_elevated():
        admin_menu.setTitle("Admin Operations (UAC Required)")


# Example 9: File operations with privilege
# ----------------------------------------

def take_file_ownership(self, file_path: str):
    """Take ownership of file."""
    from ui.elevation_dialog import QuickElevationDialog
    from system.admin_console import AdminConsoleManager

    # Ask user
    dialog = QuickElevationDialog(
        operation=f"Take ownership of:\n{file_path}",
        parent=self
    )

    if dialog.exec() != QDialog.DialogCode.Accepted:
        return

    # Execute takeown command
    manager = AdminConsoleManager()
    command = f'takeown /F "{file_path}"'

    success, stdout, stderr = manager.execute_batch_commands([command])

    if success:
        QMessageBox.information(self, "Success", "Ownership changed successfully")
    else:
        QMessageBox.critical(self, "Failed", f"Failed to take ownership:\n{stderr}")

    manager.cleanup()


def change_file_permissions(self, file_path: str):
    """Change file permissions."""
    from system.admin_console import AdminConsoleManager

    # Execute icacls command
    manager = AdminConsoleManager()
    command = f'icacls "{file_path}"'

    success, stdout, stderr = manager.execute_batch_commands([command])

    if success:
        # Show current permissions
        QMessageBox.information(
            self,
            "Current Permissions",
            stdout
        )
    else:
        QMessageBox.critical(self, "Error", stderr)

    manager.cleanup()


def delete_with_admin(self, file_path: str):
    """Delete file with admin privileges."""
    from ui.elevation_dialog import ElevationDialog
    from system.privilege_manager import PrivilegeContext

    # Confirm
    dialog = ElevationDialog(
        operation="Delete Protected File",
        description=f"This will permanently delete:\n{file_path}\n\nThis action cannot be undone.",
        parent=self
    )

    if dialog.exec() != QDialog.DialogCode.Accepted:
        return

    # Delete with privileges
    try:
        with PrivilegeContext(["SeRestorePrivilege"]):
            os.remove(file_path)

        QMessageBox.information(self, "Success", "File deleted successfully")

    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to delete file:\n{e}")


# Example 10: Status bar indicator
# -------------------------------
# Add to ui/main_window.py in __init__() method

def _add_elevation_status_indicator(self):
    """Add elevation status to status bar."""
    from system.elevation import ElevationManager
    from PyQt6.QtWidgets import QLabel

    elevation_manager = ElevationManager()

    # Create status label
    self.elevation_status_label = QLabel()

    if elevation_manager.is_elevated():
        self.elevation_status_label.setText("● Running as Administrator")
        self.elevation_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
    else:
        self.elevation_status_label.setText("● Standard User")
        self.elevation_status_label.setStyleSheet("color: #95a5a6;")

    # Add to status bar
    self.statusBar().addPermanentWidget(self.elevation_status_label)


# Complete Integration Example
# ============================

"""
To integrate the admin console system into your main window,
add these imports at the top of ui/main_window.py:
"""

# Add to imports section:
from ui.admin_console_widget import AdminConsoleWidget
from ui.elevation_dialog import ElevationDialog, QuickElevationDialog
from system.admin_console import AdminConsoleManager, ConsoleConfig, ConsoleType
from system.privilege_manager import PrivilegeManager, PrivilegeContext
from system.elevation import ElevationManager

"""
Then add the methods above to your MainWindow class.

Minimal integration:
1. Add show_admin_console() method
2. Add menu action in _create_menu()
3. Done!

Full integration:
1. Add all methods above
2. Integrate with file operations
3. Add context menu items
4. Add status indicators
5. Done!
"""

# Quick Test
# ==========

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow, QAction

    app = QApplication(sys.argv)

    # Create simple main window with admin console
    window = QMainWindow()
    window.setWindowTitle("Smart Search Pro - Admin Console Integration Test")
    window.resize(1000, 700)

    # Add menu
    menubar = window.menuBar()
    tools_menu = menubar.addMenu("Tools")

    # Add console action
    console_action = QAction("Admin Console", window)
    console_action.setShortcut("Ctrl+Alt+C")
    console_action.triggered.connect(
        lambda: show_admin_console(window)
    )
    tools_menu.addAction(console_action)

    # Add privilege action
    privilege_action = QAction("Check Privileges", window)
    privilege_action.triggered.connect(
        lambda: show_privilege_status(window)
    )
    tools_menu.addAction(privilege_action)

    # Show
    window.show()
    window.statusBar().showMessage("Press Ctrl+Alt+C to open admin console")

    sys.exit(app.exec())

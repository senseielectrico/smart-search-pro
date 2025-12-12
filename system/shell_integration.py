"""
Windows Shell Integration for Smart Search Pro.

Provides context menu registration, file associations, and jump list support.
"""

import winreg
import ctypes
import ctypes.wintypes as wintypes
import logging
from typing import Optional, List, Dict
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ContextMenuItem:
    """Context menu item configuration."""
    name: str
    command: str
    icon: Optional[str] = None
    position: Optional[str] = None  # "top" or "bottom"
    extended: bool = False  # Show only when Shift is pressed


class ShellIntegration:
    """
    Windows shell integration manager.

    Features:
    - Context menu registration
    - File type associations
    - Jump list support
    - Send To menu integration

    Note: Most operations require administrator privileges.
    """

    def __init__(self):
        """Initialize shell integration manager."""
        self.app_name = "SmartSearchPro"
        self.app_id = "com.smartsearch.pro"

        logger.info("Shell integration manager initialized")

    def add_context_menu(
        self,
        item: ContextMenuItem,
        file_types: Optional[List[str]] = None,
        directories: bool = False,
        background: bool = False,
    ) -> bool:
        """
        Add context menu item for files/directories.

        Args:
            item: Context menu item configuration
            file_types: File extensions (e.g., [".txt", ".pdf"]) or None for all
            directories: Add to directory context menu
            background: Add to folder background context menu

        Returns:
            True if added successfully

        Example:
            manager.add_context_menu(
                ContextMenuItem(
                    name="Search with Smart Search",
                    command=f'"{app_path}" --search "%1"',
                    icon=f"{app_path},0"
                ),
                file_types=[".txt", ".pdf"]
            )
        """
        try:
            # Determine registry paths
            paths = []

            if file_types:
                # Specific file types
                for ext in file_types:
                    if not ext.startswith('.'):
                        ext = f'.{ext}'
                    paths.append(f"{ext}\\shell\\{item.name}")
            else:
                # All files
                paths.append(f"*\\shell\\{item.name}")

            if directories:
                paths.append(f"Directory\\shell\\{item.name}")

            if background:
                paths.append(f"Directory\\Background\\shell\\{item.name}")

            # Register for each path
            for reg_path in paths:
                self._create_context_menu_key(reg_path, item)

            logger.info(f"Added context menu item: {item.name}")
            return True

        except Exception as e:
            logger.error(f"Error adding context menu: {e}")
            return False

    def _create_context_menu_key(
        self,
        path: str,
        item: ContextMenuItem,
    ) -> None:
        """Create registry key for context menu item."""
        # Create main key
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, path) as key:
            # Set display name
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, item.name)

            # Set icon if provided
            if item.icon:
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, item.icon)

            # Set extended flag (Shift+Right-click)
            if item.extended:
                winreg.SetValueEx(key, "Extended", 0, winreg.REG_SZ, "")

            # Set position
            if item.position:
                winreg.SetValueEx(
                    key,
                    "Position",
                    0,
                    winreg.REG_SZ,
                    item.position.capitalize()
                )

        # Create command subkey
        cmd_path = f"{path}\\command"
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, cmd_path) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, item.command)

    def remove_context_menu(
        self,
        item_name: str,
        file_types: Optional[List[str]] = None,
        directories: bool = False,
        background: bool = False,
    ) -> bool:
        """
        Remove context menu item.

        Args:
            item_name: Name of context menu item to remove
            file_types: File extensions or None for all
            directories: Remove from directory context menu
            background: Remove from folder background context menu

        Returns:
            True if removed successfully
        """
        try:
            # Determine registry paths
            paths = []

            if file_types:
                for ext in file_types:
                    if not ext.startswith('.'):
                        ext = f'.{ext}'
                    paths.append(f"{ext}\\shell\\{item_name}")
            else:
                paths.append(f"*\\shell\\{item_name}")

            if directories:
                paths.append(f"Directory\\shell\\{item_name}")

            if background:
                paths.append(f"Directory\\Background\\shell\\{item_name}")

            # Remove keys
            for reg_path in paths:
                try:
                    winreg.DeleteKey(
                        winreg.HKEY_CLASSES_ROOT,
                        f"{reg_path}\\command"
                    )
                    winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, reg_path)
                except FileNotFoundError:
                    pass

            logger.info(f"Removed context menu item: {item_name}")
            return True

        except Exception as e:
            logger.error(f"Error removing context menu: {e}")
            return False

    def register_file_association(
        self,
        extension: str,
        prog_id: str,
        description: str,
        executable: str,
        icon: Optional[str] = None,
    ) -> bool:
        """
        Register file type association.

        Args:
            extension: File extension (e.g., ".ssp")
            prog_id: Program ID (e.g., "SmartSearch.Index")
            description: File type description
            executable: Path to executable
            icon: Path to icon file

        Returns:
            True if registered successfully
        """
        try:
            if not extension.startswith('.'):
                extension = f'.{extension}'

            # Create extension key
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, extension) as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, prog_id)

            # Create ProgID key
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, prog_id) as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, description)

            # Set icon
            if icon:
                icon_path = f"{prog_id}\\DefaultIcon"
                with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, icon_path) as key:
                    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, icon)

            # Set open command
            cmd_path = f"{prog_id}\\shell\\open\\command"
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, cmd_path) as key:
                command = f'"{executable}" "%1"'
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)

            # Notify shell of changes
            self._notify_shell_change()

            logger.info(f"Registered file association: {extension} -> {prog_id}")
            return True

        except Exception as e:
            logger.error(f"Error registering file association: {e}")
            return False

    def unregister_file_association(
        self,
        extension: str,
        prog_id: str,
    ) -> bool:
        """
        Unregister file type association.

        Args:
            extension: File extension
            prog_id: Program ID

        Returns:
            True if unregistered successfully
        """
        try:
            if not extension.startswith('.'):
                extension = f'.{extension}'

            # Remove extension key
            try:
                winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, extension)
            except FileNotFoundError:
                pass

            # Remove ProgID keys
            self._delete_key_tree(winreg.HKEY_CLASSES_ROOT, prog_id)

            # Notify shell
            self._notify_shell_change()

            logger.info(f"Unregistered file association: {extension}")
            return True

        except Exception as e:
            logger.error(f"Error unregistering file association: {e}")
            return False

    def set_app_id(self, app_id: Optional[str] = None) -> bool:
        """
        Set Application User Model ID for taskbar grouping.

        Args:
            app_id: Application ID (default: self.app_id)

        Returns:
            True if set successfully
        """
        try:
            if app_id is None:
                app_id = self.app_id

            # Use shell32 to set app ID
            shell32 = ctypes.windll.shell32
            shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

            logger.info(f"Set App ID: {app_id}")
            return True

        except Exception as e:
            logger.error(f"Error setting App ID: {e}")
            return False

    def add_to_send_to(
        self,
        name: str,
        executable: str,
        arguments: Optional[str] = None,
    ) -> bool:
        """
        Add application to Send To menu.

        Args:
            name: Display name in Send To menu
            executable: Path to executable
            arguments: Command line arguments template

        Returns:
            True if added successfully
        """
        try:
            # Get Send To folder
            send_to = Path(os.path.expandvars(r"%APPDATA%\Microsoft\Windows\SendTo"))

            if not send_to.exists():
                logger.error("Send To folder not found")
                return False

            # Create shortcut
            shortcut_path = send_to / f"{name}.lnk"

            # Use PowerShell to create shortcut
            import subprocess

            ps_script = f"""
            $WshShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
            $Shortcut.TargetPath = "{executable}"
            """

            if arguments:
                ps_script += f'$Shortcut.Arguments = "{arguments}"\n'

            ps_script += "$Shortcut.Save()"

            subprocess.run(
                ["powershell", "-Command", ps_script],
                check=True,
                capture_output=True,
            )

            logger.info(f"Added to Send To: {name}")
            return True

        except Exception as e:
            logger.error(f"Error adding to Send To: {e}")
            return False

    def remove_from_send_to(self, name: str) -> bool:
        """
        Remove application from Send To menu.

        Args:
            name: Display name to remove

        Returns:
            True if removed successfully
        """
        try:
            import os
            send_to = Path(os.path.expandvars(r"%APPDATA%\Microsoft\Windows\SendTo"))
            shortcut_path = send_to / f"{name}.lnk"

            if shortcut_path.exists():
                shortcut_path.unlink()
                logger.info(f"Removed from Send To: {name}")
                return True
            else:
                logger.warning(f"Send To item not found: {name}")
                return False

        except Exception as e:
            logger.error(f"Error removing from Send To: {e}")
            return False

    def _delete_key_tree(self, root_key, sub_key: str) -> None:
        """Recursively delete registry key and all subkeys."""
        try:
            with winreg.OpenKey(root_key, sub_key) as key:
                # Get all subkeys
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        self._delete_key_tree(root_key, f"{sub_key}\\{subkey_name}")
                        i += 1
                    except OSError:
                        break

            # Delete the key itself
            winreg.DeleteKey(root_key, sub_key)

        except FileNotFoundError:
            pass

    def _notify_shell_change(self) -> None:
        """Notify Windows shell of association changes."""
        try:
            SHCNE_ASSOCCHANGED = 0x08000000
            SHCNF_IDLIST = 0x0000

            ctypes.windll.shell32.SHChangeNotify(
                SHCNE_ASSOCCHANGED,
                SHCNF_IDLIST,
                None,
                None
            )
        except Exception as e:
            logger.error(f"Error notifying shell: {e}")


# Example usage
if __name__ == "__main__":
    import os
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    manager = ShellIntegration()

    # Example: Add context menu for text files
    app_path = Path(__file__).parent.parent / "main.py"

    item = ContextMenuItem(
        name="Search with Smart Search",
        command=f'python "{app_path}" --search "%1"',
        extended=False,
    )

    print("Shell Integration Manager")
    print("=" * 50)
    print("\nNote: Most operations require administrator privileges")
    print("\nAvailable operations:")
    print("1. Add context menu for .txt files")
    print("2. Remove context menu")
    print("3. Add to Send To menu")
    print("4. Set App ID")

    choice = input("\nSelect operation (1-4): ")

    if choice == "1":
        manager.add_context_menu(item, file_types=[".txt"])
    elif choice == "2":
        manager.remove_context_menu("Search with Smart Search", file_types=[".txt"])
    elif choice == "3":
        manager.add_to_send_to("Smart Search Pro", str(app_path))
    elif choice == "4":
        manager.set_app_id()

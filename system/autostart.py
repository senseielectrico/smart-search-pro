"""
Autostart Manager for Smart Search Pro.

Manages application startup using Windows Registry and Task Scheduler.
"""

import winreg
import subprocess
import logging
from typing import Optional
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class StartupMethod(Enum):
    """Startup registration methods."""
    REGISTRY_CURRENT_USER = "registry_current_user"
    REGISTRY_LOCAL_MACHINE = "registry_local_machine"
    TASK_SCHEDULER = "task_scheduler"
    STARTUP_FOLDER = "startup_folder"


class AutostartManager:
    """
    Manager for Windows startup configuration.

    Features:
    - Add/remove from Windows startup
    - Multiple startup methods (Registry, Task Scheduler, Startup folder)
    - Per-user or system-wide startup
    - Configurable startup arguments
    """

    def __init__(self, app_name: str = "SmartSearchPro"):
        """
        Initialize autostart manager.

        Args:
            app_name: Application name for registry/task entries
        """
        self.app_name = app_name

        # Registry paths
        self.reg_path_cu = r"Software\Microsoft\Windows\CurrentVersion\Run"
        self.reg_path_lm = r"Software\Microsoft\Windows\CurrentVersion\Run"

        logger.info("Autostart manager initialized")

    def is_enabled(
        self,
        method: StartupMethod = StartupMethod.REGISTRY_CURRENT_USER,
    ) -> bool:
        """
        Check if autostart is enabled.

        Args:
            method: Startup method to check

        Returns:
            True if autostart is enabled
        """
        if method == StartupMethod.REGISTRY_CURRENT_USER:
            return self._is_registry_enabled(winreg.HKEY_CURRENT_USER)
        elif method == StartupMethod.REGISTRY_LOCAL_MACHINE:
            return self._is_registry_enabled(winreg.HKEY_LOCAL_MACHINE)
        elif method == StartupMethod.TASK_SCHEDULER:
            return self._is_task_enabled()
        elif method == StartupMethod.STARTUP_FOLDER:
            return self._is_startup_folder_enabled()
        else:
            return False

    def enable(
        self,
        executable: str,
        arguments: Optional[str] = None,
        method: StartupMethod = StartupMethod.REGISTRY_CURRENT_USER,
        minimized: bool = False,
    ) -> bool:
        """
        Enable autostart.

        Args:
            executable: Path to executable
            arguments: Optional command line arguments
            method: Startup method to use
            minimized: Start application minimized

        Returns:
            True if enabled successfully

        Example:
            manager.enable(
                r"C:\Program Files\SmartSearch\smartsearch.exe",
                "--minimized --tray",
                StartupMethod.REGISTRY_CURRENT_USER
            )
        """
        if method == StartupMethod.REGISTRY_CURRENT_USER:
            return self._enable_registry(
                executable,
                arguments,
                winreg.HKEY_CURRENT_USER,
                minimized,
            )
        elif method == StartupMethod.REGISTRY_LOCAL_MACHINE:
            return self._enable_registry(
                executable,
                arguments,
                winreg.HKEY_LOCAL_MACHINE,
                minimized,
            )
        elif method == StartupMethod.TASK_SCHEDULER:
            return self._enable_task(executable, arguments, minimized)
        elif method == StartupMethod.STARTUP_FOLDER:
            return self._enable_startup_folder(executable, arguments, minimized)
        else:
            logger.error(f"Unknown startup method: {method}")
            return False

    def disable(
        self,
        method: StartupMethod = StartupMethod.REGISTRY_CURRENT_USER,
    ) -> bool:
        """
        Disable autostart.

        Args:
            method: Startup method to disable

        Returns:
            True if disabled successfully
        """
        if method == StartupMethod.REGISTRY_CURRENT_USER:
            return self._disable_registry(winreg.HKEY_CURRENT_USER)
        elif method == StartupMethod.REGISTRY_LOCAL_MACHINE:
            return self._disable_registry(winreg.HKEY_LOCAL_MACHINE)
        elif method == StartupMethod.TASK_SCHEDULER:
            return self._disable_task()
        elif method == StartupMethod.STARTUP_FOLDER:
            return self._disable_startup_folder()
        else:
            logger.error(f"Unknown startup method: {method}")
            return False

    def disable_all(self) -> bool:
        """
        Disable autostart for all methods.

        Returns:
            True if all methods were disabled
        """
        results = []

        for method in StartupMethod:
            if self.is_enabled(method):
                results.append(self.disable(method))

        return all(results) if results else True

    def _is_registry_enabled(self, root_key) -> bool:
        """Check if registry autostart is enabled."""
        try:
            with winreg.OpenKey(root_key, self.reg_path_cu) as key:
                winreg.QueryValueEx(key, self.app_name)
                return True
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Error checking registry: {e}")
            return False

    def _enable_registry(
        self,
        executable: str,
        arguments: Optional[str],
        root_key,
        minimized: bool,
    ) -> bool:
        """Enable registry-based autostart."""
        try:
            # Build command
            command = f'"{executable}"'

            if arguments:
                command += f" {arguments}"

            # Open registry key
            with winreg.OpenKey(
                root_key,
                self.reg_path_cu,
                0,
                winreg.KEY_SET_VALUE,
            ) as key:
                winreg.SetValueEx(
                    key,
                    self.app_name,
                    0,
                    winreg.REG_SZ,
                    command,
                )

            logger.info(f"Enabled registry autostart: {command}")
            return True

        except Exception as e:
            logger.error(f"Error enabling registry autostart: {e}")
            return False

    def _disable_registry(self, root_key) -> bool:
        """Disable registry-based autostart."""
        try:
            with winreg.OpenKey(
                root_key,
                self.reg_path_cu,
                0,
                winreg.KEY_SET_VALUE,
            ) as key:
                try:
                    winreg.DeleteValue(key, self.app_name)
                    logger.info("Disabled registry autostart")
                    return True
                except FileNotFoundError:
                    return True

        except Exception as e:
            logger.error(f"Error disabling registry autostart: {e}")
            return False

    def _is_task_enabled(self) -> bool:
        """Check if Task Scheduler task exists."""
        try:
            result = subprocess.run(
                ["schtasks", "/Query", "/TN", self.app_name],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error checking task: {e}")
            return False

    def _enable_task(
        self,
        executable: str,
        arguments: Optional[str],
        minimized: bool,
    ) -> bool:
        """Enable Task Scheduler autostart."""
        try:
            # Build task XML
            task_xml = self._create_task_xml(executable, arguments, minimized)

            # Create temporary XML file
            import tempfile
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.xml',
                delete=False,
            ) as f:
                f.write(task_xml)
                xml_path = f.name

            try:
                # Create scheduled task
                result = subprocess.run(
                    [
                        "schtasks",
                        "/Create",
                        "/TN", self.app_name,
                        "/XML", xml_path,
                        "/F",  # Force overwrite
                    ],
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    logger.info("Enabled Task Scheduler autostart")
                    return True
                else:
                    logger.error(f"Failed to create task: {result.stderr}")
                    return False

            finally:
                # Clean up temp file
                Path(xml_path).unlink(missing_ok=True)

        except Exception as e:
            logger.error(f"Error enabling task autostart: {e}")
            return False

    def _disable_task(self) -> bool:
        """Disable Task Scheduler autostart."""
        try:
            result = subprocess.run(
                ["schtasks", "/Delete", "/TN", self.app_name, "/F"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                logger.info("Disabled Task Scheduler autostart")
                return True
            else:
                # Task might not exist
                return True

        except Exception as e:
            logger.error(f"Error disabling task autostart: {e}")
            return False

    def _create_task_xml(
        self,
        executable: str,
        arguments: Optional[str],
        minimized: bool,
    ) -> str:
        """Create Task Scheduler XML definition."""
        import os

        # Get current user
        username = os.environ.get('USERNAME', 'User')

        args_xml = f"<Arguments>{arguments}</Arguments>" if arguments else ""

        return f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Smart Search Pro autostart</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <UserId>{username}</UserId>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>{username}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{executable}</Command>
      {args_xml}
    </Exec>
  </Actions>
</Task>"""

    def _is_startup_folder_enabled(self) -> bool:
        """Check if shortcut exists in Startup folder."""
        import os
        startup_folder = Path(
            os.path.expandvars(
                r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
            )
        )
        shortcut_path = startup_folder / f"{self.app_name}.lnk"
        return shortcut_path.exists()

    def _enable_startup_folder(
        self,
        executable: str,
        arguments: Optional[str],
        minimized: bool,
    ) -> bool:
        """Enable startup folder autostart."""
        try:
            import os
            startup_folder = Path(
                os.path.expandvars(
                    r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
                )
            )

            if not startup_folder.exists():
                logger.error("Startup folder not found")
                return False

            shortcut_path = startup_folder / f"{self.app_name}.lnk"

            # Create shortcut using PowerShell
            ps_script = f"""
            $WshShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
            $Shortcut.TargetPath = "{executable}"
            """

            if arguments:
                ps_script += f'$Shortcut.Arguments = "{arguments}"\n'

            if minimized:
                ps_script += "$Shortcut.WindowStyle = 7\n"  # Minimized

            ps_script += "$Shortcut.Save()"

            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                logger.info("Enabled Startup folder autostart")
                return True
            else:
                logger.error(f"Failed to create shortcut: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error enabling startup folder: {e}")
            return False

    def _disable_startup_folder(self) -> bool:
        """Disable startup folder autostart."""
        try:
            import os
            startup_folder = Path(
                os.path.expandvars(
                    r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
                )
            )
            shortcut_path = startup_folder / f"{self.app_name}.lnk"

            if shortcut_path.exists():
                shortcut_path.unlink()
                logger.info("Disabled Startup folder autostart")

            return True

        except Exception as e:
            logger.error(f"Error disabling startup folder: {e}")
            return False


# Example usage
if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    manager = AutostartManager()

    print("Autostart Manager")
    print("=" * 50)

    # Check current status
    for method in StartupMethod:
        enabled = manager.is_enabled(method)
        print(f"{method.value}: {'Enabled' if enabled else 'Disabled'}")

    print("\nOperations:")
    print("1. Enable (Registry - Current User)")
    print("2. Enable (Task Scheduler)")
    print("3. Disable all")
    print("4. Exit")

    choice = input("\nSelect operation (1-4): ")

    if choice == "1":
        exe_path = input("Executable path: ")
        manager.enable(exe_path, "--minimized", StartupMethod.REGISTRY_CURRENT_USER)
    elif choice == "2":
        exe_path = input("Executable path: ")
        manager.enable(exe_path, "--minimized", StartupMethod.TASK_SCHEDULER)
    elif choice == "3":
        manager.disable_all()
        print("Disabled all autostart methods")

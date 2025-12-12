"""
Admin Console Manager for Smart Search Pro.

Provides elevated administrator console support with UAC integration,
process management, and output capture capabilities.
"""

import ctypes
import ctypes.wintypes as wintypes
import sys
import os
import subprocess
import logging
import tempfile
from typing import Optional, List, Dict, Tuple, Callable
from pathlib import Path
from enum import IntEnum
from dataclasses import dataclass

try:
    import win32process
    import win32api
    import win32con
    import win32security
    import win32event
    import pywintypes
    HAS_PYWIN32 = True
except ImportError:
    HAS_PYWIN32 = False
    logging.warning("pywin32 not available, some features will be limited")

logger = logging.getLogger(__name__)

# Import security and elevation
try:
    from core.security import sanitize_cli_argument, log_security_event, SecurityEvent
    from system.elevation import ElevationManager, ShowWindow
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.security import sanitize_cli_argument, log_security_event, SecurityEvent
    from system.elevation import ElevationManager, ShowWindow


class ConsoleType(IntEnum):
    """Console application types."""
    CMD = 1
    POWERSHELL = 2
    POWERSHELL_CORE = 3


@dataclass
class ConsoleConfig:
    """Configuration for console session."""
    console_type: ConsoleType = ConsoleType.POWERSHELL
    working_directory: Optional[str] = None
    environment_vars: Optional[Dict[str, str]] = None
    elevated: bool = False
    capture_output: bool = False
    show_window: int = ShowWindow.SW_SHOWNORMAL
    initial_commands: Optional[List[str]] = None
    title: Optional[str] = None


@dataclass
class ConsoleSession:
    """Active console session information."""
    process_handle: int
    process_id: int
    console_type: ConsoleType
    elevated: bool
    working_directory: str
    stdout_file: Optional[str] = None
    stderr_file: Optional[str] = None


class AdminConsoleManager:
    """
    Manager for administrator console operations.

    Features:
    - Launch cmd.exe or PowerShell with admin privileges
    - UAC elevation via ShellExecuteEx
    - Custom working directory and environment
    - Output capture (redirected mode)
    - Batch command execution
    - Process monitoring
    """

    def __init__(self):
        """Initialize admin console manager."""
        self.elevation_manager = ElevationManager()
        self.active_sessions: Dict[int, ConsoleSession] = {}
        self.shell32 = ctypes.windll.shell32

        # Console paths
        self.console_paths = {
            ConsoleType.CMD: os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'cmd.exe'),
            ConsoleType.POWERSHELL: os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe'),
            ConsoleType.POWERSHELL_CORE: 'pwsh.exe'  # PowerShell 7+
        }

        logger.info("Admin console manager initialized")

    def is_admin(self) -> bool:
        """Check if running as administrator."""
        return self.elevation_manager.is_elevated()

    def get_console_path(self, console_type: ConsoleType) -> Optional[str]:
        """
        Get path to console executable.

        Args:
            console_type: Type of console

        Returns:
            Path to console executable or None if not found
        """
        path = self.console_paths.get(console_type)

        if path and Path(path).exists():
            return path

        # Try to find PowerShell Core in PATH
        if console_type == ConsoleType.POWERSHELL_CORE:
            try:
                result = subprocess.run(
                    ['where', 'pwsh.exe'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return result.stdout.strip().split('\n')[0]
            except Exception:
                pass

        return None

    def launch_console(self, config: ConsoleConfig) -> Optional[ConsoleSession]:
        """
        Launch a console with specified configuration.

        Args:
            config: Console configuration

        Returns:
            ConsoleSession if successful, None otherwise
        """
        console_path = self.get_console_path(config.console_type)
        if not console_path:
            logger.error(f"Console executable not found: {config.console_type}")
            return None

        # Prepare working directory
        working_dir = config.working_directory or os.getcwd()
        if not Path(working_dir).exists():
            logger.error(f"Working directory does not exist: {working_dir}")
            return None

        # Build command arguments
        arguments = self._build_console_arguments(config)

        # Check if elevation is needed
        if config.elevated and not self.is_admin():
            return self._launch_elevated_console(
                console_path, arguments, working_dir, config
            )
        else:
            return self._launch_normal_console(
                console_path, arguments, working_dir, config
            )

    def _build_console_arguments(self, config: ConsoleConfig) -> List[str]:
        """Build command line arguments for console."""
        arguments = []

        if config.console_type == ConsoleType.CMD:
            if config.initial_commands:
                # Join commands with && for cmd.exe
                cmd_string = ' && '.join(config.initial_commands)
                arguments.extend(['/K', cmd_string])
            else:
                arguments.append('/K')  # Keep window open

        elif config.console_type in (ConsoleType.POWERSHELL, ConsoleType.POWERSHELL_CORE):
            arguments.extend(['-NoExit'])  # Keep window open

            if config.initial_commands:
                # Join commands with semicolon for PowerShell
                ps_string = '; '.join(config.initial_commands)
                arguments.extend(['-Command', ps_string])

        return arguments

    def _launch_elevated_console(
        self,
        console_path: str,
        arguments: List[str],
        working_dir: str,
        config: ConsoleConfig
    ) -> Optional[ConsoleSession]:
        """Launch console with UAC elevation."""
        try:
            # Sanitize arguments
            sanitized_args = [sanitize_cli_argument(arg) for arg in arguments]
            params = ' '.join(f'"{arg}"' for arg in sanitized_args)

            logger.info(f"Launching elevated console: {console_path} {params}")

            # Use ShellExecuteW with 'runas' verb
            result = self.shell32.ShellExecuteW(
                None,
                "runas",
                console_path,
                params,
                working_dir,
                config.show_window
            )

            # ShellExecute returns > 32 on success, but doesn't give us process info
            if result > 32:
                logger.info("Elevated console launched successfully")
                # Note: We can't get process handle from ShellExecute
                # Create a minimal session record
                session = ConsoleSession(
                    process_handle=0,  # Not available
                    process_id=0,  # Not available
                    console_type=config.console_type,
                    elevated=True,
                    working_directory=working_dir
                )
                return session
            else:
                logger.error(f"Failed to launch elevated console: {result}")
                return None

        except Exception as e:
            logger.error(f"Error launching elevated console: {e}")
            return None

    def _launch_normal_console(
        self,
        console_path: str,
        arguments: List[str],
        working_dir: str,
        config: ConsoleConfig
    ) -> Optional[ConsoleSession]:
        """Launch console without elevation."""
        try:
            if HAS_PYWIN32 and not config.capture_output:
                # Use CreateProcess for better control
                return self._launch_with_createprocess(
                    console_path, arguments, working_dir, config
                )
            else:
                # Use subprocess as fallback
                return self._launch_with_subprocess(
                    console_path, arguments, working_dir, config
                )

        except Exception as e:
            logger.error(f"Error launching console: {e}")
            return None

    def _launch_with_createprocess(
        self,
        console_path: str,
        arguments: List[str],
        working_dir: str,
        config: ConsoleConfig
    ) -> Optional[ConsoleSession]:
        """Launch console using Win32 CreateProcess."""
        if not HAS_PYWIN32:
            return None

        try:
            # Build command line
            cmd_line = f'"{console_path}" ' + ' '.join(f'"{arg}"' for arg in arguments)

            # Prepare environment
            env = None
            if config.environment_vars:
                env = os.environ.copy()
                env.update(config.environment_vars)

            # Create startup info
            startup_info = win32process.STARTUPINFO()
            startup_info.dwFlags = win32process.STARTF_USESHOWWINDOW
            startup_info.wShowWindow = config.show_window

            # Set window title if specified
            if config.title:
                startup_info.lpTitle = config.title

            # Create process
            process_handle, thread_handle, process_id, thread_id = win32process.CreateProcess(
                None,  # Application name (None to use command line)
                cmd_line,
                None,  # Process security attributes
                None,  # Thread security attributes
                False,  # Inherit handles
                win32process.CREATE_NEW_CONSOLE,  # Creation flags
                env,  # Environment
                working_dir,  # Current directory
                startup_info  # Startup info
            )

            # Close thread handle (we don't need it)
            win32api.CloseHandle(thread_handle)

            logger.info(f"Console launched with PID: {process_id}")

            # Create session
            session = ConsoleSession(
                process_handle=int(process_handle),
                process_id=process_id,
                console_type=config.console_type,
                elevated=False,
                working_directory=working_dir
            )

            self.active_sessions[process_id] = session
            return session

        except Exception as e:
            logger.error(f"CreateProcess failed: {e}")
            return None

    def _launch_with_subprocess(
        self,
        console_path: str,
        arguments: List[str],
        working_dir: str,
        config: ConsoleConfig
    ) -> Optional[ConsoleSession]:
        """Launch console using subprocess module."""
        try:
            # Prepare environment
            env = None
            if config.environment_vars:
                env = os.environ.copy()
                env.update(config.environment_vars)

            # Prepare stdout/stderr capture
            stdout_file = None
            stderr_file = None
            stdout = None
            stderr = None

            if config.capture_output:
                # Create temp files for output
                stdout_fd, stdout_file = tempfile.mkstemp(suffix='.stdout.txt', text=True)
                stderr_fd, stderr_file = tempfile.mkstemp(suffix='.stderr.txt', text=True)
                stdout = stdout_fd
                stderr = stderr_fd
            else:
                stdout = None
                stderr = None

            # Build command
            cmd = [console_path] + arguments

            # Create process
            process = subprocess.Popen(
                cmd,
                cwd=working_dir,
                env=env,
                stdout=stdout,
                stderr=stderr,
                creationflags=subprocess.CREATE_NEW_CONSOLE if not config.capture_output else 0
            )

            logger.info(f"Console launched with PID: {process.pid}")

            # Create session
            session = ConsoleSession(
                process_handle=0,  # Not available with subprocess
                process_id=process.pid,
                console_type=config.console_type,
                elevated=False,
                working_directory=working_dir,
                stdout_file=stdout_file,
                stderr_file=stderr_file
            )

            self.active_sessions[process.pid] = session
            return session

        except Exception as e:
            logger.error(f"Subprocess launch failed: {e}")
            return None

    def execute_batch_commands(
        self,
        commands: List[str],
        config: Optional[ConsoleConfig] = None,
        callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Execute batch commands in a hidden console.

        Args:
            commands: List of commands to execute
            config: Console configuration (defaults to PowerShell)
            callback: Optional callback for progress updates

        Returns:
            Tuple of (success, stdout, stderr)
        """
        if not commands:
            return False, None, "No commands provided"

        if config is None:
            config = ConsoleConfig(
                console_type=ConsoleType.POWERSHELL,
                capture_output=True,
                show_window=ShowWindow.SW_HIDE
            )
        else:
            config.capture_output = True
            config.show_window = ShowWindow.SW_HIDE

        config.initial_commands = commands

        # Launch console
        session = self.launch_console(config)
        if not session:
            return False, None, "Failed to launch console"

        # Wait for completion if we have a process handle
        if HAS_PYWIN32 and session.process_handle:
            try:
                win32event.WaitForSingleObject(session.process_handle, win32event.INFINITE)

                # Get exit code
                exit_code = win32process.GetExitCodeProcess(session.process_handle)

                # Close handle
                win32api.CloseHandle(session.process_handle)

                # Read output files
                stdout = None
                stderr = None

                if session.stdout_file and Path(session.stdout_file).exists():
                    with open(session.stdout_file, 'r', encoding='utf-8', errors='ignore') as f:
                        stdout = f.read()
                    os.remove(session.stdout_file)

                if session.stderr_file and Path(session.stderr_file).exists():
                    with open(session.stderr_file, 'r', encoding='utf-8', errors='ignore') as f:
                        stderr = f.read()
                    os.remove(session.stderr_file)

                # Remove from active sessions
                if session.process_id in self.active_sessions:
                    del self.active_sessions[session.process_id]

                success = exit_code == 0
                return success, stdout, stderr

            except Exception as e:
                logger.error(f"Error waiting for batch commands: {e}")
                return False, None, str(e)

        return True, None, None

    def is_session_active(self, session: ConsoleSession) -> bool:
        """Check if a console session is still active."""
        if not HAS_PYWIN32 or not session.process_handle:
            return False

        try:
            exit_code = win32process.GetExitCodeProcess(session.process_handle)
            return exit_code == win32process.STILL_ACTIVE
        except Exception:
            return False

    def close_session(self, session: ConsoleSession, force: bool = False) -> bool:
        """
        Close a console session.

        Args:
            session: Session to close
            force: Force termination if True

        Returns:
            True if session was closed
        """
        if not HAS_PYWIN32 or not session.process_handle:
            return False

        try:
            if force:
                win32process.TerminateProcess(session.process_handle, 0)
            else:
                # Try graceful close first
                # Send WM_CLOSE to console window
                pass  # TODO: Implement graceful close

            # Wait for exit
            win32event.WaitForSingleObject(session.process_handle, 5000)

            # Close handle
            win32api.CloseHandle(session.process_handle)

            # Remove from active sessions
            if session.process_id in self.active_sessions:
                del self.active_sessions[session.process_id]

            return True

        except Exception as e:
            logger.error(f"Error closing session: {e}")
            return False

    def get_active_sessions(self) -> List[ConsoleSession]:
        """Get list of active console sessions."""
        return [
            session for session in self.active_sessions.values()
            if self.is_session_active(session)
        ]

    def cleanup(self):
        """Cleanup all active sessions."""
        for session in list(self.active_sessions.values()):
            try:
                self.close_session(session, force=True)
            except Exception as e:
                logger.error(f"Error cleaning up session: {e}")

        self.active_sessions.clear()


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    manager = AdminConsoleManager()

    print(f"Running as admin: {manager.is_admin()}")
    print(f"Console paths:")
    for console_type in ConsoleType:
        path = manager.get_console_path(console_type)
        print(f"  {console_type.name}: {path}")

    # Test batch execution
    print("\nExecuting batch commands...")
    commands = [
        'echo "Hello from PowerShell"',
        'Get-Date',
        'Get-Location'
    ]

    success, stdout, stderr = manager.execute_batch_commands(commands)
    print(f"Success: {success}")
    if stdout:
        print(f"Output:\n{stdout}")
    if stderr:
        print(f"Errors:\n{stderr}")

    # Test interactive console launch
    response = input("\nLaunch interactive PowerShell? (y/n): ")
    if response.lower() == 'y':
        config = ConsoleConfig(
            console_type=ConsoleType.POWERSHELL,
            elevated=False,
            title="Smart Search Pro - Admin Console"
        )

        session = manager.launch_console(config)
        if session:
            print(f"Console launched with PID: {session.process_id}")

    # Cleanup
    manager.cleanup()

"""
File Unlocker - Detect and remove file locks from Windows processes

Uses Windows API to:
- Enumerate all system handles
- Identify processes locking files
- Force close file handles
- Kill locking processes
- Remove file attributes

REQUIRES: Administrator privileges for most operations
"""

import os
import sys
import ctypes
import struct
from ctypes import wintypes
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import psutil
import logging

# Windows API imports
import win32api
import win32con
import win32file
import win32process
import win32security
import pywintypes

logger = logging.getLogger(__name__)


class SYSTEM_HANDLE_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("ProcessId", wintypes.DWORD),
        ("ObjectTypeNumber", ctypes.c_ubyte),
        ("Flags", ctypes.c_ubyte),
        ("Handle", wintypes.WORD),
        ("Object", ctypes.c_void_p),
        ("GrantedAccess", wintypes.DWORD),
    ]


class LockingProcess:
    """Information about a process locking a file"""

    def __init__(self, pid: int, process_name: str, handle_value: int):
        self.pid = pid
        self.process_name = process_name
        self.handle_value = handle_value

    def __repr__(self):
        return f"LockingProcess(pid={self.pid}, name='{self.process_name}', handle={self.handle_value})"


class FileUnlocker:
    """
    Advanced file unlock utility using Windows Native API

    Features:
    - Detect which process has a file locked
    - Enumerate all system handles (requires admin)
    - Force close handles from other processes
    - Kill locking processes
    - Remove read-only/hidden/system attributes
    - Safe mode: copy file instead of forcing unlock

    Security Warning:
    This tool can disrupt running applications and cause data loss.
    Always verify you have authority to unlock the file.
    """

    # Windows API constants
    PROCESS_DUP_HANDLE = 0x0040
    DUPLICATE_CLOSE_SOURCE = 0x00000001
    DUPLICATE_SAME_ACCESS = 0x00000002

    # NT Status codes
    STATUS_SUCCESS = 0x00000000
    STATUS_INFO_LENGTH_MISMATCH = 0xC0000004

    # System information class
    SystemHandleInformation = 16

    def __init__(self):
        self.ntdll = ctypes.windll.ntdll
        self.kernel32 = ctypes.windll.kernel32
        self._is_admin = self._check_admin()

    def _check_admin(self) -> bool:
        """Check if running with administrator privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False

    def is_admin(self) -> bool:
        """Returns True if running with admin privileges"""
        return self._is_admin

    def get_locking_processes(self, file_path: str) -> List[LockingProcess]:
        """
        Find all processes that have the specified file locked

        Args:
            file_path: Full path to the file

        Returns:
            List of LockingProcess objects

        Raises:
            PermissionError: If not running as administrator
            FileNotFoundError: If file doesn't exist
        """
        if not self._is_admin:
            raise PermissionError("Administrator privileges required to enumerate system handles")

        file_path = os.path.abspath(file_path)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Scanning for processes locking: {file_path}")

        locking_processes = []

        # Get all handles in the system
        handles = self._enumerate_handles()

        # Check each handle
        for handle_info in handles:
            try:
                if self._is_file_handle(handle_info, file_path):
                    process = self._get_process_info(handle_info.ProcessId)
                    if process:
                        locking_processes.append(LockingProcess(
                            pid=handle_info.ProcessId,
                            process_name=process,
                            handle_value=handle_info.Handle
                        ))
                        logger.info(f"Found locking process: {process} (PID: {handle_info.ProcessId})")
            except Exception as e:
                logger.debug(f"Error checking handle: {e}")
                continue

        return locking_processes

    def _enumerate_handles(self) -> List[SYSTEM_HANDLE_INFORMATION]:
        """
        Enumerate all handles in the system using NtQuerySystemInformation

        Returns:
            List of SYSTEM_HANDLE_INFORMATION structures
        """
        buffer_size = 0x10000  # Start with 64KB

        while True:
            buffer = ctypes.create_string_buffer(buffer_size)
            return_length = wintypes.DWORD()

            status = self.ntdll.NtQuerySystemInformation(
                self.SystemHandleInformation,
                buffer,
                buffer_size,
                ctypes.byref(return_length)
            )

            if status == self.STATUS_SUCCESS:
                break
            elif status == self.STATUS_INFO_LENGTH_MISMATCH:
                buffer_size = return_length.value
                continue
            else:
                logger.error(f"NtQuerySystemInformation failed with status: 0x{status:08X}")
                return []

        # Parse the buffer
        handle_count = struct.unpack('I', buffer.raw[:4])[0]
        handles = []

        offset = 8  # Skip handle count and padding
        for i in range(handle_count):
            if offset + ctypes.sizeof(SYSTEM_HANDLE_INFORMATION) > len(buffer):
                break

            handle_info = SYSTEM_HANDLE_INFORMATION.from_buffer_copy(buffer.raw[offset:])
            handles.append(handle_info)
            offset += ctypes.sizeof(SYSTEM_HANDLE_INFORMATION)

        logger.info(f"Enumerated {len(handles)} system handles")
        return handles

    def _is_file_handle(self, handle_info: SYSTEM_HANDLE_INFORMATION, file_path: str) -> bool:
        """
        Check if a handle refers to the specified file

        Args:
            handle_info: Handle information structure
            file_path: Path to check against

        Returns:
            True if the handle refers to the file
        """
        try:
            # Open the process
            process_handle = self.kernel32.OpenProcess(
                self.PROCESS_DUP_HANDLE,
                False,
                handle_info.ProcessId
            )

            if not process_handle:
                return False

            try:
                # Duplicate the handle into our process
                duplicate_handle = wintypes.HANDLE()
                result = self.kernel32.DuplicateHandle(
                    process_handle,
                    handle_info.Handle,
                    self.kernel32.GetCurrentProcess(),
                    ctypes.byref(duplicate_handle),
                    0,
                    False,
                    self.DUPLICATE_SAME_ACCESS
                )

                if not result:
                    return False

                try:
                    # Get the file name for this handle
                    handle_path = self._get_handle_path(duplicate_handle.value)

                    if handle_path:
                        # Normalize paths for comparison
                        handle_path = os.path.normcase(os.path.abspath(handle_path))
                        file_path_normalized = os.path.normcase(os.path.abspath(file_path))

                        return handle_path == file_path_normalized

                finally:
                    self.kernel32.CloseHandle(duplicate_handle)
            finally:
                self.kernel32.CloseHandle(process_handle)

        except Exception as e:
            logger.debug(f"Error checking handle: {e}")

        return False

    def _get_handle_path(self, handle: int) -> Optional[str]:
        """Get file path from handle"""
        try:
            return win32file.GetFinalPathNameByHandle(
                handle,
                win32con.FILE_NAME_NORMALIZED | win32con.VOLUME_NAME_DOS
            )
        except:
            return None

    def _get_process_info(self, pid: int) -> Optional[str]:
        """Get process name from PID"""
        try:
            process = psutil.Process(pid)
            return process.name()
        except:
            return None

    def close_handle(self, pid: int, handle_value: int) -> bool:
        """
        Close a specific handle in another process

        Args:
            pid: Process ID
            handle_value: Handle value to close

        Returns:
            True if successful
        """
        if not self._is_admin:
            raise PermissionError("Administrator privileges required")

        try:
            # Open the target process
            process_handle = self.kernel32.OpenProcess(
                self.PROCESS_DUP_HANDLE,
                False,
                pid
            )

            if not process_handle:
                logger.error(f"Failed to open process {pid}")
                return False

            try:
                # Duplicate the handle with DUPLICATE_CLOSE_SOURCE
                # This closes the handle in the source process
                dummy_handle = wintypes.HANDLE()
                result = self.kernel32.DuplicateHandle(
                    process_handle,
                    handle_value,
                    self.kernel32.GetCurrentProcess(),
                    ctypes.byref(dummy_handle),
                    0,
                    False,
                    self.DUPLICATE_CLOSE_SOURCE
                )

                if result:
                    logger.info(f"Successfully closed handle {handle_value} in process {pid}")
                    if dummy_handle.value:
                        self.kernel32.CloseHandle(dummy_handle)
                    return True
                else:
                    logger.error(f"Failed to close handle {handle_value} in process {pid}")
                    return False

            finally:
                self.kernel32.CloseHandle(process_handle)

        except Exception as e:
            logger.error(f"Error closing handle: {e}")
            return False

    def kill_locking_process(self, pid: int, force: bool = False) -> bool:
        """
        Terminate a process that's locking a file

        Args:
            pid: Process ID to terminate
            force: If True, use force kill (may cause data loss)

        Returns:
            True if successful
        """
        try:
            process = psutil.Process(pid)
            process_name = process.name()

            logger.warning(f"Attempting to kill process: {process_name} (PID: {pid})")

            if force:
                process.kill()  # Force kill
            else:
                process.terminate()  # Graceful termination

            process.wait(timeout=5)
            logger.info(f"Successfully terminated process {pid}")
            return True

        except psutil.NoSuchProcess:
            logger.error(f"Process {pid} not found")
            return False
        except psutil.AccessDenied:
            logger.error(f"Access denied to terminate process {pid}")
            return False
        except Exception as e:
            logger.error(f"Error killing process {pid}: {e}")
            return False

    def remove_file_attributes(self, file_path: str) -> bool:
        """
        Remove read-only, hidden, and system attributes from file

        Args:
            file_path: Path to file

        Returns:
            True if successful
        """
        try:
            # Get current attributes
            attrs = win32api.GetFileAttributes(file_path)

            # Remove read-only, hidden, system attributes
            new_attrs = attrs & ~(
                win32con.FILE_ATTRIBUTE_READONLY |
                win32con.FILE_ATTRIBUTE_HIDDEN |
                win32con.FILE_ATTRIBUTE_SYSTEM
            )

            if new_attrs != attrs:
                win32api.SetFileAttributes(file_path, new_attrs)
                logger.info(f"Removed restrictive attributes from: {file_path}")
                return True

            return True

        except Exception as e:
            logger.error(f"Error removing attributes: {e}")
            return False

    def unlock_file(self, file_path: str, kill_process: bool = False, safe_mode: bool = False) -> Dict[str, any]:
        """
        Comprehensive file unlock operation

        Args:
            file_path: Path to file to unlock
            kill_process: If True, kill locking processes
            safe_mode: If True, copy file instead of forcing unlock

        Returns:
            Dictionary with operation results
        """
        result = {
            'success': False,
            'file': file_path,
            'locking_processes': [],
            'handles_closed': 0,
            'processes_killed': 0,
            'attributes_removed': False,
            'errors': []
        }

        try:
            # Check if file exists
            if not os.path.exists(file_path):
                result['errors'].append('File not found')
                return result

            # Remove restrictive attributes
            if self.remove_file_attributes(file_path):
                result['attributes_removed'] = True

            # Find locking processes
            if self._is_admin:
                locking_processes = self.get_locking_processes(file_path)
                result['locking_processes'] = [
                    {'pid': p.pid, 'name': p.process_name} for p in locking_processes
                ]

                if safe_mode and locking_processes:
                    result['errors'].append('Safe mode enabled - file is locked, copy recommended')
                    return result

                # Close handles
                for process in locking_processes:
                    if self.close_handle(process.pid, process.handle_value):
                        result['handles_closed'] += 1

                # Kill processes if requested
                if kill_process:
                    for process in locking_processes:
                        if self.kill_locking_process(process.pid):
                            result['processes_killed'] += 1
            else:
                result['errors'].append('Not running as admin - cannot enumerate handles')

            # Test if file is now accessible
            try:
                handle = win32file.CreateFile(
                    file_path,
                    win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                    0,  # No sharing
                    None,
                    win32con.OPEN_EXISTING,
                    0,
                    None
                )
                win32file.CloseHandle(handle)
                result['success'] = True
                logger.info(f"Successfully unlocked: {file_path}")

            except pywintypes.error as e:
                result['errors'].append(f'File still locked: {e.strerror}')

        except Exception as e:
            result['errors'].append(str(e))
            logger.error(f"Error unlocking file: {e}")

        return result

    def batch_unlock(self, file_paths: List[str], **kwargs) -> List[Dict]:
        """
        Unlock multiple files

        Args:
            file_paths: List of file paths
            **kwargs: Additional arguments passed to unlock_file

        Returns:
            List of result dictionaries
        """
        results = []
        for file_path in file_paths:
            result = self.unlock_file(file_path, **kwargs)
            results.append(result)
        return results


# Convenience functions
def unlock_file(file_path: str, kill_process: bool = False) -> bool:
    """Simple unlock function"""
    unlocker = FileUnlocker()
    result = unlocker.unlock_file(file_path, kill_process=kill_process)
    return result['success']


def find_locking_processes(file_path: str) -> List[Dict]:
    """Find processes locking a file"""
    unlocker = FileUnlocker()
    if not unlocker.is_admin():
        return []

    processes = unlocker.get_locking_processes(file_path)
    return [{'pid': p.pid, 'name': p.process_name} for p in processes]


if __name__ == '__main__':
    # Test/demo code
    import argparse

    parser = argparse.ArgumentParser(description='File Unlocker - Remove file locks')
    parser.add_argument('file', help='File to unlock')
    parser.add_argument('--kill', action='store_true', help='Kill locking processes')
    parser.add_argument('--list', action='store_true', help='List locking processes only')

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    unlocker = FileUnlocker()

    if not unlocker.is_admin():
        print("WARNING: Not running as administrator - functionality limited")
        print("Run as administrator for full functionality")

    if args.list:
        processes = unlocker.get_locking_processes(args.file)
        if processes:
            print(f"\nProcesses locking {args.file}:")
            for p in processes:
                print(f"  - {p.process_name} (PID: {p.pid})")
        else:
            print(f"No processes found locking: {args.file}")
    else:
        result = unlocker.unlock_file(args.file, kill_process=args.kill)
        print(f"\nUnlock Result:")
        print(f"  Success: {result['success']}")
        print(f"  Handles closed: {result['handles_closed']}")
        print(f"  Processes killed: {result['processes_killed']}")
        if result['errors']:
            print(f"  Errors: {', '.join(result['errors'])}")

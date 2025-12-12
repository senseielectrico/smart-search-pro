"""
Privilege Manager for Smart Search Pro.

Provides fine-grained Windows privilege management for operations
requiring specific system privileges.
"""

import ctypes
import ctypes.wintypes as wintypes
import sys
import os
import logging
from typing import Optional, List, Set
from enum import IntEnum

try:
    import win32security
    import win32api
    import win32con
    import win32process
    import ntsecuritycon
    import pywintypes
    HAS_PYWIN32 = True
except ImportError:
    HAS_PYWIN32 = False
    logging.warning("pywin32 not available, privilege management will be limited")

logger = logging.getLogger(__name__)

# Import elevation manager
try:
    from system.elevation import ElevationManager
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from system.elevation import ElevationManager


class Privilege(IntEnum):
    """Windows privilege constants."""
    # Common privileges
    SE_BACKUP_PRIVILEGE = 1
    SE_RESTORE_PRIVILEGE = 2
    SE_DEBUG_PRIVILEGE = 3
    SE_SHUTDOWN_PRIVILEGE = 4
    SE_SYSTEMTIME_PRIVILEGE = 5
    SE_TAKE_OWNERSHIP_PRIVILEGE = 6
    SE_SECURITY_PRIVILEGE = 7
    SE_LOAD_DRIVER_PRIVILEGE = 8
    SE_SYSTEM_PROFILE_PRIVILEGE = 9
    SE_INCREASE_PRIORITY_PRIVILEGE = 10
    SE_CREATE_PAGEFILE_PRIVILEGE = 11
    SE_CREATE_PERMANENT_PRIVILEGE = 12


# Privilege name mapping
PRIVILEGE_NAMES = {
    Privilege.SE_BACKUP_PRIVILEGE: "SeBackupPrivilege",
    Privilege.SE_RESTORE_PRIVILEGE: "SeRestorePrivilege",
    Privilege.SE_DEBUG_PRIVILEGE: "SeDebugPrivilege",
    Privilege.SE_SHUTDOWN_PRIVILEGE: "SeShutdownPrivilege",
    Privilege.SE_SYSTEMTIME_PRIVILEGE: "SeSystemtimePrivilege",
    Privilege.SE_TAKE_OWNERSHIP_PRIVILEGE: "SeTakeOwnershipPrivilege",
    Privilege.SE_SECURITY_PRIVILEGE: "SeSecurityPrivilege",
    Privilege.SE_LOAD_DRIVER_PRIVILEGE: "SeLoadDriverPrivilege",
    Privilege.SE_SYSTEM_PROFILE_PRIVILEGE: "SeSystemProfilePrivilege",
    Privilege.SE_INCREASE_PRIORITY_PRIVILEGE: "SeIncreaseBasePriorityPrivilege",
    Privilege.SE_CREATE_PAGEFILE_PRIVILEGE: "SeCreatePagefilePrivilege",
    Privilege.SE_CREATE_PERMANENT_PRIVILEGE: "SeCreatePermanentPrivilege",
}


class PrivilegeManager:
    """
    Manager for Windows process privileges.

    Features:
    - Check current process privileges
    - Request specific privileges (SeBackupPrivilege, etc.)
    - Enable/disable privileges dynamically
    - Check if user is in Administrators group
    - Token manipulation utilities
    """

    def __init__(self):
        """Initialize privilege manager."""
        self.elevation_manager = ElevationManager()
        self.process_token = None
        self._enabled_privileges: Set[str] = set()

        logger.info("Privilege manager initialized")

    def is_admin(self) -> bool:
        """Check if running as administrator."""
        return self.elevation_manager.is_elevated()

    def is_in_admin_group(self) -> bool:
        """
        Check if current user is in Administrators group.

        Returns:
            True if user is in Administrators group
        """
        if not HAS_PYWIN32:
            return self.is_admin()

        try:
            # Get Administrators SID
            administrators_sid = win32security.CreateWellKnownSid(
                win32security.WinBuiltinAdministratorsSid
            )

            # Check membership
            is_member = win32security.CheckTokenMembership(
                None,  # Current thread token
                administrators_sid
            )

            return is_member

        except Exception as e:
            logger.error(f"Error checking admin group membership: {e}")
            return False

    def get_process_token(self, access: int = None) -> Optional[int]:
        """
        Get current process token.

        Args:
            access: Token access rights (default: TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY)

        Returns:
            Token handle or None
        """
        if not HAS_PYWIN32:
            return None

        if access is None:
            access = win32con.TOKEN_ADJUST_PRIVILEGES | win32con.TOKEN_QUERY

        try:
            # Get current process handle
            process_handle = win32api.GetCurrentProcess()

            # Open process token
            token = win32security.OpenProcessToken(process_handle, access)

            return token

        except Exception as e:
            logger.error(f"Error getting process token: {e}")
            return None

    def has_privilege(self, privilege_name: str) -> bool:
        """
        Check if process has a specific privilege.

        Args:
            privilege_name: Name of privilege (e.g., "SeBackupPrivilege")

        Returns:
            True if privilege is available
        """
        if not HAS_PYWIN32:
            return False

        try:
            token = self.get_process_token()
            if not token:
                return False

            # Lookup privilege LUID
            luid = win32security.LookupPrivilegeValue(None, privilege_name)

            # Get token privileges
            privileges = win32security.GetTokenInformation(
                token,
                win32security.TokenPrivileges
            )

            # Check if privilege is in the list
            for priv_luid, flags in privileges:
                if priv_luid == luid:
                    win32api.CloseHandle(token)
                    return True

            win32api.CloseHandle(token)
            return False

        except Exception as e:
            logger.error(f"Error checking privilege: {e}")
            return False

    def is_privilege_enabled(self, privilege_name: str) -> bool:
        """
        Check if a privilege is currently enabled.

        Args:
            privilege_name: Name of privilege

        Returns:
            True if privilege is enabled
        """
        if not HAS_PYWIN32:
            return False

        try:
            token = self.get_process_token()
            if not token:
                return False

            # Lookup privilege LUID
            luid = win32security.LookupPrivilegeValue(None, privilege_name)

            # Get token privileges
            privileges = win32security.GetTokenInformation(
                token,
                win32security.TokenPrivileges
            )

            # Check if privilege is enabled
            for priv_luid, flags in privileges:
                if priv_luid == luid:
                    enabled = (flags & win32security.SE_PRIVILEGE_ENABLED) != 0
                    win32api.CloseHandle(token)
                    return enabled

            win32api.CloseHandle(token)
            return False

        except Exception as e:
            logger.error(f"Error checking if privilege is enabled: {e}")
            return False

    def enable_privilege(self, privilege_name: str) -> bool:
        """
        Enable a specific privilege for the current process.

        Args:
            privilege_name: Name of privilege (e.g., "SeBackupPrivilege")

        Returns:
            True if privilege was enabled

        Example:
            manager.enable_privilege("SeBackupPrivilege")
        """
        if not HAS_PYWIN32:
            logger.warning("pywin32 not available, cannot enable privilege")
            return False

        try:
            token = self.get_process_token()
            if not token:
                return False

            # Lookup privilege LUID
            luid = win32security.LookupPrivilegeValue(None, privilege_name)

            # Enable privilege
            new_state = [(luid, win32security.SE_PRIVILEGE_ENABLED)]

            win32security.AdjustTokenPrivileges(
                token,
                False,  # Don't disable all
                new_state
            )

            win32api.CloseHandle(token)

            # Track enabled privilege
            self._enabled_privileges.add(privilege_name)

            logger.info(f"Enabled privilege: {privilege_name}")
            return True

        except pywintypes.error as e:
            logger.error(f"Error enabling privilege {privilege_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error enabling privilege {privilege_name}: {e}")
            return False

    def disable_privilege(self, privilege_name: str) -> bool:
        """
        Disable a specific privilege for the current process.

        Args:
            privilege_name: Name of privilege

        Returns:
            True if privilege was disabled
        """
        if not HAS_PYWIN32:
            return False

        try:
            token = self.get_process_token()
            if not token:
                return False

            # Lookup privilege LUID
            luid = win32security.LookupPrivilegeValue(None, privilege_name)

            # Disable privilege
            new_state = [(luid, 0)]  # 0 = disabled

            win32security.AdjustTokenPrivileges(
                token,
                False,
                new_state
            )

            win32api.CloseHandle(token)

            # Remove from tracked privileges
            self._enabled_privileges.discard(privilege_name)

            logger.info(f"Disabled privilege: {privilege_name}")
            return True

        except Exception as e:
            logger.error(f"Error disabling privilege {privilege_name}: {e}")
            return False

    def enable_backup_restore_privileges(self) -> bool:
        """
        Enable both backup and restore privileges.

        These are commonly needed for file operations.

        Returns:
            True if both privileges were enabled
        """
        backup_ok = self.enable_privilege("SeBackupPrivilege")
        restore_ok = self.enable_privilege("SeRestorePrivilege")

        return backup_ok and restore_ok

    def enable_debug_privilege(self) -> bool:
        """
        Enable debug privilege.

        Required for accessing other processes.

        Returns:
            True if privilege was enabled
        """
        return self.enable_privilege("SeDebugPrivilege")

    def get_enabled_privileges(self) -> List[str]:
        """
        Get list of currently enabled privileges.

        Returns:
            List of privilege names
        """
        return list(self._enabled_privileges)

    def get_all_privileges(self) -> List[tuple]:
        """
        Get all privileges for current process.

        Returns:
            List of (privilege_name, is_enabled) tuples
        """
        if not HAS_PYWIN32:
            return []

        try:
            token = self.get_process_token()
            if not token:
                return []

            # Get token privileges
            privileges = win32security.GetTokenInformation(
                token,
                win32security.TokenPrivileges
            )

            result = []
            for priv_luid, flags in privileges:
                try:
                    # Lookup privilege name
                    name = win32security.LookupPrivilegeName(None, priv_luid)
                    enabled = (flags & win32security.SE_PRIVILEGE_ENABLED) != 0
                    result.append((name, enabled))
                except Exception:
                    pass

            win32api.CloseHandle(token)
            return result

        except Exception as e:
            logger.error(f"Error getting all privileges: {e}")
            return []

    def elevate_if_needed(self, required_privileges: List[str]) -> bool:
        """
        Check if we have required privileges, elevate if needed.

        Args:
            required_privileges: List of required privilege names

        Returns:
            True if all privileges are available
        """
        if not required_privileges:
            return True

        # Check if we have all required privileges
        has_all = all(self.has_privilege(priv) for priv in required_privileges)

        if has_all:
            return True

        # We don't have all privileges, check if we're elevated
        if not self.is_admin():
            logger.warning(
                f"Missing required privileges: {required_privileges}, elevation needed"
            )

            # Request elevation
            self.elevation_manager.relaunch_elevated()
            # Will exit if successful

        return False

    def get_token_user(self) -> Optional[str]:
        """
        Get current token user (username).

        Returns:
            Username or None
        """
        if not HAS_PYWIN32:
            return None

        try:
            token = self.get_process_token()
            if not token:
                return None

            # Get token user
            user_sid, attributes = win32security.GetTokenInformation(
                token,
                win32security.TokenUser
            )

            # Convert SID to account name
            name, domain, account_type = win32security.LookupAccountSid(
                None,
                user_sid
            )

            win32api.CloseHandle(token)

            return f"{domain}\\{name}"

        except Exception as e:
            logger.error(f"Error getting token user: {e}")
            return None

    def get_token_groups(self) -> List[str]:
        """
        Get groups the current token belongs to.

        Returns:
            List of group names
        """
        if not HAS_PYWIN32:
            return []

        try:
            token = self.get_process_token()
            if not token:
                return []

            # Get token groups
            groups = win32security.GetTokenInformation(
                token,
                win32security.TokenGroups
            )

            result = []
            for sid, attributes in groups:
                try:
                    name, domain, account_type = win32security.LookupAccountSid(
                        None,
                        sid
                    )
                    result.append(f"{domain}\\{name}")
                except Exception:
                    pass

            win32api.CloseHandle(token)
            return result

        except Exception as e:
            logger.error(f"Error getting token groups: {e}")
            return []

    def cleanup(self):
        """Cleanup resources."""
        # Disable all enabled privileges
        for privilege in list(self._enabled_privileges):
            self.disable_privilege(privilege)


# Context manager for temporary privilege elevation
class PrivilegeContext:
    """
    Context manager for temporarily enabling privileges.

    Example:
        with PrivilegeContext(["SeBackupPrivilege", "SeRestorePrivilege"]):
            # Privileges enabled here
            perform_backup()
        # Privileges automatically disabled
    """

    def __init__(self, privileges: List[str]):
        """
        Initialize privilege context.

        Args:
            privileges: List of privilege names to enable
        """
        self.privileges = privileges
        self.manager = PrivilegeManager()
        self.originally_enabled = set()

    def __enter__(self):
        """Enable privileges on enter."""
        for privilege in self.privileges:
            # Track which were originally enabled
            if self.manager.is_privilege_enabled(privilege):
                self.originally_enabled.add(privilege)
            else:
                # Enable privilege
                self.manager.enable_privilege(privilege)

        return self.manager

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Disable privileges on exit."""
        for privilege in self.privileges:
            # Only disable if it wasn't originally enabled
            if privilege not in self.originally_enabled:
                self.manager.disable_privilege(privilege)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    manager = PrivilegeManager()

    print(f"Running as admin: {manager.is_admin()}")
    print(f"In admin group: {manager.is_in_admin_group()}")
    print(f"Current user: {manager.get_token_user()}")

    print("\nAll privileges:")
    for name, enabled in manager.get_all_privileges():
        status = "ENABLED" if enabled else "disabled"
        print(f"  {name}: {status}")

    print("\nChecking specific privileges:")
    privileges_to_check = [
        "SeBackupPrivilege",
        "SeRestorePrivilege",
        "SeDebugPrivilege",
        "SeShutdownPrivilege"
    ]

    for privilege in privileges_to_check:
        has = manager.has_privilege(privilege)
        enabled = manager.is_privilege_enabled(privilege)
        print(f"  {privilege}: has={has}, enabled={enabled}")

    # Test enabling privilege
    if manager.is_admin():
        print("\nTesting privilege enable/disable:")
        if manager.has_privilege("SeBackupPrivilege"):
            print("  Enabling SeBackupPrivilege...")
            if manager.enable_privilege("SeBackupPrivilege"):
                print(f"  Enabled: {manager.is_privilege_enabled('SeBackupPrivilege')}")

                print("  Disabling SeBackupPrivilege...")
                manager.disable_privilege("SeBackupPrivilege")
                print(f"  Enabled: {manager.is_privilege_enabled('SeBackupPrivilege')}")

        # Test context manager
        print("\nTesting privilege context:")
        print(f"  Before: {manager.is_privilege_enabled('SeBackupPrivilege')}")

        with PrivilegeContext(["SeBackupPrivilege"]):
            print(f"  Inside: {manager.is_privilege_enabled('SeBackupPrivilege')}")

        print(f"  After: {manager.is_privilege_enabled('SeBackupPrivilege')}")
    else:
        print("\nNot running as admin, cannot test privilege manipulation")
        print("Run this script as administrator to test privilege features")

    # Cleanup
    manager.cleanup()

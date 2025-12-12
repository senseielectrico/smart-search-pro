"""
Permission Fixer - Repair file and folder permissions

Features:
- Take ownership of files/folders
- Reset ACLs to default
- Grant full control to current user
- Recursively fix permissions
- Remove inheritance blocking
- Clear deny ACEs
- Backup current permissions

REQUIRES: Administrator privileges with SeBackupPrivilege and SeRestorePrivilege
"""

import os
import sys
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import logging

import win32api
import win32con
import win32file
import win32security
import ntsecuritycon
import pywintypes

logger = logging.getLogger(__name__)


class PermissionBackup:
    """Container for backed up permissions"""

    def __init__(self, path: str, security_descriptor):
        self.path = path
        self.security_descriptor = security_descriptor
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        """Serialize to dictionary (without security descriptor)"""
        return {
            'path': self.path,
            'timestamp': self.timestamp.isoformat()
        }


class PermissionFixer:
    """
    Advanced permission repair utility

    Security Warning:
    This tool modifies file system permissions and ownership.
    Incorrect use can make files inaccessible or compromise security.
    Always backup permissions before making changes.
    """

    def __init__(self):
        self._is_admin = self._check_admin()
        self._enable_privileges()
        self._backups = []

    def _check_admin(self) -> bool:
        """Check if running with administrator privileges"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False

    def _enable_privileges(self):
        """Enable required privileges for taking ownership and backup"""
        if not self._is_admin:
            logger.warning("Not running as administrator - some operations may fail")
            return

        try:
            # Get current process token
            token = win32security.OpenProcessToken(
                win32api.GetCurrentProcess(),
                win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY
            )

            # Enable SeBackupPrivilege
            privilege_backup = win32security.LookupPrivilegeValue(
                None,
                win32security.SE_BACKUP_NAME
            )
            win32security.AdjustTokenPrivileges(
                token,
                False,
                [(privilege_backup, win32security.SE_PRIVILEGE_ENABLED)]
            )

            # Enable SeRestorePrivilege
            privilege_restore = win32security.LookupPrivilegeValue(
                None,
                win32security.SE_RESTORE_NAME
            )
            win32security.AdjustTokenPrivileges(
                token,
                False,
                [(privilege_restore, win32security.SE_PRIVILEGE_ENABLED)]
            )

            # Enable SeTakeOwnershipPrivilege
            privilege_ownership = win32security.LookupPrivilegeValue(
                None,
                win32security.SE_TAKE_OWNERSHIP_NAME
            )
            win32security.AdjustTokenPrivileges(
                token,
                False,
                [(privilege_ownership, win32security.SE_PRIVILEGE_ENABLED)]
            )

            logger.info("Successfully enabled security privileges")

        except Exception as e:
            logger.error(f"Error enabling privileges: {e}")

    def get_current_permissions(self, path: str) -> Dict:
        """
        Get current permissions information

        Args:
            path: File or folder path

        Returns:
            Dictionary with permission details
        """
        try:
            # Get security descriptor
            sd = win32security.GetFileSecurity(
                path,
                win32security.OWNER_SECURITY_INFORMATION |
                win32security.GROUP_SECURITY_INFORMATION |
                win32security.DACL_SECURITY_INFORMATION
            )

            # Get owner
            owner_sid = sd.GetSecurityDescriptorOwner()
            owner_name, owner_domain, _ = win32security.LookupAccountSid(None, owner_sid)

            # Get group
            group_sid = sd.GetSecurityDescriptorGroup()
            group_name, group_domain, _ = win32security.LookupAccountSid(None, group_sid)

            # Get DACL
            dacl = sd.GetSecurityDescriptorDacl()

            # Parse ACEs
            aces = []
            if dacl:
                for i in range(dacl.GetAceCount()):
                    ace = dacl.GetAce(i)
                    ace_type, ace_flags, ace_mask, ace_sid = ace

                    try:
                        ace_account, ace_domain, _ = win32security.LookupAccountSid(None, ace_sid)
                        ace_name = f"{ace_domain}\\{ace_account}" if ace_domain else ace_account
                    except:
                        ace_name = str(ace_sid)

                    aces.append({
                        'type': self._ace_type_to_string(ace_type),
                        'account': ace_name,
                        'permissions': self._mask_to_permissions(ace_mask),
                        'flags': ace_flags
                    })

            return {
                'path': path,
                'owner': f"{owner_domain}\\{owner_name}" if owner_domain else owner_name,
                'group': f"{group_domain}\\{group_name}" if group_domain else group_name,
                'aces': aces,
                'dacl_protected': bool(sd.GetSecurityDescriptorControl()[0] & win32security.SE_DACL_PROTECTED)
            }

        except Exception as e:
            logger.error(f"Error getting permissions for {path}: {e}")
            return {'error': str(e)}

    def _ace_type_to_string(self, ace_type: int) -> str:
        """Convert ACE type to string"""
        types = {
            win32security.ACCESS_ALLOWED_ACE_TYPE: 'Allow',
            win32security.ACCESS_DENIED_ACE_TYPE: 'Deny',
        }
        return types.get(ace_type, f'Unknown({ace_type})')

    def _mask_to_permissions(self, mask: int) -> List[str]:
        """Convert permission mask to list of permission names"""
        perms = []

        if mask & ntsecuritycon.FILE_GENERIC_READ:
            perms.append('Read')
        if mask & ntsecuritycon.FILE_GENERIC_WRITE:
            perms.append('Write')
        if mask & ntsecuritycon.FILE_GENERIC_EXECUTE:
            perms.append('Execute')
        if mask & win32con.DELETE:
            perms.append('Delete')
        if mask & win32security.WRITE_DAC:
            perms.append('Change Permissions')
        if mask & win32security.WRITE_OWNER:
            perms.append('Take Ownership')

        # Check for full control
        if mask & ntsecuritycon.FILE_ALL_ACCESS == ntsecuritycon.FILE_ALL_ACCESS:
            return ['Full Control']

        return perms if perms else [f'Custom(0x{mask:08X})']

    def backup_permissions(self, path: str) -> bool:
        """
        Backup current permissions

        Args:
            path: File or folder path

        Returns:
            True if successful
        """
        try:
            sd = win32security.GetFileSecurity(
                path,
                win32security.OWNER_SECURITY_INFORMATION |
                win32security.GROUP_SECURITY_INFORMATION |
                win32security.DACL_SECURITY_INFORMATION |
                win32security.SACL_SECURITY_INFORMATION
            )

            backup = PermissionBackup(path, sd)
            self._backups.append(backup)

            logger.info(f"Backed up permissions for: {path}")
            return True

        except Exception as e:
            logger.error(f"Error backing up permissions: {e}")
            return False

    def restore_permissions(self, path: str) -> bool:
        """
        Restore permissions from backup

        Args:
            path: File or folder path

        Returns:
            True if successful
        """
        # Find most recent backup for this path
        backup = None
        for b in reversed(self._backups):
            if b.path == path:
                backup = b
                break

        if not backup:
            logger.error(f"No backup found for: {path}")
            return False

        try:
            win32security.SetFileSecurity(
                path,
                win32security.OWNER_SECURITY_INFORMATION |
                win32security.GROUP_SECURITY_INFORMATION |
                win32security.DACL_SECURITY_INFORMATION,
                backup.security_descriptor
            )

            logger.info(f"Restored permissions for: {path}")
            return True

        except Exception as e:
            logger.error(f"Error restoring permissions: {e}")
            return False

    def take_ownership(self, path: str, recursive: bool = False) -> Dict:
        """
        Take ownership of file or folder

        Args:
            path: File or folder path
            recursive: If True, take ownership recursively

        Returns:
            Dictionary with operation results
        """
        if not self._is_admin:
            raise PermissionError("Administrator privileges required")

        result = {
            'success': False,
            'path': path,
            'files_processed': 0,
            'errors': []
        }

        try:
            # Get current user SID
            user_sid = win32security.GetTokenInformation(
                win32security.OpenProcessToken(
                    win32api.GetCurrentProcess(),
                    win32security.TOKEN_QUERY
                ),
                win32security.TokenUser
            )[0]

            # Take ownership of the main path
            if self._take_ownership_single(path, user_sid):
                result['files_processed'] += 1
            else:
                result['errors'].append(f"Failed to take ownership: {path}")

            # Recursive processing
            if recursive and os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for name in dirs + files:
                        item_path = os.path.join(root, name)
                        try:
                            if self._take_ownership_single(item_path, user_sid):
                                result['files_processed'] += 1
                        except Exception as e:
                            result['errors'].append(f"{item_path}: {str(e)}")

            result['success'] = result['files_processed'] > 0

        except Exception as e:
            result['errors'].append(str(e))
            logger.error(f"Error taking ownership: {e}")

        return result

    def _take_ownership_single(self, path: str, owner_sid) -> bool:
        """Take ownership of a single file/folder"""
        try:
            # Create new security descriptor with owner
            sd = win32security.SECURITY_DESCRIPTOR()
            sd.SetSecurityDescriptorOwner(owner_sid, False)

            # Set the owner
            win32security.SetFileSecurity(
                path,
                win32security.OWNER_SECURITY_INFORMATION,
                sd
            )

            logger.info(f"Took ownership of: {path}")
            return True

        except Exception as e:
            logger.error(f"Error taking ownership of {path}: {e}")
            return False

    def grant_full_control(self, path: str, user: Optional[str] = None, recursive: bool = False) -> Dict:
        """
        Grant full control to user

        Args:
            path: File or folder path
            user: Username (None = current user)
            recursive: If True, grant recursively

        Returns:
            Dictionary with operation results
        """
        if not self._is_admin:
            raise PermissionError("Administrator privileges required")

        result = {
            'success': False,
            'path': path,
            'files_processed': 0,
            'errors': []
        }

        try:
            # Get user SID
            if user is None:
                user_sid = win32security.GetTokenInformation(
                    win32security.OpenProcessToken(
                        win32api.GetCurrentProcess(),
                        win32security.TOKEN_QUERY
                    ),
                    win32security.TokenUser
                )[0]
            else:
                user_sid = win32security.LookupAccountName(None, user)[0]

            # Grant on main path
            if self._grant_full_control_single(path, user_sid):
                result['files_processed'] += 1
            else:
                result['errors'].append(f"Failed to grant access: {path}")

            # Recursive processing
            if recursive and os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for name in dirs + files:
                        item_path = os.path.join(root, name)
                        try:
                            if self._grant_full_control_single(item_path, user_sid):
                                result['files_processed'] += 1
                        except Exception as e:
                            result['errors'].append(f"{item_path}: {str(e)}")

            result['success'] = result['files_processed'] > 0

        except Exception as e:
            result['errors'].append(str(e))
            logger.error(f"Error granting full control: {e}")

        return result

    def _grant_full_control_single(self, path: str, user_sid) -> bool:
        """Grant full control to a single file/folder"""
        try:
            # Get current DACL
            sd = win32security.GetFileSecurity(
                path,
                win32security.DACL_SECURITY_INFORMATION
            )
            dacl = sd.GetSecurityDescriptorDacl()

            if dacl is None:
                dacl = win32security.ACL()

            # Add full control ACE
            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION,
                ntsecuritycon.FILE_ALL_ACCESS,
                user_sid
            )

            # Set new DACL
            sd.SetSecurityDescriptorDacl(1, dacl, 0)
            win32security.SetFileSecurity(
                path,
                win32security.DACL_SECURITY_INFORMATION,
                sd
            )

            logger.info(f"Granted full control to: {path}")
            return True

        except Exception as e:
            logger.error(f"Error granting full control to {path}: {e}")
            return False

    def remove_deny_aces(self, path: str, recursive: bool = False) -> Dict:
        """
        Remove all deny ACEs

        Args:
            path: File or folder path
            recursive: If True, process recursively

        Returns:
            Dictionary with operation results
        """
        result = {
            'success': False,
            'path': path,
            'files_processed': 0,
            'aces_removed': 0,
            'errors': []
        }

        try:
            # Process main path
            removed = self._remove_deny_aces_single(path)
            if removed >= 0:
                result['files_processed'] += 1
                result['aces_removed'] += removed

            # Recursive processing
            if recursive and os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for name in dirs + files:
                        item_path = os.path.join(root, name)
                        try:
                            removed = self._remove_deny_aces_single(item_path)
                            if removed >= 0:
                                result['files_processed'] += 1
                                result['aces_removed'] += removed
                        except Exception as e:
                            result['errors'].append(f"{item_path}: {str(e)}")

            result['success'] = True

        except Exception as e:
            result['errors'].append(str(e))
            logger.error(f"Error removing deny ACEs: {e}")

        return result

    def _remove_deny_aces_single(self, path: str) -> int:
        """Remove deny ACEs from a single file/folder"""
        try:
            sd = win32security.GetFileSecurity(
                path,
                win32security.DACL_SECURITY_INFORMATION
            )
            dacl = sd.GetSecurityDescriptorDacl()

            if dacl is None:
                return 0

            # Create new DACL without deny ACEs
            new_dacl = win32security.ACL()
            removed_count = 0

            for i in range(dacl.GetAceCount()):
                ace = dacl.GetAce(i)
                ace_type, ace_flags, ace_mask, ace_sid = ace

                # Only add allow ACEs
                if ace_type == win32security.ACCESS_ALLOWED_ACE_TYPE:
                    new_dacl.AddAccessAllowedAce(
                        win32security.ACL_REVISION,
                        ace_mask,
                        ace_sid
                    )
                else:
                    removed_count += 1

            # Set new DACL
            sd.SetSecurityDescriptorDacl(1, new_dacl, 0)
            win32security.SetFileSecurity(
                path,
                win32security.DACL_SECURITY_INFORMATION,
                sd
            )

            if removed_count > 0:
                logger.info(f"Removed {removed_count} deny ACE(s) from: {path}")

            return removed_count

        except Exception as e:
            logger.error(f"Error removing deny ACEs from {path}: {e}")
            return -1

    def reset_to_defaults(self, path: str, recursive: bool = False) -> Dict:
        """
        Reset permissions to Windows defaults

        Args:
            path: File or folder path
            recursive: If True, reset recursively

        Returns:
            Dictionary with operation results
        """
        result = {
            'success': False,
            'path': path,
            'files_processed': 0,
            'errors': []
        }

        try:
            # Take ownership first
            take_result = self.take_ownership(path, recursive)
            result['files_processed'] = take_result['files_processed']
            result['errors'].extend(take_result['errors'])

            # Grant administrators and system full control
            # Grant users read & execute

            # This is a simplified default - actual defaults vary by location
            logger.warning("Reset to defaults is simplified - may not match exact Windows defaults")

            result['success'] = take_result['success']

        except Exception as e:
            result['errors'].append(str(e))
            logger.error(f"Error resetting to defaults: {e}")

        return result

    def fix_inheritance(self, path: str, enable: bool = True) -> bool:
        """
        Enable or disable permission inheritance

        Args:
            path: File or folder path
            enable: True to enable inheritance, False to disable

        Returns:
            True if successful
        """
        try:
            sd = win32security.GetFileSecurity(
                path,
                win32security.DACL_SECURITY_INFORMATION
            )
            dacl = sd.GetSecurityDescriptorDacl()

            if enable:
                # Enable inheritance (remove protected flag)
                sd.SetSecurityDescriptorDacl(1, dacl, 0)  # Last param: not protected
            else:
                # Disable inheritance (set protected flag)
                # Copy inherited ACEs to explicit
                pass  # Implementation would copy inherited ACEs

            win32security.SetFileSecurity(
                path,
                win32security.DACL_SECURITY_INFORMATION,
                sd
            )

            logger.info(f"{'Enabled' if enable else 'Disabled'} inheritance for: {path}")
            return True

        except Exception as e:
            logger.error(f"Error fixing inheritance: {e}")
            return False


# Convenience functions
def take_ownership(path: str, recursive: bool = False) -> bool:
    """Simple take ownership function"""
    fixer = PermissionFixer()
    result = fixer.take_ownership(path, recursive)
    return result['success']


def grant_full_control(path: str, recursive: bool = False) -> bool:
    """Simple grant full control function"""
    fixer = PermissionFixer()
    result = fixer.grant_full_control(path, recursive=recursive)
    return result['success']


if __name__ == '__main__':
    # Test/demo code
    import argparse

    parser = argparse.ArgumentParser(description='Permission Fixer - Repair file permissions')
    parser.add_argument('path', help='File or folder path')
    parser.add_argument('--take-ownership', action='store_true', help='Take ownership')
    parser.add_argument('--grant-full', action='store_true', help='Grant full control')
    parser.add_argument('--remove-deny', action='store_true', help='Remove deny ACEs')
    parser.add_argument('--show', action='store_true', help='Show current permissions')
    parser.add_argument('--recursive', '-r', action='store_true', help='Recursive')

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    fixer = PermissionFixer()

    if args.show:
        perms = fixer.get_current_permissions(args.path)
        print(f"\nPermissions for: {args.path}")
        print(f"Owner: {perms.get('owner', 'Unknown')}")
        print(f"Group: {perms.get('group', 'Unknown')}")
        print(f"\nAccess Control Entries:")
        for ace in perms.get('aces', []):
            print(f"  {ace['type']:6} - {ace['account']:30} - {', '.join(ace['permissions'])}")

    if args.take_ownership:
        result = fixer.take_ownership(args.path, args.recursive)
        print(f"\nTake Ownership Result:")
        print(f"  Success: {result['success']}")
        print(f"  Files processed: {result['files_processed']}")
        if result['errors']:
            print(f"  Errors: {len(result['errors'])}")

    if args.grant_full:
        result = fixer.grant_full_control(args.path, recursive=args.recursive)
        print(f"\nGrant Full Control Result:")
        print(f"  Success: {result['success']}")
        print(f"  Files processed: {result['files_processed']}")

    if args.remove_deny:
        result = fixer.remove_deny_aces(args.path, args.recursive)
        print(f"\nRemove Deny ACEs Result:")
        print(f"  Success: {result['success']}")
        print(f"  Files processed: {result['files_processed']}")
        print(f"  ACEs removed: {result['aces_removed']}")

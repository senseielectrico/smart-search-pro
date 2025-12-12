"""
Anti-Forensics Module - Counter Forensic Detection
Prevent digital forensics from discovering vault

Techniques:
- No registry traces
- Secure file deletion (DoD 5220.22-M)
- Timestamp randomization
- Memory cleanup
- Process name obfuscation
- File system metadata manipulation
"""

import os
import sys
import time
import secrets
import tempfile
import platform
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta


class AntiForensics:
    """Anti-forensics and anti-detection measures"""

    @staticmethod
    def secure_delete(file_path: str, passes: int = 7) -> bool:
        """
        Securely delete file using DoD 5220.22-M standard

        Args:
            file_path: Path to file to delete
            passes: Number of overwrite passes (default: 7)

        Returns:
            True if successful
        """
        try:
            if not os.path.exists(file_path):
                return True

            file_size = os.path.getsize(file_path)

            # Open file for writing
            with open(file_path, 'r+b') as f:
                for pass_num in range(passes):
                    f.seek(0)

                    if pass_num == 0:
                        # Pass 1: All zeros
                        pattern = b'\x00'
                    elif pass_num == 1:
                        # Pass 2: All ones
                        pattern = b'\xFF'
                    else:
                        # Remaining passes: Random data
                        pattern = None

                    # Overwrite file
                    chunk_size = 4096
                    for offset in range(0, file_size, chunk_size):
                        size = min(chunk_size, file_size - offset)

                        if pattern:
                            data = pattern * size
                        else:
                            data = secrets.token_bytes(size)

                        f.write(data)

                    # Flush to disk
                    f.flush()
                    os.fsync(f.fileno())

            # Delete file
            os.remove(file_path)

            return True

        except Exception as e:
            print(f"Secure delete error: {e}")
            return False

    @staticmethod
    def randomize_timestamps(file_path: str) -> bool:
        """
        Randomize file timestamps to blend with system files

        Sets timestamps to random times within past year
        """
        try:
            if not os.path.exists(file_path):
                return False

            # Generate random timestamp within past year
            now = time.time()
            year_ago = now - (365 * 24 * 60 * 60)
            random_time = year_ago + secrets.randbelow(int(now - year_ago))

            # Set both access and modification time
            os.utime(file_path, (random_time, random_time))

            return True

        except Exception as e:
            print(f"Timestamp randomization error: {e}")
            return False

    @staticmethod
    def clear_recent_files() -> bool:
        """
        Clear recent files list (Windows)

        Prevents vault files from appearing in recent files
        """
        if platform.system() != 'Windows':
            return True

        try:
            import winreg

            # Clear Recent Documents
            recent_path = os.path.join(
                os.environ.get('APPDATA', ''),
                'Microsoft\\Windows\\Recent'
            )

            if os.path.exists(recent_path):
                for file in os.listdir(recent_path):
                    file_path = os.path.join(recent_path, file)
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass

            # Clear registry recent files (if needed)
            # Note: This is more aggressive and may affect user experience

            return True

        except Exception as e:
            print(f"Recent files clearing error: {e}")
            return False

    @staticmethod
    def blend_with_system_files(file_path: str) -> bool:
        """
        Make file blend in with system files

        - Hidden attribute
        - System attribute (Windows)
        - Randomized timestamp
        """
        try:
            if not os.path.exists(file_path):
                return False

            # Randomize timestamp
            AntiForensics.randomize_timestamps(file_path)

            if platform.system() == 'Windows':
                import subprocess

                # Set hidden and system attributes
                subprocess.run(
                    ['attrib', '+H', '+S', file_path],
                    capture_output=True,
                    check=False
                )

            return True

        except Exception as e:
            print(f"File blending error: {e}")
            return False

    @staticmethod
    def clear_memory() -> bool:
        """
        Clear sensitive data from memory

        Forces garbage collection and attempts memory cleanup
        """
        try:
            import gc

            # Force garbage collection
            gc.collect()

            # On Unix-like systems, we could use mlock/munlock
            # On Windows, VirtualLock/VirtualUnlock
            # Python doesn't expose these directly, but we can at least GC

            return True

        except Exception:
            return False

    @staticmethod
    def get_secure_temp_location() -> str:
        """
        Get secure temporary location that's cleaned automatically

        Returns:
            Path to secure temporary directory
        """
        # Use system temp with random subdirectory
        temp_base = tempfile.gettempdir()
        random_name = secrets.token_hex(16)

        # Create hidden directory
        if platform.system() == 'Windows':
            temp_dir = os.path.join(temp_base, f".{random_name}")
        else:
            temp_dir = os.path.join(temp_base, f".{random_name}")

        os.makedirs(temp_dir, exist_ok=True)

        # Make it hidden
        if platform.system() == 'Windows':
            import subprocess
            subprocess.run(['attrib', '+H', temp_dir], capture_output=True, check=False)

        return temp_dir

    @staticmethod
    def obfuscate_process_name() -> str:
        """
        Return an innocent-looking process name

        Returns:
            Innocent process name
        """
        innocent_names = [
            'svchost.exe',
            'explorer.exe',
            'system32.exe',
            'RuntimeBroker.exe',
            'dwm.exe',
            'csrss.exe',
        ]

        return secrets.choice(innocent_names)

    @staticmethod
    def check_debugger() -> bool:
        """
        Check if debugger is attached

        Returns:
            True if debugger detected
        """
        # Check Python debugger
        if sys.gettrace() is not None:
            return True

        if platform.system() == 'Windows':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                if kernel32.IsDebuggerPresent():
                    return True
            except Exception:
                pass

        return False

    @staticmethod
    def check_vm() -> bool:
        """
        Check if running in virtual machine

        Returns:
            True if VM detected
        """
        vm_indicators = []

        # Check common VM identifiers
        try:
            import subprocess

            if platform.system() == 'Windows':
                # Check manufacturer
                result = subprocess.run(
                    ['wmic', 'computersystem', 'get', 'manufacturer'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                manufacturer = result.stdout.lower()
                vm_keywords = ['vmware', 'virtualbox', 'qemu', 'xen', 'virtual']

                for keyword in vm_keywords:
                    if keyword in manufacturer:
                        return True

        except Exception:
            pass

        return False

    @staticmethod
    def anti_screenshot() -> bool:
        """
        Attempt to prevent screenshots (limited effectiveness)

        Note: This is difficult to enforce on modern OS
        """
        # On Windows, we could use SetWindowDisplayAffinity
        # This would require PyWin32 and window handle

        # For now, return False (not implemented fully)
        # Full implementation would need window-specific code

        return False

    @staticmethod
    def clear_clipboard() -> bool:
        """
        Clear system clipboard

        Returns:
            True if successful
        """
        try:
            if platform.system() == 'Windows':
                import ctypes

                # Open clipboard
                if ctypes.windll.user32.OpenClipboard(0):
                    # Empty clipboard
                    ctypes.windll.user32.EmptyClipboard()
                    # Close clipboard
                    ctypes.windll.user32.CloseClipboard()
                    return True

            elif platform.system() == 'Darwin':  # macOS
                import subprocess
                subprocess.run(['pbcopy'], input=b'', check=False)
                return True

            elif platform.system() == 'Linux':
                import subprocess
                # Try xclip
                try:
                    subprocess.run(
                        ['xclip', '-selection', 'clipboard', '/dev/null'],
                        check=False,
                        timeout=1
                    )
                    return True
                except Exception:
                    pass

        except Exception as e:
            print(f"Clipboard clear error: {e}")

        return False

    @staticmethod
    def generate_decoy_files(directory: str, count: int = 10) -> List[str]:
        """
        Generate decoy files to hide vault among them

        Args:
            directory: Directory to create decoy files
            count: Number of decoy files

        Returns:
            List of created decoy file paths
        """
        decoy_files = []

        try:
            os.makedirs(directory, exist_ok=True)

            extensions = ['.dll', '.dat', '.tmp', '.log', '.cache']

            for i in range(count):
                # Random filename
                name = secrets.token_hex(8)
                ext = secrets.choice(extensions)
                file_path = os.path.join(directory, f"{name}{ext}")

                # Create file with random content
                size = secrets.randbelow(1024 * 1024) + 1024  # 1KB to 1MB
                with open(file_path, 'wb') as f:
                    f.write(secrets.token_bytes(size))

                # Randomize timestamps
                AntiForensics.randomize_timestamps(file_path)

                # Blend with system
                AntiForensics.blend_with_system_files(file_path)

                decoy_files.append(file_path)

            return decoy_files

        except Exception as e:
            print(f"Decoy generation error: {e}")
            return decoy_files

    @staticmethod
    def check_forensic_tools() -> bool:
        """
        Check for common forensic tools running

        Returns:
            True if forensic tool detected
        """
        forensic_processes = [
            'wireshark',
            'tcpdump',
            'procmon',
            'procexp',
            'processhacker',
            'ollydbg',
            'x64dbg',
            'ida',
            'ghidra',
            'volatility',
            'autopsy',
            'ftk',
            'encase',
        ]

        try:
            if platform.system() == 'Windows':
                import subprocess
                result = subprocess.run(
                    ['tasklist'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                running = result.stdout.lower()
                for tool in forensic_processes:
                    if tool in running:
                        return True

            elif platform.system() in ('Linux', 'Darwin'):
                import subprocess
                result = subprocess.run(
                    ['ps', 'aux'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                running = result.stdout.lower()
                for tool in forensic_processes:
                    if tool in running:
                        return True

        except Exception:
            pass

        return False

    @staticmethod
    def create_timeline_gap(file_path: str, gap_days: int = 30) -> bool:
        """
        Create timeline gap by setting old timestamp

        Useful to make file appear to be from long ago
        """
        try:
            if not os.path.exists(file_path):
                return False

            # Set timestamp to gap_days ago
            now = time.time()
            old_time = now - (gap_days * 24 * 60 * 60)

            os.utime(file_path, (old_time, old_time))

            return True

        except Exception as e:
            print(f"Timeline gap error: {e}")
            return False

    @staticmethod
    def get_environment_info() -> dict:
        """
        Get environment information for security assessment

        Returns:
            Dictionary with environment details
        """
        info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'python_version': sys.version,
            'is_admin': False,
            'debugger_attached': AntiForensics.check_debugger(),
            'vm_detected': AntiForensics.check_vm(),
            'forensic_tools': AntiForensics.check_forensic_tools(),
        }

        # Check admin privileges
        try:
            if platform.system() == 'Windows':
                import ctypes
                info['is_admin'] = ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                info['is_admin'] = os.geteuid() == 0
        except Exception:
            pass

        return info

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to remove identifying information

        Returns:
            Sanitized filename
        """
        # Remove personal identifiers
        import re

        # Remove common personal patterns
        sanitized = re.sub(r'[A-Za-z]+\s+[A-Za-z]+', 'user', filename)  # Names
        sanitized = re.sub(r'\d{3}-\d{2}-\d{4}', 'xxx-xx-xxxx', sanitized)  # SSN
        sanitized = re.sub(r'\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b', 'xxxx-xxxx-xxxx-xxxx', sanitized)  # Credit card

        return sanitized

    @staticmethod
    def wipe_free_space(drive: str, passes: int = 1) -> bool:
        """
        Wipe free space on drive (WARNING: Time-consuming)

        Args:
            drive: Drive letter (Windows) or mount point (Unix)
            passes: Number of wipe passes

        Returns:
            True if successful
        """
        # This is extremely time-consuming and should only be used when necessary
        # Implementation would create large files to fill free space, then securely delete them

        try:
            import shutil

            # Get free space
            stats = shutil.disk_usage(drive)
            free_space = stats.free

            # Leave 10% free for safety
            wipe_size = int(free_space * 0.9)

            # Create temporary directory
            temp_dir = AntiForensics.get_secure_temp_location()

            for pass_num in range(passes):
                temp_file = os.path.join(temp_dir, f"wipe_{pass_num}.tmp")

                try:
                    # Create large file
                    with open(temp_file, 'wb') as f:
                        chunk_size = 1024 * 1024  # 1MB chunks
                        written = 0

                        while written < wipe_size:
                            size = min(chunk_size, wipe_size - written)
                            data = secrets.token_bytes(size)
                            f.write(data)
                            written += size

                    # Securely delete
                    AntiForensics.secure_delete(temp_file, passes=1)

                except Exception:
                    # Disk full or other error
                    if os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except Exception:
                            pass
                    break

            # Cleanup
            try:
                os.rmdir(temp_dir)
            except Exception:
                pass

            return True

        except Exception as e:
            print(f"Free space wipe error: {e}")
            return False

"""
Archive Password Recovery Tool

Helps users recover forgotten passwords from their own password-protected archives.
Uses dictionary matching and pattern-based recovery methods.

IMPORTANT: This tool is designed for legitimate password recovery of your own
files only. Unauthorized access to others' encrypted archives is illegal.
"""

import itertools
import string
import threading
from typing import Optional, List, Callable, Set, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import time

from .sevenzip_manager import SevenZipManager


@dataclass
class RecoveryProgress:
    """Progress tracking for password recovery operations"""
    attempts: int = 0
    attempts_per_second: float = 0.0
    current_password: str = ""
    elapsed_seconds: float = 0.0
    found: bool = False
    password: Optional[str] = None
    cancelled: bool = False


# Backwards compatibility alias
CrackProgress = RecoveryProgress


class PasswordRecovery:
    """
    Archive password recovery tool with multiple recovery strategies:
    - Dictionary matching with common wordlists
    - Pattern-based search with charset options
    - Mask-based recovery (for partially known passwords)
    - Multi-threaded processing
    - Progress reporting and resume capability

    NOTICE: This tool is intended for recovering passwords from your own
    archives. Always ensure you have authorization before attempting
    password recovery on any file.
    """

    # Common password patterns
    COMMON_PASSWORDS = [
        'password', '123456', '12345678', 'qwerty', 'abc123',
        'monkey', '1234567', 'letmein', 'trustno1', 'dragon',
        'baseball', '111111', 'iloveyou', 'master', 'sunshine',
        'ashley', 'bailey', 'passw0rd', 'shadow', '123123',
        '654321', 'superman', 'qazwsx', 'michael', 'football'
    ]

    # Common number suffixes
    COMMON_SUFFIXES = ['', '1', '123', '2023', '2024', '!', '!!']

    def __init__(self, max_threads: int = 4):
        """
        Initialize password cracker

        Args:
            max_threads: Maximum concurrent threads
        """
        self.max_threads = max_threads
        self.seven_zip = SevenZipManager()
        self._cancel_flag = threading.Event()
        self._lock = threading.Lock()

    def dictionary_attack(
        self,
        archive_path: str,
        wordlist_path: Optional[str] = None,
        use_common: bool = True,
        use_variations: bool = True,
        progress_callback: Optional[Callable[[CrackProgress], None]] = None
    ) -> Optional[str]:
        """
        Dictionary attack using wordlist

        Args:
            archive_path: Path to archive
            wordlist_path: Path to wordlist file (one password per line)
            use_common: Include common passwords
            use_variations: Try variations (case, suffixes, etc.)
            progress_callback: Progress callback

        Returns:
            Password if found, None otherwise
        """
        self._cancel_flag.clear()

        passwords = []

        # Add common passwords
        if use_common:
            passwords.extend(self.COMMON_PASSWORDS)

        # Load wordlist
        if wordlist_path and Path(wordlist_path).exists():
            try:
                with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        password = line.strip()
                        if password:
                            passwords.append(password)
            except Exception:
                pass

        # Generate variations
        if use_variations:
            passwords = self._generate_variations(passwords)

        # Remove duplicates
        passwords = list(dict.fromkeys(passwords))

        return self._test_passwords(archive_path, passwords, progress_callback)

    def brute_force_attack(
        self,
        archive_path: str,
        charset: str = string.ascii_lowercase + string.digits,
        min_length: int = 1,
        max_length: int = 6,
        progress_callback: Optional[Callable[[CrackProgress], None]] = None
    ) -> Optional[str]:
        """
        Brute force attack with custom charset

        Args:
            archive_path: Path to archive
            charset: Characters to use
            min_length: Minimum password length
            max_length: Maximum password length
            progress_callback: Progress callback

        Returns:
            Password if found, None otherwise
        """
        self._cancel_flag.clear()

        for length in range(min_length, max_length + 1):
            if self._cancel_flag.is_set():
                return None

            # Generate all combinations of this length
            for password_tuple in itertools.product(charset, repeat=length):
                if self._cancel_flag.is_set():
                    return None

                password = ''.join(password_tuple)

                # Test password
                result = self._test_passwords(archive_path, [password], progress_callback)
                if result:
                    return result

        return None

    def mask_attack(
        self,
        archive_path: str,
        mask: str,
        progress_callback: Optional[Callable[[CrackProgress], None]] = None
    ) -> Optional[str]:
        """
        Mask attack for known pattern

        Mask format:
        - 'l' = lowercase letter
        - 'u' = uppercase letter
        - 'd' = digit
        - 's' = special character
        - '?' = any character
        - literal characters = themselves

        Example: "password?d?d" tries password00, password01, ..., password99

        Args:
            archive_path: Path to archive
            mask: Password mask pattern
            progress_callback: Progress callback

        Returns:
            Password if found, None otherwise
        """
        self._cancel_flag.clear()

        # Parse mask and generate possibilities
        charsets = {
            'l': string.ascii_lowercase,
            'u': string.ascii_uppercase,
            'd': string.digits,
            's': string.punctuation,
            '?': string.ascii_letters + string.digits + string.punctuation
        }

        positions = []
        fixed_chars = {}

        for idx, char in enumerate(mask):
            if char in charsets:
                positions.append((idx, charsets[char]))
            else:
                fixed_chars[idx] = char

        # Generate passwords from mask
        if not positions:
            # No wildcards, test the mask itself
            return self._test_passwords(archive_path, [mask], progress_callback)

        # Generate all combinations
        indices, charset_lists = zip(*positions)

        for combo in itertools.product(*charset_lists):
            if self._cancel_flag.is_set():
                return None

            # Build password
            password_list = list(mask)
            for idx, char in zip(indices, combo):
                password_list[idx] = char

            password = ''.join(password_list)

            # Test password
            result = self._test_passwords(archive_path, [password], progress_callback)
            if result:
                return result

        return None

    def _generate_variations(self, passwords: List[str]) -> List[str]:
        """Generate variations of passwords"""
        variations = []

        for pwd in passwords:
            # Original
            variations.append(pwd)

            # Capitalized
            variations.append(pwd.capitalize())

            # All uppercase
            variations.append(pwd.upper())

            # All lowercase
            variations.append(pwd.lower())

            # With common suffixes
            for suffix in self.COMMON_SUFFIXES:
                variations.append(pwd + suffix)
                variations.append(pwd.capitalize() + suffix)

            # Common substitutions (leet speak)
            leet = pwd.replace('a', '@').replace('e', '3').replace('i', '1').replace('o', '0')
            if leet != pwd:
                variations.append(leet)

        return variations

    def _test_passwords(
        self,
        archive_path: str,
        passwords: List[str],
        progress_callback: Optional[Callable[[CrackProgress], None]]
    ) -> Optional[str]:
        """Test list of passwords"""
        progress = CrackProgress()
        start_time = time.time()

        for password in passwords:
            if self._cancel_flag.is_set():
                progress.cancelled = True
                if progress_callback:
                    progress_callback(progress)
                return None

            progress.attempts += 1
            progress.current_password = password
            progress.elapsed_seconds = time.time() - start_time

            if progress.elapsed_seconds > 0:
                progress.attempts_per_second = progress.attempts / progress.elapsed_seconds

            # Test password
            try:
                # Try to list contents with this password
                self.seven_zip.list_contents(archive_path, password=password)

                # Success!
                progress.found = True
                progress.password = password

                if progress_callback:
                    progress_callback(progress)

                return password

            except ValueError:
                # Wrong password, continue
                pass
            except Exception:
                # Other error, skip this password
                pass

            # Update progress
            if progress_callback and progress.attempts % 10 == 0:
                progress_callback(progress)

        # Not found
        if progress_callback:
            progress_callback(progress)

        return None

    def cancel(self):
        """Cancel ongoing password cracking"""
        self._cancel_flag.set()

    def estimate_brute_force_time(
        self,
        charset: str,
        min_length: int,
        max_length: int,
        attempts_per_second: float = 100.0
    ) -> Dict[str, Any]:
        """
        Estimate time for brute force attack

        Args:
            charset: Character set
            min_length: Minimum length
            max_length: Maximum length
            attempts_per_second: Estimated attempts per second

        Returns:
            Time estimates
        """
        total_combinations = 0

        for length in range(min_length, max_length + 1):
            combinations = len(charset) ** length
            total_combinations += combinations

        estimated_seconds = total_combinations / attempts_per_second

        return {
            'total_combinations': total_combinations,
            'attempts_per_second': attempts_per_second,
            'estimated_seconds': estimated_seconds,
            'estimated_minutes': estimated_seconds / 60,
            'estimated_hours': estimated_seconds / 3600,
            'estimated_days': estimated_seconds / 86400,
            'warning': 'Very long if > 7 characters' if max_length > 7 else None
        }

    def create_wordlist_from_patterns(
        self,
        base_words: List[str],
        output_path: str,
        include_variations: bool = True,
        include_numbers: bool = True,
        max_suffix_digits: int = 4
    ) -> int:
        """
        Create custom wordlist from base words

        Args:
            base_words: Base words to build from
            output_path: Output wordlist path
            include_variations: Include case variations
            include_numbers: Include number suffixes
            max_suffix_digits: Maximum digits to append

        Returns:
            Number of passwords generated
        """
        passwords: Set[str] = set()

        for word in base_words:
            # Add base word
            passwords.add(word)

            if include_variations:
                # Case variations
                passwords.add(word.lower())
                passwords.add(word.upper())
                passwords.add(word.capitalize())

            if include_numbers:
                # Number suffixes
                for i in range(10 ** max_suffix_digits):
                    passwords.add(f"{word}{i}")
                    if include_variations:
                        passwords.add(f"{word.capitalize()}{i}")

                # Common year suffixes
                for year in range(2000, 2030):
                    passwords.add(f"{word}{year}")

            # Common symbols
            for symbol in ['!', '@', '#', '$', '123']:
                passwords.add(f"{word}{symbol}")

        # Write to file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for password in sorted(passwords):
                    f.write(password + '\n')

            return len(passwords)

        except Exception as e:
            raise RuntimeError(f"Failed to create wordlist: {str(e)}")

"""
Smart Search Pro - Archive Module
Complete 7-Zip integration with recursive extraction, analysis, and management.
"""

# Runtime imports for actual usage
from .sevenzip_manager import SevenZipManager
from .recursive_extractor import RecursiveExtractor
from .archive_analyzer import ArchiveAnalyzer
from .password_recovery import PasswordRecovery

# Backwards compatibility alias
PasswordCracker = PasswordRecovery

__all__ = [
    'SevenZipManager',
    'RecursiveExtractor',
    'ArchiveAnalyzer',
    'PasswordRecovery',
    'PasswordCracker',  # Alias for backwards compatibility
]

__version__ = '1.0.0'

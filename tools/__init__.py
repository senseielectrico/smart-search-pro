"""
Smart Search Pro - File Unlocking and Decryption Tools
Security-focused toolkit for handling locked, encrypted, and inaccessible files.

SECURITY WARNING:
These tools modify file permissions, close handles, and manipulate system resources.
They require elevated privileges and should only be used on files you own or have authorization to access.
Misuse may violate computer security policies and laws.

Author: Smart Search Pro Development Team
Version: 1.1.0
"""

from .file_unlocker import FileUnlocker
from .permission_fixer import PermissionFixer
from .file_decryptor import FileDecryptor
from .cad_file_handler import CADFileHandler

# ExifTool integration components
from .exiftool_wrapper import ExifToolWrapper
from .metadata_analyzer import MetadataAnalyzer
from .metadata_editor import MetadataEditor
from .forensic_report import ForensicReportGenerator

__all__ = [
    'FileUnlocker',
    'PermissionFixer',
    'FileDecryptor',
    'CADFileHandler',
    'ExifToolWrapper',
    'MetadataAnalyzer',
    'MetadataEditor',
    'ForensicReportGenerator'
]

__version__ = '1.1.0'

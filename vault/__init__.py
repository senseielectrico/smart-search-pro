"""
Secure Vault System for Smart Search Pro
Military-grade encryption with plausible deniability

Components:
- secure_vault.py: Core AES-256-GCM encryption engine
- steganography.py: Hide vault in plain sight
- anti_forensics.py: Anti-detection measures
- virtual_fs.py: Virtual encrypted filesystem
"""

from .secure_vault import SecureVault, VaultConfig
from .steganography import SteganographyEngine
from .anti_forensics import AntiForensics
from .virtual_fs import VirtualFileSystem

__all__ = [
    'SecureVault',
    'VaultConfig',
    'SteganographyEngine',
    'AntiForensics',
    'VirtualFileSystem',
]

__version__ = '1.0.0'

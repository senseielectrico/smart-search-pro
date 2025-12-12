"""
Smart Search Pro UI Module
Modern Files App-style interface with PyQt6

Main Components:
- MainWindow: Tabbed interface with modern layout
- SearchPanel: Advanced search with filters
- ResultsPanel: Virtual scrolling table view
- PreviewPanel: File preview with syntax highlighting
- DirectoryTree: Enhanced tree with favorites
- DuplicatesPanel: Grouped duplicates view
- OperationsPanel: File operations manager
- ArchivePanel: 7-Zip archive manager
- ExtractDialog: Archive extraction options
- MetadataPanel: Forensic metadata viewer and editor
- ExifToolDialog: ExifTool operations and configuration
- SettingsDialog: Application settings
- VaultPanel: Secure encrypted vault (Ctrl+Shift+V)
- VaultUnlockDialog: Secure password entry
- Themes: Light/Dark theme system
- Widgets: Custom reusable components
"""

from .main_window import MainWindow
from .search_panel import SearchPanel
from .results_panel import ResultsPanel
from .preview_panel import PreviewPanel
from .directory_tree import DirectoryTree
from .duplicates_panel import DuplicatesPanel
from .operations_panel import OperationsPanel
from .archive_panel import ArchivePanel
from .extract_dialog import ExtractDialog
from .metadata_panel import MetadataPanel
from .exiftool_dialog import ExifToolDialog
from .settings_dialog import SettingsDialog
from .vault_panel import VaultPanel
from .vault_unlock_dialog import VaultUnlockDialog
from .themes import ThemeManager, Theme
from .widgets import FilterChip, SpeedGraph, BreadcrumbBar, ProgressCard, FileIcon
from .result_batcher import SearchResultBatcher, AdaptiveBatcher, CoalescingBatcher, create_batcher

__all__ = [
    'MainWindow',
    'SearchPanel',
    'ResultsPanel',
    'PreviewPanel',
    'DirectoryTree',
    'DuplicatesPanel',
    'OperationsPanel',
    'ArchivePanel',
    'ExtractDialog',
    'MetadataPanel',
    'ExifToolDialog',
    'SettingsDialog',
    'VaultPanel',
    'VaultUnlockDialog',
    'ThemeManager',
    'Theme',
    'FilterChip',
    'SpeedGraph',
    'BreadcrumbBar',
    'ProgressCard',
    'FileIcon',
    'SearchResultBatcher',
    'AdaptiveBatcher',
    'CoalescingBatcher',
    'create_batcher',
]

__version__ = '1.2.0'

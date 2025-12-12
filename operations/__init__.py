"""
Smart Search Pro - File Operations Module
TeraCopy-style high-performance file operations with queue management,
verification, advanced conflict resolution, and batch renaming.
"""

# Import all components for runtime usage
from .manager import OperationsManager
from .copier import FileCopier
from .mover import FileMover
from .verifier import FileVerifier
from .conflicts import ConflictResolver, ConflictAction
from .progress import ProgressTracker, OperationProgress
from .batch_renamer import BatchRenamer, RenamePattern, CaseMode, CollisionMode
from .rename_patterns import PatternLibrary, SavedPattern
from .rename_history import RenameHistory

__all__ = [
    "OperationsManager",
    "FileCopier",
    "FileMover",
    "FileVerifier",
    "ConflictResolver",
    "ConflictAction",
    "ProgressTracker",
    "OperationProgress",
    "BatchRenamer",
    "RenamePattern",
    "CaseMode",
    "CollisionMode",
    "PatternLibrary",
    "SavedPattern",
    "RenameHistory",
]

__version__ = "1.1.0"

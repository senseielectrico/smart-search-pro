"""
Data Viewers Module
===================

Provides comprehensive viewers for databases and data files:
- SQLite database viewer
- JSON file viewer
- Auto-detection factory for multiple formats

Author: Smart Search Team
Date: 2025-12-12
"""

from .database_viewer import DatabaseViewer, SQLiteConnection
from .json_viewer import JSONViewer, JSONTreeModel
from .data_viewer_factory import DataViewerFactory, ViewerType

__all__ = [
    'DatabaseViewer',
    'SQLiteConnection',
    'JSONViewer',
    'JSONTreeModel',
    'DataViewerFactory',
    'ViewerType',
]

__version__ = '1.0.0'

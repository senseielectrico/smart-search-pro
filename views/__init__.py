"""
Views - iOS-style file browser and categorization views
"""

# Lazy imports to avoid circular dependencies
def __getattr__(name):
    if name == 'iPhoneFileView':
        from .iphone_view import iPhoneFileView
        return iPhoneFileView
    elif name == 'CategoryScanner':
        from .category_scanner import CategoryScanner
        return CategoryScanner
    elif name == 'CategoryData':
        from .category_scanner import CategoryData
        return CategoryData
    raise AttributeError(f"module 'views' has no attribute '{name}'")

__all__ = ['iPhoneFileView', 'CategoryScanner', 'CategoryData']

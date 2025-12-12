"""
System Integration Module for Smart Search Pro.

This module provides Windows system integration features including:
- System tray icon and notifications
- Global hotkey registration
- Administrator elevation support
- Windows shell integration
- Autostart management
- Single instance enforcement
"""

# Runtime imports for actual usage
from .tray import SystemTrayIcon
from .hotkeys import HotkeyManager
from .elevation import ElevationManager
from .shell_integration import ShellIntegration
from .autostart import AutostartManager
from .single_instance import SingleInstanceManager

__all__ = [
    "SystemTrayIcon",
    "HotkeyManager",
    "ElevationManager",
    "ShellIntegration",
    "AutostartManager",
    "SingleInstanceManager",
]

__version__ = "1.0.0"

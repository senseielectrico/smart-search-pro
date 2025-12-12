"""
Simple launcher for system integration demo.

This script demonstrates all system integration features in action.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Check Python version
if sys.version_info < (3, 8):
    print("Error: Python 3.8+ required")
    sys.exit(1)

# Check platform
if sys.platform != 'win32':
    print("Error: Windows platform required")
    sys.exit(1)

# Check dependencies
try:
    from PyQt6.QtWidgets import QApplication
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    print("Warning: PyQt6 not installed")
    print("Install with: pip install PyQt6")
    print()

print("=" * 70)
print(" Smart Search Pro - System Integration Demo")
print("=" * 70)
print()

# Show menu
print("Available demos:")
print()
print("1. System Tray Icon Demo (requires PyQt6)")
print("2. Global Hotkeys Demo")
print("3. Single Instance Demo")
print("4. Autostart Manager Demo")
print("5. Elevation Manager Demo")
print("6. Shell Integration Demo (requires admin)")
print("7. Complete Integration Example (requires PyQt6)")
print("8. Run Test Suite")
print()
print("0. Exit")
print()

choice = input("Select demo (0-8): ").strip()

if choice == "0":
    sys.exit(0)

elif choice == "1":
    if not PYQT6_AVAILABLE:
        print("\nError: PyQt6 required for system tray")
        print("Install with: pip install PyQt6")
        sys.exit(1)

    print("\nLaunching System Tray Demo...")
    print("-" * 70)
    os.system(f'python "{Path(__file__).parent / "tray.py"}"')

elif choice == "2":
    print("\nLaunching Global Hotkeys Demo...")
    print("-" * 70)
    print("This will register test hotkeys:")
    print("  - Ctrl+Shift+F: Test hotkey 1")
    print("  - Ctrl+Q: Quit")
    print()
    input("Press Enter to continue...")
    os.system(f'python "{Path(__file__).parent / "hotkeys.py"}"')

elif choice == "3":
    print("\nLaunching Single Instance Demo...")
    print("-" * 70)
    print("This will run for 30 seconds.")
    print("Try running it again in another terminal to test.")
    print()
    input("Press Enter to continue...")
    os.system(f'python "{Path(__file__).parent / "single_instance.py"}"')

elif choice == "4":
    print("\nLaunching Autostart Manager Demo...")
    print("-" * 70)
    os.system(f'python "{Path(__file__).parent / "autostart.py"}"')

elif choice == "5":
    print("\nLaunching Elevation Manager Demo...")
    print("-" * 70)
    os.system(f'python "{Path(__file__).parent / "elevation.py"}"')

elif choice == "6":
    print("\nLaunching Shell Integration Demo...")
    print("-" * 70)
    print("Note: Most operations require administrator privileges")
    print()
    input("Press Enter to continue...")
    os.system(f'python "{Path(__file__).parent / "shell_integration.py"}"')

elif choice == "7":
    if not PYQT6_AVAILABLE:
        print("\nError: PyQt6 required for complete integration example")
        print("Install with: pip install PyQt6")
        sys.exit(1)

    print("\nLaunching Complete Integration Example...")
    print("-" * 70)
    print("This demonstrates all features working together:")
    print("  - Single instance enforcement")
    print("  - System tray icon")
    print("  - Global hotkeys (Ctrl+Shift+F, Ctrl+Shift+S)")
    print("  - Main window")
    print()
    input("Press Enter to continue...")
    os.system(f'python "{Path(__file__).parent / "example_integration.py"}"')

elif choice == "8":
    print("\nLaunching Test Suite...")
    print("-" * 70)
    os.system(f'python "{Path(__file__).parent / "test_system.py"}"')

else:
    print("\nInvalid choice")
    sys.exit(1)

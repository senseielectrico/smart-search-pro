#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Search Pro - Complete Installer
======================================

This script:
1. Installs all dependencies
2. Creates desktop shortcut
3. Creates Start Menu entry
4. Registers context menu (optional)
5. Sets up autostart (optional)

Run as Administrator for full functionality.
"""

import sys
import os
import subprocess
import winreg
import ctypes
from pathlib import Path
import shutil


APP_NAME = "Smart Search Pro"
APP_VERSION = "2.0.0"
APP_DIR = Path(__file__).parent.resolve()
PYTHON_EXE = sys.executable
PYTHONW_EXE = PYTHON_EXE.replace('python.exe', 'pythonw.exe')


def is_admin():
    """Check if running as administrator"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def print_header(text):
    """Print formatted header"""
    print()
    print("=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_step(step, text):
    """Print step information"""
    print(f"\n[{step}] {text}")


def print_success(text):
    """Print success message"""
    print(f"    [OK] {text}")


def print_error(text):
    """Print error message"""
    print(f"    [ERROR] {text}")


def print_info(text):
    """Print info message"""
    print(f"    [INFO] {text}")


def install_dependencies():
    """Install all Python dependencies"""
    print_step(1, "Installing Python dependencies...")

    requirements_file = APP_DIR / "requirements_full.txt"

    if not requirements_file.exists():
        print_error(f"Requirements file not found: {requirements_file}")
        return False

    try:
        # Upgrade pip first
        subprocess.run(
            [PYTHON_EXE, "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            capture_output=True
        )
        print_success("pip upgraded")

        # Install requirements
        result = subprocess.run(
            [PYTHON_EXE, "-m", "pip", "install", "-r", str(requirements_file)],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print_success("All dependencies installed successfully")
            return True
        else:
            print_error(f"Some dependencies failed: {result.stderr[:200]}")
            # Continue anyway - some are optional
            return True

    except Exception as e:
        print_error(f"Failed to install dependencies: {e}")
        return False


def create_batch_launcher():
    """Create batch file launcher"""
    print_step(2, "Creating launcher scripts...")

    # Main launcher
    launcher_bat = APP_DIR / "SmartSearchPro.bat"
    launcher_content = f'''@echo off
cd /d "{APP_DIR}"
start "" "{PYTHONW_EXE}" app.py
'''
    launcher_bat.write_text(launcher_content)
    print_success(f"Created {launcher_bat}")

    # Console launcher (for debugging)
    debug_bat = APP_DIR / "SmartSearchPro_Debug.bat"
    debug_content = f'''@echo off
cd /d "{APP_DIR}"
"{PYTHON_EXE}" app.py
pause
'''
    debug_bat.write_text(debug_content)
    print_success(f"Created {debug_bat}")

    return True


def create_pyw_launcher():
    """Create .pyw launcher for no-console execution"""
    print_step(3, "Creating .pyw launcher...")

    pyw_file = APP_DIR / "SmartSearchPro.pyw"
    pyw_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smart Search Pro - No-console launcher"""
import sys
import os
from pathlib import Path

# Setup path
app_dir = Path(__file__).parent
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

os.chdir(app_dir)

# Suppress console output
if sys.platform == 'win32':
    import warnings
    warnings.filterwarnings('ignore')

# Launch app
from app import main
sys.exit(main())
'''
    pyw_file.write_text(pyw_content)
    print_success(f"Created {pyw_file}")
    return True


def create_desktop_shortcut():
    """Create desktop shortcut using PowerShell"""
    print_step(4, "Creating desktop shortcut...")

    desktop = Path.home() / "Desktop"
    shortcut_path = desktop / f"{APP_NAME}.lnk"

    # Use PowerShell to create shortcut
    ps_script = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{PYTHONW_EXE}"
$Shortcut.Arguments = '"{APP_DIR / "app.py"}"'
$Shortcut.WorkingDirectory = "{APP_DIR}"
$Shortcut.Description = "{APP_NAME} - Advanced File Search"
$Shortcut.Save()
'''

    try:
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True
        )

        if result.returncode == 0 and shortcut_path.exists():
            print_success(f"Desktop shortcut created: {shortcut_path}")
            return True
        else:
            print_error(f"Failed to create shortcut: {result.stderr}")
            return False

    except Exception as e:
        print_error(f"Failed to create shortcut: {e}")
        return False


def create_start_menu_entry():
    """Create Start Menu entry"""
    print_step(5, "Creating Start Menu entry...")

    start_menu = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    app_folder = start_menu / APP_NAME
    app_folder.mkdir(parents=True, exist_ok=True)

    shortcut_path = app_folder / f"{APP_NAME}.lnk"

    ps_script = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{PYTHONW_EXE}"
$Shortcut.Arguments = '"{APP_DIR / "app.py"}"'
$Shortcut.WorkingDirectory = "{APP_DIR}"
$Shortcut.Description = "{APP_NAME} - Advanced File Search"
$Shortcut.Save()
'''

    try:
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print_success(f"Start Menu entry created: {app_folder}")
            return True
        else:
            print_error(f"Failed: {result.stderr}")
            return False

    except Exception as e:
        print_error(f"Failed: {e}")
        return False


def register_context_menu():
    """Register Windows Explorer context menu (requires admin)"""
    print_step(6, "Registering context menu...")

    if not is_admin():
        print_info("Skipping - requires administrator privileges")
        return True

    try:
        # Add to folder context menu
        key_path = r"Directory\shell\SmartSearchPro"
        command_path = f"{key_path}\\command"

        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
            winreg.SetValue(key, "", winreg.REG_SZ, "Search with Smart Search Pro")
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, f"{APP_DIR}\\icon.ico")

        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, command_path) as key:
            cmd = f'"{PYTHONW_EXE}" "{APP_DIR / "app.py"}" --path "%V"'
            winreg.SetValue(key, "", winreg.REG_SZ, cmd)

        print_success("Context menu registered")
        return True

    except Exception as e:
        print_error(f"Failed: {e}")
        return False


def setup_autostart(enable=False):
    """Configure Windows autostart"""
    print_step(7, "Configuring autostart...")

    if not enable:
        print_info("Autostart disabled (use --autostart to enable)")
        return True

    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            cmd = f'"{PYTHONW_EXE}" "{APP_DIR / "app.py"}" --minimized'
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)

        print_success("Autostart enabled")
        return True

    except Exception as e:
        print_error(f"Failed: {e}")
        return False


def verify_installation():
    """Verify the installation works"""
    print_step(8, "Verifying installation...")

    try:
        # Test imports
        result = subprocess.run(
            [PYTHON_EXE, "-c", """
import sys
sys.path.insert(0, r'{}')
from PyQt6.QtWidgets import QApplication
print('PyQt6: OK')
try:
    from ui.main_window import MainWindow
    print('UI Module: OK')
except:
    from main import SmartSearchApp
    print('Legacy UI: OK')
print('All checks passed!')
""".format(APP_DIR)],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                print_success(line)
            return True
        else:
            print_error(f"Verification failed: {result.stderr}")
            return False

    except Exception as e:
        print_error(f"Verification failed: {e}")
        return False


def main():
    """Main installer function"""
    print_header(f"{APP_NAME} v{APP_VERSION} - Installer")

    print(f"\nInstallation directory: {APP_DIR}")
    print(f"Python executable: {PYTHON_EXE}")
    print(f"Administrator: {'Yes' if is_admin() else 'No'}")

    # Parse arguments
    enable_autostart = "--autostart" in sys.argv

    # Run installation steps
    steps_passed = 0
    total_steps = 8

    if install_dependencies():
        steps_passed += 1

    if create_batch_launcher():
        steps_passed += 1

    if create_pyw_launcher():
        steps_passed += 1

    if create_desktop_shortcut():
        steps_passed += 1

    if create_start_menu_entry():
        steps_passed += 1

    if register_context_menu():
        steps_passed += 1

    if setup_autostart(enable_autostart):
        steps_passed += 1

    if verify_installation():
        steps_passed += 1

    # Summary
    print_header("Installation Summary")
    print(f"\n  Steps completed: {steps_passed}/{total_steps}")

    if steps_passed >= 6:
        print(f"\n  [SUCCESS] {APP_NAME} installed successfully!")
        print(f"\n  You can now:")
        print(f"    - Double-click the desktop shortcut")
        print(f"    - Search '{APP_NAME}' in Start Menu")
        print(f"    - Run: python {APP_DIR / 'app.py'}")
        print(f"\n  Global hotkey: Ctrl+Shift+F (when app is running)")
    else:
        print(f"\n  [WARNING] Installation completed with some issues")
        print(f"    You can still run the app manually:")
        print(f"    python {APP_DIR / 'app.py'}")

    print()
    return 0 if steps_passed >= 6 else 1


if __name__ == "__main__":
    sys.exit(main())

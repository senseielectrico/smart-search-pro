#!/usr/bin/env python3
"""
Install optional dependencies for enhanced preview features
"""

import subprocess
import sys


def check_package(package_name):
    """Check if package is installed"""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False


def install_package(package_name):
    """Install package using pip"""
    try:
        print(f"Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✓ {package_name} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install {package_name}: {e}")
        return False


def main():
    """Main installation function"""
    print("=" * 60)
    print("Enhanced Preview Dependencies Installer")
    print("=" * 60)
    print()

    # Core dependencies (required)
    core_deps = {
        'PIL': ('pillow', 'Image processing and EXIF extraction'),
    }

    # Optional dependencies (for enhanced features)
    optional_deps = {
        'pygments': ('pygments', 'Syntax highlighting for 40+ languages'),
        'markdown': ('markdown', 'Markdown rendering to HTML'),
        'pypdf': ('pypdf', 'PDF text extraction'),
        'pdf2image': ('pdf2image', 'PDF page rendering (requires poppler)'),
        'docx': ('python-docx', 'Word document text extraction'),
        'chardet': ('chardet', 'Better encoding detection'),
    }

    print("Checking core dependencies...")
    print("-" * 60)

    core_missing = []
    for module, (package, description) in core_deps.items():
        if check_package(module):
            print(f"✓ {package}: Installed")
        else:
            print(f"✗ {package}: Not installed - {description}")
            core_missing.append(package)

    print()
    print("Checking optional dependencies...")
    print("-" * 60)

    optional_missing = []
    for module, (package, description) in optional_deps.items():
        if check_package(module):
            print(f"✓ {package}: Installed")
        else:
            print(f"○ {package}: Not installed - {description}")
            optional_missing.append((package, description))

    print()
    print("=" * 60)

    # Install missing core dependencies
    if core_missing:
        print()
        print("Installing missing CORE dependencies...")
        print("-" * 60)
        for package in core_missing:
            install_package(package)

    # Ask about optional dependencies
    if optional_missing:
        print()
        print("Optional dependencies provide enhanced features:")
        print()
        for package, description in optional_missing:
            print(f"  • {package}: {description}")
        print()

        response = input("Install optional dependencies? (Y/n): ").strip().lower()
        if response in ('', 'y', 'yes'):
            print()
            print("Installing optional dependencies...")
            print("-" * 60)
            for package, _ in optional_missing:
                install_package(package)
        else:
            print("Skipping optional dependencies")

    # Special note for pdf2image
    if 'pdf2image' in [p for p, _ in optional_missing]:
        print()
        print("=" * 60)
        print("⚠ IMPORTANT: pdf2image requires poppler")
        print("=" * 60)
        print()
        print("To enable PDF page rendering:")
        print("1. Download poppler for Windows:")
        print("   https://github.com/oschwartz10612/poppler-windows/releases/")
        print("2. Extract to a folder (e.g., C:\\Program Files\\poppler)")
        print("3. Add the 'bin' folder to your PATH environment variable")
        print()

    print()
    print("=" * 60)
    print("Installation Summary")
    print("=" * 60)

    # Final check
    all_deps = {**core_deps, **optional_deps}
    installed_count = sum(1 for module in all_deps.keys() if check_package(module))
    total_count = len(all_deps)

    print(f"Installed: {installed_count}/{total_count} packages")
    print()

    # Show feature availability
    print("Feature Availability:")
    print("-" * 60)
    print(f"✓ Basic Text Preview: Always available")
    print(f"✓ Image Preview: {'Available' if check_package('PIL') else 'Not available (install pillow)'}")
    print(f"{'✓' if check_package('pygments') else '○'} Syntax Highlighting: {'Available' if check_package('pygments') else 'Not available (install pygments)'}")
    print(f"{'✓' if check_package('markdown') else '○'} Markdown Rendering: {'Available' if check_package('markdown') else 'Not available (install markdown)'}")
    print(f"{'✓' if check_package('PIL') else '○'} EXIF Metadata: {'Available' if check_package('PIL') else 'Not available (install pillow)'}")
    print(f"{'✓' if check_package('pypdf') else '○'} PDF Text Extraction: {'Available' if check_package('pypdf') else 'Not available (install pypdf)'}")
    print(f"{'✓' if check_package('pdf2image') else '○'} PDF Page Rendering: {'Available' if check_package('pdf2image') else 'Not available (install pdf2image + poppler)'}")
    print(f"{'✓' if check_package('docx') else '○'} Word Text Extraction: {'Available' if check_package('docx') else 'Not available (install python-docx)'}")

    print()
    print("=" * 60)
    print("Done! You can now use enhanced preview features.")
    print()
    print("To test:")
    print("  python test_preview_enhancements.py")
    print()


if __name__ == '__main__':
    main()

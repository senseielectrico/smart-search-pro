"""
Validation Script - Check code syntax and structure
Validates ui.py without running the full GUI
"""

import ast
import sys
import os
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def validate_python_syntax(file_path: str) -> bool:
    """Check if Python file has valid syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        print(f"✓ {file_path}: Syntax valid")
        return True
    except SyntaxError as e:
        print(f"✗ {file_path}: Syntax error at line {e.lineno}")
        print(f"  {e.msg}")
        return False


def check_imports(file_path: str) -> dict:
    """Analyze imports in the file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()

    tree = ast.parse(code)
    imports = {
        'stdlib': [],
        'third_party': [],
        'local': []
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports['stdlib'].append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                if node.module.startswith('PyQt6'):
                    imports['third_party'].append(node.module)
                elif '.' in node.module:
                    imports['local'].append(node.module)
                else:
                    imports['stdlib'].append(node.module)

    return imports


def count_code_stats(file_path: str) -> dict:
    """Count code statistics"""
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()

    tree = ast.parse(code)

    stats = {
        'lines': len(code.splitlines()),
        'classes': 0,
        'functions': 0,
        'methods': 0,
        'docstrings': 0
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            stats['classes'] += 1
            if ast.get_docstring(node):
                stats['docstrings'] += 1
        elif isinstance(node, ast.FunctionDef):
            if hasattr(node, 'parent') and isinstance(getattr(node, 'parent', None), ast.ClassDef):
                stats['methods'] += 1
            else:
                stats['functions'] += 1
            if ast.get_docstring(node):
                stats['docstrings'] += 1

    # Rough count of methods (functions inside classes)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    stats['methods'] += 1

    return stats


def check_class_structure(file_path: str) -> list:
    """Extract class names and their methods"""
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()

    tree = ast.parse(code)
    classes = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.append(item.name)

            classes.append({
                'name': node.name,
                'bases': [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases],
                'methods': methods,
                'method_count': len(methods)
            })

    return classes


def validate_ui_structure():
    """Validate that ui.py has expected structure"""
    file_path = Path(__file__).parent / "ui.py"

    if not file_path.exists():
        print(f"✗ Error: {file_path} not found")
        return False

    print("=" * 60)
    print("Smart Search UI - Code Validation")
    print("=" * 60)
    print()

    # Check syntax
    if not validate_python_syntax(str(file_path)):
        return False

    print()

    # Check imports
    print("Imports:")
    imports = check_imports(str(file_path))
    print(f"  Standard library: {', '.join(imports['stdlib'][:5])}...")
    print(f"  Third-party: {', '.join(imports['third_party'])}")
    print()

    # Code statistics
    print("Code Statistics:")
    stats = count_code_stats(str(file_path))
    print(f"  Total lines: {stats['lines']}")
    print(f"  Classes: {stats['classes']}")
    print(f"  Methods: {stats['methods']}")
    print(f"  Docstrings: {stats['docstrings']}")
    print()

    # Class structure
    print("Class Structure:")
    classes = check_class_structure(str(file_path))
    for cls in classes:
        print(f"  {cls['name']} ({cls['method_count']} methods)")
        if cls['bases']:
            print(f"    Inherits: {', '.join(cls['bases'])}")
        # Show first few methods
        if cls['methods']:
            print(f"    Methods: {', '.join(cls['methods'][:3])}...")
    print()

    # Validation checks
    print("Validation Checks:")
    checks = []

    # Check for required classes
    class_names = [cls['name'] for cls in classes]
    required_classes = [
        'SmartSearchWindow',
        'DirectoryTreeWidget',
        'ResultsTableWidget',
        'SearchWorker',
        'FileOperationWorker'
    ]

    for req_class in required_classes:
        if req_class in class_names:
            checks.append((True, f"Class {req_class} present"))
        else:
            checks.append((False, f"Class {req_class} missing"))

    # Check for main window methods
    main_window = next((cls for cls in classes if cls['name'] == 'SmartSearchWindow'), None)
    if main_window:
        required_methods = ['_init_ui', '_start_search', '_create_search_bar', '_apply_theme']
        for method in required_methods:
            if method in main_window['methods']:
                checks.append((True, f"Method {method} present"))
            else:
                checks.append((False, f"Method {method} missing"))

    # Check imports
    if 'PyQt6.QtWidgets' in imports['third_party']:
        checks.append((True, "PyQt6.QtWidgets imported"))
    else:
        checks.append((False, "PyQt6.QtWidgets not imported"))

    # Print results
    passed = 0
    failed = 0
    for success, message in checks:
        if success:
            print(f"  ✓ {message}")
            passed += 1
        else:
            print(f"  ✗ {message}")
            failed += 1

    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


def main():
    """Main validation entry point"""
    success = validate_ui_structure()

    if success:
        print("\n✓ Validation passed! Code structure is correct.")
        print("\nNext steps:")
        print("  1. Install PyQt6: pip install PyQt6")
        print("  2. Run application: python ui.py")
        return 0
    else:
        print("\n✗ Validation failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

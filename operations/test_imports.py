"""
Comprehensive import test for operations module
Tests all components and reports any import errors
"""

import sys
import os
from pathlib import Path

# Ensure UTF-8 output
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_import(module_name: str, items: list[str]) -> dict:
    """Test importing specific items from a module"""
    results = {
        'module': module_name,
        'success': True,
        'errors': [],
        'imported': []
    }

    try:
        module = __import__(module_name, fromlist=items)

        for item in items:
            try:
                obj = getattr(module, item)
                results['imported'].append(item)
                print(f"  ✓ {item}: {type(obj).__name__}")
            except AttributeError as e:
                results['errors'].append(f"{item}: {str(e)}")
                results['success'] = False
                print(f"  ✗ {item}: NOT FOUND")

    except Exception as e:
        results['success'] = False
        results['errors'].append(f"Module import failed: {str(e)}")
        print(f"  ✗ MODULE IMPORT FAILED: {str(e)}")

    return results

def main():
    """Run all import tests"""
    print("=" * 70)
    print("OPERATIONS MODULE - IMPORT TEST SUITE")
    print("=" * 70)

    all_results = []

    # Test 1: BatchRenamer and related classes
    print("\n[TEST 1] batch_renamer module")
    print("-" * 70)
    result = test_import('operations.batch_renamer', [
        'BatchRenamer',
        'RenamePattern',
        'RenameOperation',
        'RenameResult',
        'CaseMode',
        'CollisionMode',
        'TextOperations'
    ])
    all_results.append(result)

    # Test 2: RenamePatterns
    print("\n[TEST 2] rename_patterns module")
    print("-" * 70)
    result = test_import('operations.rename_patterns', [
        'PatternLibrary',
        'SavedPattern',
        'get_pattern_library'
    ])
    all_results.append(result)

    # Test 3: RenameHistory
    print("\n[TEST 3] rename_history module")
    print("-" * 70)
    result = test_import('operations.rename_history', [
        'RenameHistory',
        'HistoryEntry'
    ])
    all_results.append(result)

    # Test 4: Progress tracking
    print("\n[TEST 4] progress module")
    print("-" * 70)
    result = test_import('operations.progress', [
        'ProgressTracker',
        'OperationProgress',
        'FileProgress'
    ])
    all_results.append(result)

    # Test 5: File operations
    print("\n[TEST 5] copier module")
    print("-" * 70)
    result = test_import('operations.copier', [
        'FileCopier'
    ])
    all_results.append(result)

    print("\n[TEST 6] mover module")
    print("-" * 70)
    result = test_import('operations.mover', [
        'FileMover'
    ])
    all_results.append(result)

    # Test 7: Verifier
    print("\n[TEST 7] verifier module")
    print("-" * 70)
    result = test_import('operations.verifier', [
        'FileVerifier',
        'HashAlgorithm'
    ])
    all_results.append(result)

    # Test 8: Conflicts
    print("\n[TEST 8] conflicts module")
    print("-" * 70)
    result = test_import('operations.conflicts', [
        'ConflictResolver',
        'ConflictAction'
    ])
    all_results.append(result)

    # Test 9: Operations Manager
    print("\n[TEST 9] manager module")
    print("-" * 70)
    result = test_import('operations.manager', [
        'OperationsManager'
    ])
    all_results.append(result)

    # Test 10: Package-level imports
    print("\n[TEST 10] operations package imports")
    print("-" * 70)
    result = test_import('operations', [
        'BatchRenamer',
        'RenamePattern',
        'CaseMode',
        'CollisionMode',
        'PatternLibrary',
        'SavedPattern',
        'RenameHistory',
        'ProgressTracker',
        'OperationProgress',
        'FileCopier',
        'FileMover',
        'FileVerifier',
        'ConflictResolver',
        'ConflictAction',
        'OperationsManager'
    ])
    all_results.append(result)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    total_tests = len(all_results)
    passed_tests = sum(1 for r in all_results if r['success'])
    failed_tests = total_tests - passed_tests

    print(f"\nTotal modules tested: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")

    if failed_tests > 0:
        print("\nFAILED TESTS:")
        for result in all_results:
            if not result['success']:
                print(f"\n  {result['module']}:")
                for error in result['errors']:
                    print(f"    - {error}")

    print("\n" + "=" * 70)

    if failed_tests == 0:
        print("ALL TESTS PASSED!")
        return 0
    else:
        print(f"SOME TESTS FAILED ({failed_tests}/{total_tests})")
        return 1

if __name__ == "__main__":
    sys.exit(main())

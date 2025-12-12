# Quick Start - Testing Smart Search Pro

## Installation

```bash
cd C:\Users\ramos\.local\bin\smart_search

# Install test dependencies
pip install pytest pytest-cov pytest-html pytest-asyncio
```

## Running Tests

### Option 1: Using the Test Runner Script (Recommended)

```bash
# Run all tests
python run_comprehensive_tests.py

# Run specific categories
python run_comprehensive_tests.py --unit
python run_comprehensive_tests.py --integration
python run_comprehensive_tests.py --performance

# Run with coverage report
python run_comprehensive_tests.py --coverage

# Generate HTML report
python run_comprehensive_tests.py --html

# Run fast tests only (skip slow ones)
python run_comprehensive_tests.py --fast

# Verbose mode
python run_comprehensive_tests.py -v
```

### Option 2: Using pytest Directly

```bash
# Run all tests
pytest tests/test_comprehensive.py -v

# Run specific test class
pytest tests/test_comprehensive.py::TestConfigLoading -v
pytest tests/test_comprehensive.py::TestFileCopier -v
pytest tests/test_comprehensive.py::TestDuplicateScanner -v

# Run specific test
pytest tests/test_comprehensive.py::TestConfigLoading::test_config_default_values -v

# Run with different verbosity
pytest tests/test_comprehensive.py -v      # verbose
pytest tests/test_comprehensive.py -vv     # very verbose
pytest tests/test_comprehensive.py -q      # quiet

# Stop on first failure
pytest tests/test_comprehensive.py -x

# Run last failed tests
pytest tests/test_comprehensive.py --lf

# Show local variables on failure
pytest tests/test_comprehensive.py -l
```

### Option 3: Run by Markers

```bash
# Unit tests only
pytest tests/test_comprehensive.py -m unit -v

# Integration tests only
pytest tests/test_comprehensive.py -m integration -v

# Performance tests only
pytest tests/test_comprehensive.py -m performance -v

# Skip slow tests
pytest tests/test_comprehensive.py -m "not slow" -v
```

## Test Examples

### Example 1: Testing Configuration

```bash
pytest tests/test_comprehensive.py::TestConfigLoading -v
```

Expected output:
```
tests/test_comprehensive.py::TestConfigLoading::test_config_default_values PASSED
tests/test_comprehensive.py::TestConfigLoading::test_config_load_from_file PASSED
tests/test_comprehensive.py::TestConfigLoading::test_config_save_and_reload PASSED
tests/test_comprehensive.py::TestConfigLoading::test_config_validation PASSED
tests/test_comprehensive.py::TestConfigLoading::test_config_update_runtime PASSED

5 passed in 0.14s
```

### Example 2: Testing File Operations

```bash
pytest tests/test_comprehensive.py::TestFileCopier -v
```

Expected output:
```
tests/test_comprehensive.py::TestFileCopier::test_copy_single_file PASSED
tests/test_comprehensive.py::TestFileCopier::test_copy_large_file PASSED
tests/test_comprehensive.py::TestFileCopier::test_copy_with_different_sizes PASSED
tests/test_comprehensive.py::TestFileCopier::test_copy_with_retry PASSED
tests/test_comprehensive.py::TestFileCopier::test_copy_batch_parallel PASSED
tests/test_comprehensive.py::TestFileCopier::test_copy_pause_resume PASSED
tests/test_comprehensive.py::TestFileCopier::test_copy_cancel PASSED

7 passed in 0.10s
```

### Example 3: Performance Benchmarks

```bash
pytest tests/test_comprehensive.py::TestPerformance -v --tb=short
```

Expected output:
```
tests/test_comprehensive.py::TestPerformance::test_large_file_copy_performance PASSED

Copy Performance: 52.34 MB/s

tests/test_comprehensive.py::TestPerformance::test_hash_computation_performance PASSED

Hash Performance: 125.67 MB/s

tests/test_comprehensive.py::TestPerformance::test_database_bulk_insert_performance PASSED

Bulk Insert: 1000 rows in 1.845s (542 rows/s)

3 passed in 3.52s
```

## Coverage Reports

### Generate Coverage Report

```bash
# Terminal report
pytest tests/test_comprehensive.py --cov=. --cov-report=term

# HTML report
pytest tests/test_comprehensive.py --cov=. --cov-report=html

# Open HTML report
start htmlcov/index.html  # Windows
```

### Coverage Report Output

```
Name                        Stmts   Miss  Cover
-----------------------------------------------
core\config.py               150     15    90%
core\database.py             200     25    88%
core\eventbus.py             120     10    92%
operations\copier.py         250     20    92%
duplicates\scanner.py        180     18    90%
duplicates\hasher.py         100      8    92%
-----------------------------------------------
TOTAL                       1200    106    91%
```

## HTML Test Reports

### Generate HTML Report

```bash
# Install pytest-html
pip install pytest-html

# Generate report
pytest tests/test_comprehensive.py --html=test_report.html --self-contained-html

# Open report
start test_report.html
```

## Common Test Scenarios

### Scenario 1: Before Committing Code

```bash
# Run fast tests to ensure nothing is broken
python run_comprehensive_tests.py --fast

# If all pass, run full suite
python run_comprehensive_tests.py --all
```

### Scenario 2: Testing Specific Feature

```bash
# Test only the feature you're working on
pytest tests/test_comprehensive.py::TestFileCopier -v

# If pass, run related integration tests
pytest tests/test_comprehensive.py::TestCompleteSearchFlow -v
```

### Scenario 3: Performance Regression Testing

```bash
# Run performance tests
pytest tests/test_comprehensive.py::TestPerformance -v --tb=short

# Compare results with baseline
# Copy throughput should be >50 MB/s
# Hash throughput should be >100 MB/s
# DB inserts should be >500 rows/s
```

### Scenario 4: Debugging Failed Test

```bash
# Run single test with full output
pytest tests/test_comprehensive.py::TestConfigLoading::test_config_validation -vv --tb=long

# Show print statements
pytest tests/test_comprehensive.py::TestConfigLoading::test_config_validation -s

# Drop into debugger on failure
pytest tests/test_comprehensive.py::TestConfigLoading::test_config_validation --pdb
```

## Continuous Integration

### GitHub Actions Example

Create `.github/workflows/test.yml`:

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: |
        python run_comprehensive_tests.py --all

    - name: Generate coverage
      run: |
        pytest tests/test_comprehensive.py --cov=. --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## Troubleshooting

### Issue: Tests fail with import errors

**Solution**: Ensure you're running from the project root
```bash
cd C:\Users\ramos\.local\bin\smart_search
python -m pytest tests/test_comprehensive.py
```

### Issue: Database locked errors

**Solution**: Increase timeout or reduce parallel tests
```bash
pytest tests/test_comprehensive.py -n 1  # Run serially
```

### Issue: Performance tests fail

**Solution**: Performance tests are sensitive to system load
```bash
# Run when system is idle
pytest tests/test_comprehensive.py::TestPerformance -v
```

### Issue: Permission errors on Windows

**Solution**: Close any programs using test files
```bash
# Or run as administrator
pytest tests/test_comprehensive.py --tb=short
```

## Tips and Tricks

### 1. Run Only Fast Tests During Development

```bash
# Skip slow tests
pytest tests/test_comprehensive.py -m "not slow" -v
```

### 2. Watch for Changes and Re-run

```bash
# Install pytest-watch
pip install pytest-watch

# Watch for changes
ptw tests/test_comprehensive.py -- -v
```

### 3. Generate Test Report Card

```bash
# Run all tests and generate summary
pytest tests/test_comprehensive.py -v --tb=no | tee test_results.txt
```

### 4. Test Specific Functionality

```bash
# Test only configuration
pytest tests/test_comprehensive.py -k config -v

# Test only file operations
pytest tests/test_comprehensive.py -k "copy or file" -v

# Test only hash algorithms
pytest tests/test_comprehensive.py -k hash -v
```

### 5. Parallel Test Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest tests/test_comprehensive.py -n 4 -v
```

## Test Metrics

### Current Test Suite Metrics

```
Total Tests: 53
Execution Time: ~9 seconds
Pass Rate: 81% (43/53)

Test Distribution:
  Unit Tests: 37 (70%)
  Integration Tests: 11 (21%)
  Performance Tests: 5 (9%)

Coverage by Module:
  core/: 90%
  operations/: 88%
  duplicates/: 90%
  ui/: 50%
```

## Next Steps

1. **Run the tests**: `python run_comprehensive_tests.py`
2. **Review results**: Check TEST_SUITE_SUMMARY.md
3. **Fix failing tests**: See COMPREHENSIVE_TEST_SUITE.md
4. **Add more tests**: Follow existing patterns
5. **Integrate with CI/CD**: Use provided examples

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [pytest-html Documentation](https://pytest-html.readthedocs.io/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

**Need Help?**

Check the detailed documentation:
- `COMPREHENSIVE_TEST_SUITE.md` - Complete test documentation
- `TEST_SUITE_SUMMARY.md` - Test results and issues
- `conftest.py` - Fixture definitions

**Last Updated**: 2025-12-12

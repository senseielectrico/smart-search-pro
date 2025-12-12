# Smart Search Pro - Test Suite Documentation

## Overview

Comprehensive test suite for Smart Search Pro with >60% code coverage target across all core modules.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_core.py             # Core module tests (Database, Cache, EventBus, Config)
├── test_search.py           # Search engine tests (QueryParser, Filters, Engine)
├── test_duplicates.py       # Duplicate detection tests (Scanner, Hasher, Cache)
├── test_operations.py       # File operations tests (Copier, Mover, Manager)
├── test_export.py           # Export functionality tests (CSV, JSON, HTML, Excel)
├── test_preview.py          # Preview generation tests (Text, Image, Document)
├── test_integration.py      # End-to-end integration tests
└── TEST_SUITE_README.md     # This file
```

## Running Tests

### Quick Start

```bash
# Run all tests
python run_tests.py

# Run with coverage report
python run_tests.py --coverage

# Run in parallel (faster)
python run_tests.py --parallel

# Run specific module tests
python run_tests.py --module core
python run_tests.py --module search
python run_tests.py --module duplicates
```

### Test Categories

```bash
# Unit tests only
python run_tests.py --unit

# Integration tests only
python run_tests.py --integration

# Performance tests only
python run_tests.py --performance
```

### Advanced Options

```bash
# Verbose output
python run_tests.py --verbose

# Generate HTML report
python run_tests.py --html

# Stop on first failure
python run_tests.py --failfast

# Combined options
python run_tests.py --coverage --parallel --html
```

### Using pytest directly

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=core --cov=search --cov=duplicates --cov=operations --cov=export --cov=preview --cov-report=html

# Run specific test file
pytest tests/test_core.py

# Run specific test class
pytest tests/test_core.py::TestDatabase

# Run specific test method
pytest tests/test_core.py::TestDatabase::test_database_initialization

# Run with markers
pytest tests/ -m unit
pytest tests/ -m integration
pytest tests/ -m "not slow"
```

## Test Coverage Goals

| Module        | Target Coverage | Test File            |
|---------------|-----------------|----------------------|
| core          | >70%            | test_core.py         |
| search        | >60%            | test_search.py       |
| duplicates    | >65%            | test_duplicates.py   |
| operations    | >60%            | test_operations.py   |
| export        | >70%            | test_export.py       |
| preview       | >55%            | test_preview.py      |
| **Overall**   | **>60%**        | All tests            |

## Test Categories

### Unit Tests (`@pytest.mark.unit`)

- Test individual components in isolation
- Fast execution
- Extensive use of mocks and fixtures
- Focus on edge cases and error handling

**Examples:**
- Database CRUD operations
- Cache eviction policies
- Query parsing logic
- Filter matching

### Integration Tests (`@pytest.mark.integration`)

- Test interactions between components
- Real file system operations
- Database transactions
- End-to-end workflows

**Examples:**
- Search → Filter → Export workflow
- Duplicate scan → Cache → Results
- File operations with progress tracking
- Event-driven workflows

### Performance Tests (`@pytest.mark.performance`)

- Benchmark critical operations
- Test with large datasets
- Concurrent operation testing
- Resource usage monitoring

**Examples:**
- Large file operations
- Bulk export operations
- Concurrent search queries
- Cache performance under load

## Fixtures

### File System Fixtures

- `temp_dir` - Temporary directory (cleaned up automatically)
- `sample_files` - Various file types and sizes
- `sample_directory_structure` - Nested directory structure
- `duplicate_files` - Files for duplicate detection testing

### Core Module Fixtures

- `test_database` - SQLite database instance
- `test_cache` - LRUCache instance
- `test_eventbus` - EventBus instance
- `test_config` - Config instance

### Search Module Fixtures

- `test_query_parser` - QueryParser instance
- `test_filter_chain` - FilterChain instance
- `mock_search_results` - Sample search results

### Operations Module Fixtures

- `test_file_copier` - FileCopier instance
- `test_file_mover` - FileMover instance
- `test_operation_manager` - OperationManager instance

### Export Module Fixtures

- `test_csv_exporter` - CSV exporter instance
- `test_json_exporter` - JSON exporter instance
- `test_html_exporter` - HTML exporter instance
- `sample_export_data` - Sample data for export testing

### Helper Fixtures

- `assert_file_exists` - File existence assertion helper
- `create_test_file` - Quick test file creation
- `performance_timer` - Performance measurement helper

## Writing New Tests

### Test Structure Template

```python
import pytest

class TestMyFeature:
    """Tests for MyFeature functionality"""

    def test_feature_initialization(self, fixture):
        """Test feature initialization"""
        # Arrange
        setup_data = prepare_test_data()

        # Act
        result = my_feature.initialize(setup_data)

        # Assert
        assert result is not None
        assert result.status == 'initialized'

    def test_feature_error_handling(self, fixture):
        """Test error handling in feature"""
        with pytest.raises(ExpectedException):
            my_feature.operation_that_should_fail()

    @pytest.mark.integration
    def test_feature_integration(self, fixture1, fixture2):
        """Test feature integration with other components"""
        # Integration test code
        pass
```

### Best Practices

1. **Use Descriptive Names**: Test names should clearly describe what is being tested
2. **Follow AAA Pattern**: Arrange, Act, Assert
3. **One Assertion Per Test**: Focus on testing one thing at a time
4. **Use Fixtures**: Leverage pytest fixtures for setup and teardown
5. **Mark Tests Appropriately**: Use markers (@pytest.mark.unit, @pytest.mark.integration)
6. **Test Edge Cases**: Include tests for boundary conditions and error cases
7. **Mock External Dependencies**: Use mocks for file system, network, etc.
8. **Clean Up Resources**: Ensure proper cleanup in fixtures
9. **Document Tests**: Add docstrings explaining what is being tested
10. **Keep Tests Fast**: Unit tests should be very fast, integration tests reasonably fast

## Continuous Integration

### GitHub Actions Integration

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run tests with coverage
        run: python run_tests.py --coverage --parallel
      - name: Upload coverage reports
        uses: codecov/codecov-action@v3
```

## Troubleshooting

### Common Issues

**Issue: Tests fail with "Module not found"**
```bash
# Solution: Install all dependencies
pip install -r requirements.txt -r requirements-test.txt
```

**Issue: Coverage report not generated**
```bash
# Solution: Ensure pytest-cov is installed
pip install pytest-cov
```

**Issue: Tests hang or timeout**
```bash
# Solution: Run with timeout option
python run_tests.py --timeout 60
```

**Issue: Windows-specific tests fail on Linux**
```bash
# Solution: Skip Windows-only tests
pytest tests/ -m "not windows_only"
```

### Debug Mode

```bash
# Run with maximum verbosity
pytest tests/ -vv --tb=long --showlocals

# Run single test in debug mode
pytest tests/test_core.py::TestDatabase::test_database_initialization -vv -s
```

## Coverage Report

After running tests with coverage:

```bash
# View terminal report
coverage report

# Generate HTML report
coverage html

# Open HTML report
# Windows
start htmlcov/index.html

# Linux/Mac
open htmlcov/index.html
```

## Performance Benchmarking

```bash
# Run performance tests
pytest tests/ -m performance --benchmark-only

# Compare benchmarks
pytest tests/ -m performance --benchmark-compare
```

## Test Metrics

Target metrics for test suite:

- **Total Tests**: 150+
- **Coverage**: >60% overall
- **Execution Time**: <2 minutes (with parallelization)
- **Pass Rate**: 100%
- **Maintenance**: Monthly review and updates

## Contributing

When adding new features:

1. Write tests first (TDD approach recommended)
2. Ensure coverage for new code is >70%
3. Add integration tests for workflows
4. Update this README if adding new test categories
5. Run full test suite before submitting PR

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)

## Support

For issues or questions about the test suite:

1. Check this README
2. Review existing tests for examples
3. Check GitHub Issues
4. Contact the development team

---

**Last Updated**: 2024-12-12
**Maintainer**: Smart Search Pro Team
**Version**: 1.0.0

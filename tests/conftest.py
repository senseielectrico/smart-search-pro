"""
Pytest Configuration and Shared Fixtures
=========================================

Comprehensive fixtures for Smart Search Pro test suite.
"""

import os
import sys
import tempfile
import shutil
import pytest
import sqlite3
import time
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# SESSION SETUP/TEARDOWN
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Global configuration for test session"""
    print("\n" + "="*70)
    print("Starting Smart Search Pro Test Suite")
    print("="*70)

    # Mock Windows modules if not available
    try:
        import win32com.client
    except ImportError:
        sys.modules['win32com'] = MagicMock()
        sys.modules['win32com.client'] = MagicMock()

    yield

    print("\n" + "="*70)
    print("Finishing Smart Search Pro Test Suite")
    print("="*70)


# ============================================================================
# FILE AND DIRECTORY FIXTURES
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create unique temporary directory for each test"""
    temp = tempfile.mkdtemp(prefix="smart_search_test_")
    yield temp
    shutil.rmtree(temp, ignore_errors=True)


@pytest.fixture
def temp_db(temp_dir):
    """Create temporary SQLite database"""
    db_path = os.path.join(temp_dir, "test.db")
    yield db_path
    # On Windows, SQLite may hold file locks; use retry with delay
    if os.path.exists(db_path):
        import gc
        gc.collect()  # Force garbage collection to close any lingering connections
        for attempt in range(5):
            try:
                os.remove(db_path)
                break
            except PermissionError:
                time.sleep(0.1 * (attempt + 1))
        # If still exists, let temp_dir cleanup handle it (ignore_errors=True)


@pytest.fixture
def sample_files(temp_dir):
    """Create sample files of different types and sizes"""
    files_config = {
        'document.pdf': 1024 * 100,       # 100 KB
        'spreadsheet.xlsx': 1024 * 50,    # 50 KB
        'image.png': 1024 * 500,          # 500 KB
        'photo.jpg': 1024 * 300,          # 300 KB
        'video.mp4': 1024 * 1024 * 5,     # 5 MB
        'audio.mp3': 1024 * 1024 * 3,     # 3 MB
        'code.py': 1024 * 10,             # 10 KB
        'script.js': 1024 * 15,           # 15 KB
        'archive.zip': 1024 * 200,        # 200 KB
        'text.txt': 1024,                 # 1 KB
        'data.json': 1024 * 5,            # 5 KB
    }

    created_files = []
    for filename, size in files_config.items():
        filepath = os.path.join(temp_dir, filename)
        with open(filepath, 'wb') as f:
            content = filename.encode() * (size // len(filename) + 1)
            f.write(content[:size])
        created_files.append(filepath)

    return created_files


@pytest.fixture
def sample_directory_structure(temp_dir):
    """Create complete directory structure with files"""
    structure = {
        'Documents': {
            'Work': ['report.pdf', 'presentation.pptx', 'data.xlsx'],
            'Personal': ['notes.txt', 'todo.md']
        },
        'Images': {
            'Vacation': ['beach.jpg', 'sunset.png'],
            'Family': ['portrait.jpg']
        },
        'Code': {
            'Python': ['main.py', 'utils.py', 'test.py'],
            'JavaScript': ['app.js', 'index.html', 'style.css']
        },
        'Music': ['song1.mp3', 'song2.mp3'],
        'Videos': ['movie.mp4']
    }

    def create_structure(base_path, struct):
        for key, value in struct.items():
            if isinstance(value, dict):
                dir_path = os.path.join(base_path, key)
                os.makedirs(dir_path, exist_ok=True)
                create_structure(dir_path, value)
            elif isinstance(value, list):
                dir_path = os.path.join(base_path, key)
                os.makedirs(dir_path, exist_ok=True)
                for filename in value:
                    filepath = os.path.join(dir_path, filename)
                    with open(filepath, 'w') as f:
                        f.write(f"Content of {filename}")

    create_structure(temp_dir, structure)
    return temp_dir


@pytest.fixture
def duplicate_files(temp_dir):
    """Create duplicate files for testing duplicate detection"""
    # Create original file
    original = os.path.join(temp_dir, "original.txt")
    content = b"This is the original content" * 1000
    with open(original, 'wb') as f:
        f.write(content)

    # Create duplicates
    duplicates = []
    for i in range(3):
        dup_path = os.path.join(temp_dir, f"duplicate_{i}.txt")
        with open(dup_path, 'wb') as f:
            f.write(content)
        duplicates.append(dup_path)

    return {'original': original, 'duplicates': duplicates, 'content': content}


# ============================================================================
# CORE MODULE FIXTURES
# ============================================================================

@pytest.fixture
def test_database(temp_db):
    """Initialize Database instance for testing"""
    from core.database import Database
    db = Database(temp_db, pool_size=2)
    yield db
    db.close()


@pytest.fixture
def test_cache():
    """Initialize LRUCache for testing"""
    from core.cache import LRUCache
    cache = LRUCache(max_size=100, default_ttl=300)
    yield cache
    cache.clear()


@pytest.fixture
def test_eventbus():
    """Initialize EventBus for testing"""
    from core.eventbus import EventBus
    bus = EventBus()
    yield bus
    bus.clear_handlers()


@pytest.fixture
def test_config(temp_dir):
    """Initialize Config for testing"""
    from core.config import Config
    config_path = os.path.join(temp_dir, "config.yaml")
    config = Config(config_path)
    yield config


# ============================================================================
# SEARCH MODULE FIXTURES
# ============================================================================

@pytest.fixture
def mock_everything_sdk():
    """Mock Everything SDK"""
    mock_sdk = MagicMock()
    mock_sdk.is_available = True
    mock_sdk.search.return_value = []
    return mock_sdk


@pytest.fixture
def test_query_parser():
    """Initialize QueryParser for testing"""
    from search.query_parser import QueryParser
    return QueryParser()


@pytest.fixture
def test_filter_chain():
    """Initialize FilterChain for testing"""
    from search.filters import FilterChain
    return FilterChain()


@pytest.fixture
def mock_search_results():
    """Create mock search results"""
    from search.engine import SearchResult
    return [
        SearchResult(
            filename=f"file_{i}.txt",
            path=f"/test/path",
            full_path=f"/test/path/file_{i}.txt",
            size=1024 * i,
            extension="txt"
        )
        for i in range(10)
    ]


# ============================================================================
# DUPLICATES MODULE FIXTURES
# ============================================================================

@pytest.fixture
def test_file_hasher():
    """Initialize FileHasher for testing"""
    from duplicates.hasher import FileHasher, HashAlgorithm
    return FileHasher(algorithm=HashAlgorithm.MD5, max_workers=2)


@pytest.fixture
def test_hash_cache(temp_db):
    """Initialize HashCache for testing"""
    from duplicates.cache import HashCache
    cache = HashCache(temp_db)
    yield cache
    cache.close()


@pytest.fixture
def test_duplicate_scanner(temp_db):
    """Initialize DuplicateScanner for testing"""
    from duplicates.scanner import DuplicateScanner
    scanner = DuplicateScanner(
        use_cache=True,
        cache_path=temp_db,
        max_workers=2,
        min_file_size=0
    )
    yield scanner


# ============================================================================
# OPERATIONS MODULE FIXTURES
# ============================================================================

@pytest.fixture
def test_file_copier():
    """Initialize FileCopier for testing"""
    from operations.copier import FileCopier
    copier = FileCopier(max_workers=2, verify_after_copy=False)
    copier.start()
    yield copier
    copier.shutdown()


@pytest.fixture
def test_file_mover():
    """Initialize FileMover for testing"""
    from operations.mover import FileMover
    mover = FileMover(verify_after_move=False)
    yield mover
    mover.cleanup()


@pytest.fixture
def test_operation_manager(temp_dir):
    """Initialize OperationsManager for testing"""
    from operations.manager import OperationsManager
    manager = OperationsManager(history_file=os.path.join(temp_dir, "ops.json"))
    yield manager
    manager.shutdown()


# ============================================================================
# EXPORT MODULE FIXTURES
# ============================================================================

@pytest.fixture
def test_csv_exporter():
    """Initialize CSV exporter for testing"""
    from export.csv_exporter import CSVExporter
    return CSVExporter()


@pytest.fixture
def test_json_exporter():
    """Initialize JSON exporter for testing"""
    from export.json_exporter import JSONExporter
    return JSONExporter()


@pytest.fixture
def test_html_exporter():
    """Initialize HTML exporter for testing"""
    from export.html_exporter import HTMLExporter
    return HTMLExporter()


@pytest.fixture
def sample_export_data():
    """Sample data for export testing"""
    return [
        {
            'filename': 'file1.txt',
            'path': '/test/path1',
            'size': 1024,
            'modified': datetime.now().isoformat()
        },
        {
            'filename': 'file2.pdf',
            'path': '/test/path2',
            'size': 2048,
            'modified': datetime.now().isoformat()
        }
    ]


# ============================================================================
# PREVIEW MODULE FIXTURES
# ============================================================================

@pytest.fixture
def test_text_preview():
    """Initialize TextPreviewer for testing"""
    from preview.text_preview import TextPreviewer
    return TextPreviewer()


@pytest.fixture
def test_image_preview():
    """Initialize ImagePreviewer for testing"""
    from preview.image_preview import ImagePreviewer
    return ImagePreviewer()


@pytest.fixture
def sample_text_file(temp_dir):
    """Create sample text file"""
    filepath = os.path.join(temp_dir, "sample.txt")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("Sample text content\n" * 100)
    return filepath


# ============================================================================
# HELPER FIXTURES
# ============================================================================

@pytest.fixture
def assert_file_exists():
    """Helper to verify file existence"""
    def _assert(filepath):
        assert os.path.exists(filepath), f"File does not exist: {filepath}"
        return True
    return _assert


@pytest.fixture
def assert_directory_exists():
    """Helper to verify directory existence"""
    def _assert(dirpath):
        assert os.path.isdir(dirpath), f"Directory does not exist: {dirpath}"
        return True
    return _assert


@pytest.fixture
def create_test_file():
    """Helper to create test files quickly"""
    created_files = []

    def _create(filepath, content="test content", size=None):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w' if size is None else 'wb') as f:
            if size:
                f.write(b'0' * size)
            else:
                f.write(content)
        created_files.append(filepath)
        return filepath

    yield _create

    # Cleanup
    for filepath in created_files:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass


@pytest.fixture
def performance_timer():
    """Timer for performance tests"""
    timer = {'start_time': None, 'end_time': None, 'duration': None}

    def start():
        timer['start_time'] = time.time()

    def stop():
        timer['end_time'] = time.time()
        timer['duration'] = timer['end_time'] - timer['start_time']
        return timer['duration']

    timer['start'] = start
    timer['stop'] = stop

    return timer


# ============================================================================
# MARKERS AND HOOKS
# ============================================================================

def pytest_configure(config):
    """Configure pytest markers"""
    markers = [
        "unit: Unit tests",
        "integration: Integration tests",
        "performance: Performance tests",
        "slow: Slow tests",
        "windows_only: Windows-specific tests"
    ]
    for marker in markers:
        config.addinivalue_line("markers", marker)


def pytest_collection_modifyitems(config, items):
    """Modify collected test items"""
    for item in items:
        # Auto-mark based on nodeid
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)
        elif "performance" in item.nodeid.lower():
            item.add_marker(pytest.mark.performance)
        else:
            item.add_marker(pytest.mark.unit)

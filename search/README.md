# Smart Search Pro - Advanced Search Module

High-performance file search module with Everything SDK integration and Windows Search API fallback.

## Features

- **Everything SDK Integration**: Lightning-fast search using Everything's indexing engine
- **Windows Search Fallback**: Automatic fallback to Windows Search API
- **Advanced Query Parsing**: Support for complex queries with multiple filters
- **Threading Support**: Async search with cancellation and progress callbacks
- **Smart History**: Search history with autocomplete suggestions
- **Comprehensive Filtering**: File type, size, date, path, and content filters
- **High Performance**: Optimized for speed with parallel processing

## Installation

### Prerequisites

1. **Everything** (recommended for best performance)
   - Download from: https://www.voidtools.com/
   - Install to: `C:\Program Files\Everything\`
   - Ensure Everything service is running

2. **Python Packages**
   ```bash
   pip install pywin32  # For Windows Search API fallback
   ```

### Setup

No additional setup required. The module automatically detects and uses available search backends.

## Quick Start

```python
from smart_search.search import SearchEngine

# Initialize search engine
engine = SearchEngine()

# Simple search
results = engine.search("python", max_results=10)

for result in results:
    print(f"{result.filename} - {result.full_path}")
```

## Query Syntax

### Basic Queries

```python
# Simple keyword
"python"

# Multiple keywords (OR)
"python * javascript * rust"

# Quoted phrases
'"machine learning"'
```

### File Type Filters

```python
# Single extension
"ext:pdf"

# Multiple extensions
"ext:pdf ext:docx"

# File type groups
"type:image"      # jpg, png, gif, etc.
"type:video"      # mp4, avi, mkv, etc.
"type:audio"      # mp3, wav, flac, etc.
"type:document"   # doc, docx, pdf, txt, etc.
"type:code"       # py, js, java, cpp, etc.
```

### Size Filters

```python
# Greater than
"size:>10mb"
"size:>1gb"

# Less than
"size:<100kb"
"size:<1gb"

# Greater or equal
"size:>=500mb"

# Less or equal
"size:<=10mb"

# Supported units: b, kb, mb, gb, tb
```

### Date Filters

```python
# Presets
"modified:today"
"modified:yesterday"
"modified:thisweek"
"modified:lastweek"
"modified:thismonth"
"modified:lastmonth"
"modified:thisyear"
"modified:lastyear"

# Specific dates
"created:2024"              # Year
"created:2024-03"           # Year-Month
"created:2024-03-15"        # Full date

# Date comparisons
"modified:>2024-01-01"      # After
"modified:<2024-12-31"      # Before
"modified:>=2024-06-01"     # On or after

# Other date fields
"created:today"
"accessed:thisweek"
```

### Path Filters

```python
# Contains path
"path:documents"
"folder:downloads"

# Exact path match
"path:C:\\Users\\Documents"
```

### Content Filters

```python
# Search file content (text files only)
"content:password"
"content:TODO"
```

### Regex Filters

```python
# Regular expression search
"regex:test_.*\\.py"
"regex:report_\\d{4}\\.pdf"
```

### Complex Queries

Combine multiple filters:

```python
# Documents modified this week
"ext:pdf ext:docx modified:thisweek"

# Large images in specific folder
"type:image size:>5mb path:photos"

# Python files with specific content
"ext:py content:import path:projects"

# Reports from 2024 between 1-50 MB
"report * analysis ext:pdf size:>1mb size:<50mb created:2024"
```

## API Reference

### SearchEngine

Main search engine class.

```python
from smart_search.search import SearchEngine

engine = SearchEngine(
    everything_dll_path=None,  # Optional: Custom DLL path
    max_workers=4              # Thread pool size
)
```

#### Methods

**`search(query, max_results=1000, sort_by="name", ascending=True, progress_callback=None)`**

Synchronous search.

```python
results = engine.search(
    query="ext:pdf size:>10mb",
    max_results=100,
    sort_by="modified",  # name, path, size, modified, created, accessed
    ascending=False,
    progress_callback=lambda current, total: print(f"{current}/{total}")
)
```

**`search_async(query, max_results=1000, callback=None, progress_callback=None)`**

Asynchronous search.

```python
def on_results(results):
    print(f"Found {len(results)} results")

thread = engine.search_async(
    query="python",
    callback=on_results,
    progress_callback=lambda c, t: print(f"{c}/{t}")
)

# Cancel if needed
engine.cancel()
```

**`get_suggestions(partial_query, limit=10)`**

Get search suggestions.

```python
suggestions = engine.get_suggestions("ext:", limit=5)
```

### SearchResult

Search result object.

```python
@dataclass
class SearchResult:
    filename: str           # File/folder name
    path: str              # Parent directory path
    full_path: str         # Complete path
    extension: str         # File extension (without dot)
    size: int             # Size in bytes
    date_created: int     # Windows FILETIME
    date_modified: int    # Windows FILETIME
    date_accessed: int    # Windows FILETIME
    attributes: int       # File attributes
    is_folder: bool       # True if directory
    relevance_score: float # Relevance score (default: 1.0)
```

### QueryParser

Parse search queries.

```python
from smart_search.search import QueryParser

parser = QueryParser()
parsed = parser.parse("ext:pdf size:>10mb modified:today")

print(parsed.extensions)      # {'pdf'}
print(parsed.size_filters)    # [SizeFilter(...)]
print(parsed.date_filters)    # [DateFilter(...)]

# Build Everything query
everything_query = parser.build_everything_query(parsed)
```

### SearchHistory

Manage search history with autocomplete.

```python
from smart_search.search import SearchHistory

history = SearchHistory(
    history_file="~/.smart_search_history.json",
    max_entries=1000,
    max_suggestions=20
)

# Add search
history.add(
    query="python tutorial",
    result_count=150,
    execution_time_ms=45.2,
    filters_used=["ext", "size"]
)

# Get recent searches
recent = history.get_recent(limit=10)

# Get popular searches
popular = history.get_popular(limit=10)

# Get autocomplete suggestions
suggestions = history.get_suggestions("pyth", limit=5)

# Search history
results = history.search("python", limit=50)

# Statistics
stats = history.get_statistics()
print(stats["total_searches"])
print(stats["average_time_ms"])

# Export/Import
history.export_to_json("backup.json")
history.import_from_json("backup.json", merge=True)

# Clear
history.clear()
```

### Filters

Filter search results.

```python
from smart_search.search import (
    FileTypeFilter,
    SizeFilter,
    DateFilter,
    PathFilter,
    ContentFilter,
    FilterChain
)

# Create filter chain
chain = FilterChain()
chain.add_filter(FileTypeFilter({"pdf", "docx"}))
chain.add_filter(SizeFilterImpl([...]))
chain.add_filter(DateFilterImpl([...]))

# Or create from parsed query
from smart_search.search.filters import create_filter_chain_from_query

parsed = parser.parse("ext:pdf size:>10mb")
chain = create_filter_chain_from_query(parsed)

# Apply to results
filtered_results = [r for r in results if chain.matches(r)]
```

## Examples

### Example 1: Basic Search

```python
from smart_search.search import SearchEngine

engine = SearchEngine()

# Search for Python files
results = engine.search("ext:py", max_results=10)

for result in results:
    print(f"{result.filename} ({result.size / 1024:.1f} KB)")
```

### Example 2: Advanced Filtering

```python
# Large PDFs modified this week in Documents folder
query = "ext:pdf size:>10mb modified:thisweek path:documents"
results = engine.search(query, max_results=50)

for result in results:
    size_mb = result.size / (1024 * 1024)
    print(f"{result.filename} - {size_mb:.2f} MB")
```

### Example 3: Async Search with Progress

```python
def progress_callback(current, total):
    if total > 0:
        percent = (current / total) * 100
        print(f"\rProgress: {percent:.1f}%", end="")

def results_callback(results):
    print(f"\nFound {len(results)} results")

thread = engine.search_async(
    query="type:image size:>1mb",
    max_results=100,
    callback=results_callback,
    progress_callback=progress_callback
)

thread.join()
```

### Example 4: Search History with Autocomplete

```python
from smart_search.search import SearchHistory

history = SearchHistory()

# Add searches
history.add("python tutorial", result_count=150)
history.add("javascript guide", result_count=200)
history.add("python examples", result_count=300)

# Get suggestions as user types
suggestions = history.get_suggestions("pyth")
# Returns: ["python tutorial", "python examples"]

# Get popular searches
popular = history.get_popular(limit=5)
```

### Example 5: Complex Query

```python
# Reports and analysis documents:
# - PDF or DOCX format
# - Between 1MB and 50MB
# - Modified this month
# - In documents folder
query = """
    report * analysis
    ext:pdf ext:docx
    size:>1mb size:<50mb
    modified:thismonth
    path:documents
"""

results = engine.search(query, max_results=20)
```

## Performance

### Everything SDK Performance

When Everything SDK is available:

- **Instant Results**: Most queries return in <50ms
- **Large Result Sets**: 100,000+ files in <100ms
- **Regex Support**: Native regex support
- **Real-time Updates**: Index updates automatically

### Windows Search Performance

When falling back to Windows Search:

- **Slower**: 500ms - 2000ms for typical queries
- **Limited**: May not index all locations
- **Requires Setup**: Windows Search service must be enabled

### Optimization Tips

1. **Use Everything**: Install Everything for best performance
2. **Limit Results**: Use `max_results` to limit result set size
3. **Specific Filters**: More specific queries are faster
4. **Async for Large Queries**: Use `search_async` for potentially large result sets
5. **Content Search**: Content search is slow; use sparingly

## Testing

Run the test suite:

```bash
# Install pytest
pip install pytest pytest-cov

# Run tests
cd C:\Users\ramos\.local\bin\smart_search\search
python -m pytest test_search.py -v

# With coverage
python -m pytest test_search.py -v --cov=. --cov-report=html
```

## Examples Runner

Run interactive examples:

```bash
cd C:\Users\ramos\.local\bin\smart_search\search
python examples.py
```

Available examples:
1. Basic Search
2. Advanced Filters
3. Query Parsing
4. Async Search
5. Search History
6. Size and Date Filters
7. Complex Query
8. Performance Test

## Troubleshooting

### Everything SDK not detected

1. Verify Everything is installed: `C:\Program Files\Everything\`
2. Check Everything is running: Look for Everything in system tray
3. Verify DLL exists: `C:\Program Files\Everything\Everything64.dll`
4. Try specifying DLL path manually:
   ```python
   engine = SearchEngine(
       everything_dll_path=r"C:\Program Files\Everything\Everything64.dll"
   )
   ```

### Windows Search not working

1. Enable Windows Search service:
   - Open Services (services.msc)
   - Find "Windows Search"
   - Set to Automatic and Start

2. Rebuild Windows Search index:
   - Open Indexing Options
   - Click "Advanced"
   - Click "Rebuild"

### No search backend available

```python
engine = SearchEngine()
if not engine.is_available:
    print("No search backend available!")
    print("Install Everything or enable Windows Search")
```

### Slow content search

Content search reads file contents and is inherently slow. Optimize:

1. Limit file size: Content filter skips files >10MB by default
2. Use file type filters: Only text files are searched
3. Reduce result set: Use other filters first
4. Consider external tools: Use grep-like tools for code search

## Architecture

### Module Structure

```
search/
├── __init__.py          # Package exports
├── engine.py            # Main search engine
├── query_parser.py      # Query parsing
├── filters.py           # Filter implementations
├── history.py           # Search history
├── everything_sdk.py    # Everything SDK wrapper
├── test_search.py       # Test suite
├── examples.py          # Usage examples
└── README.md           # This file
```

### Design Principles

1. **Separation of Concerns**: Each module has a single responsibility
2. **Type Safety**: Full type hints throughout
3. **Error Handling**: Graceful degradation and fallbacks
4. **Performance**: Threading, caching, and optimization
5. **Extensibility**: Easy to add new filters and backends

### Threading Model

- **Main Thread**: Query parsing and result assembly
- **Worker Threads**: Parallel filtering of large result sets
- **Async Thread**: Background search execution
- **ThreadPoolExecutor**: Configurable worker pool

## License

Part of Smart Search Pro. See main project for license information.

## Credits

- Everything SDK by voidtools: https://www.voidtools.com/
- Windows Search API by Microsoft

## Version

1.0.0 (2025-12-12)

---

For more information, see the main Smart Search Pro documentation.

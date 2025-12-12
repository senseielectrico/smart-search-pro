# Smart Search Pro - Quick Start Guide

Get started with Smart Search Pro in 5 minutes!

## Installation

### 1. Install Everything (Recommended)

For best performance, install Everything search engine:

1. Download from: https://www.voidtools.com/
2. Run installer (default location: `C:\Program Files\Everything\`)
3. Start Everything.exe (it will appear in system tray)
4. Wait for initial indexing to complete (~30 seconds for 100K files)

### 2. Install Python Dependencies

```bash
cd C:\Users\ramos\.local\bin\smart_search\search
pip install -r requirements.txt
```

### 3. Verify Installation

```bash
python validate.py
```

You should see all checks pass with either Everything SDK or Windows Search backend.

## Basic Usage

### Example 1: Simple Search

```python
from smart_search.search import SearchEngine

# Initialize engine
engine = SearchEngine()

# Search for Python files
results = engine.search("ext:py", max_results=10)

# Display results
for result in results:
    print(f"{result.filename} - {result.full_path}")
```

### Example 2: Advanced Filters

```python
# Find large PDFs modified this week
query = "ext:pdf size:>10mb modified:thisweek"
results = engine.search(query, max_results=50)

for result in results:
    size_mb = result.size / (1024 * 1024)
    print(f"{result.filename} ({size_mb:.1f} MB)")
```

### Example 3: Multiple Keywords

```python
# Find files with "report" OR "analysis"
query = "report * analysis ext:pdf"
results = engine.search(query)
```

### Example 4: Search History

```python
from smart_search.search import SearchHistory

# Create history manager
history = SearchHistory()

# Add search
history.add("python tutorial", result_count=150, execution_time_ms=45.2)

# Get autocomplete suggestions
suggestions = history.get_suggestions("pyth", limit=5)
print(suggestions)  # ["python tutorial", ...]
```

## Query Syntax Reference

### File Extensions
```
ext:pdf              # Single extension
ext:pdf ext:docx     # Multiple extensions
```

### File Types
```
type:image          # jpg, png, gif, etc.
type:video          # mp4, avi, mkv, etc.
type:document       # pdf, doc, docx, txt, etc.
type:code           # py, js, java, cpp, etc.
```

### Size Filters
```
size:>10mb          # Larger than 10 MB
size:<1gb           # Smaller than 1 GB
size:>=500kb        # At least 500 KB
```

### Date Filters
```
modified:today      # Modified today
modified:thisweek   # Modified this week
created:2024        # Created in 2024
modified:>2024-01-01  # After January 1, 2024
```

### Path Filters
```
path:documents      # Contains "documents" in path
folder:downloads    # In downloads folder
```

### Combined Query
```
report * analysis ext:pdf size:>1mb modified:thisweek path:documents
```

This finds PDFs with "report" or "analysis" in the name, larger than 1MB, modified this week, in documents folder.

## Running Examples

```bash
cd C:\Users\ramos\.local\bin\smart_search\search
python examples.py
```

Choose from:
1. Basic Search
2. Advanced Filters
3. Query Parsing
4. Async Search
5. Search History
6. Size and Date Filters
7. Complex Query
8. Performance Test

## Common Use Cases

### Find Large Files

```python
# Files larger than 100 MB
results = engine.search("size:>100mb", max_results=20)
```

### Find Recent Files

```python
# Files modified today
results = engine.search("modified:today")

# Files created this week
results = engine.search("created:thisweek")
```

### Find Old Files

```python
# Files not modified in over a year
results = engine.search("modified:<2023-01-01")
```

### Find Specific File Types

```python
# All Python code files
results = engine.search("ext:py")

# All images
results = engine.search("type:image")

# Large videos
results = engine.search("type:video size:>500mb")
```

### Search in Specific Folder

```python
# PDFs in Documents
results = engine.search("ext:pdf path:documents")

# Everything in Downloads
results = engine.search("path:downloads")
```

### Complex Searches

```python
# Project reports from 2024, PDF or Word, between 1-50 MB
query = "report * project ext:pdf ext:docx size:>1mb size:<50mb created:2024"
results = engine.search(query)
```

## Async Search

For potentially slow searches:

```python
def on_complete(results):
    print(f"Search completed! Found {len(results)} files")

def on_progress(current, total):
    print(f"Progress: {current}/{total}")

# Start async search
thread = engine.search_async(
    query="type:video size:>1gb",
    max_results=100,
    callback=on_complete,
    progress_callback=on_progress
)

# Do other work...

# Wait for completion
thread.join()
```

## Performance Tips

1. **Install Everything**: 10-100x faster than Windows Search
2. **Use Specific Filters**: Narrow down results quickly
3. **Limit Results**: Use `max_results` parameter
4. **Avoid Content Search**: Very slow, use sparingly
5. **Use Async for Large Searches**: Keeps UI responsive

## Troubleshooting

### Everything not detected

```python
# Specify DLL path manually
engine = SearchEngine(
    everything_dll_path=r"C:\Program Files\Everything\Everything64.dll"
)
```

### Slow searches

- Check if Everything.exe is running
- Reduce `max_results`
- Use more specific filters
- Avoid content search on many files

### No results found

- Check spelling
- Try broader search terms
- Remove some filters
- Use `*` for multiple keywords

## Next Steps

1. Read full documentation: `README.md`
2. Run test suite: `pytest test_search.py -v`
3. Try interactive examples: `python examples.py`
4. Integrate into your application

## API Quick Reference

```python
# Search Engine
engine = SearchEngine(max_workers=4)
results = engine.search(query, max_results=1000)
thread = engine.search_async(query, callback=func)
engine.cancel()  # Cancel search
engine.shutdown()  # Cleanup

# Query Parser
parser = QueryParser()
parsed = parser.parse(query)
everything_query = parser.build_everything_query(parsed)

# Search History
history = SearchHistory()
history.add(query, result_count=100)
suggestions = history.get_suggestions(partial)
recent = history.get_recent(limit=10)
popular = history.get_popular(limit=10)

# Search Result
result.filename        # File name
result.full_path       # Complete path
result.size           # Size in bytes
result.extension      # File extension
result.is_folder      # True if directory
```

## Getting Help

- Full documentation: `README.md`
- Example code: `examples.py`
- Test cases: `test_search.py`
- Validation: `python validate.py`

## Version

1.0.0 (2025-12-12)

---

Happy searching!

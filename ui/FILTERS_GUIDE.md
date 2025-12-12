# Advanced Filters Guide

## Overview

Smart Search Pro now includes an intuitive filter system with toggleable chips and an expandable advanced panel. Filters are applied in real-time and can be combined for powerful search refinement.

## Filter Chips

### Size Filters

Quick preset size filters for common use cases:

- **>1KB** - Files larger than 1 kilobyte
- **>1MB** - Files larger than 1 megabyte
- **>100MB** - Files larger than 100 megabytes
- **>1GB** - Files larger than 1 gigabyte

**Usage:**
- Click a chip to activate it (turns blue)
- Click again to deactivate
- Only one size filter can be active at a time

### Date Filters

Quick preset date filters based on modification time:

- **Today** - Files modified today
- **Week** - Files modified this week
- **Month** - Files modified this month
- **Year** - Files modified this year

**Usage:**
- Click a chip to activate it (turns blue)
- Click again to deactivate
- Only one date filter can be active at a time
- By default applies to "Modified" date

### Type Filters

File type category filters:

- **Docs** - Documents (pdf, doc, docx, txt, etc.)
- **Images** - Image files (jpg, png, gif, svg, etc.)
- **Videos** - Video files (mp4, avi, mkv, etc.)
- **Audio** - Audio files (mp3, wav, flac, etc.)
- **Archives** - Compressed files (zip, rar, 7z, etc.)
- **Code** - Source code files (py, js, ts, java, etc.)

**Usage:**
- Click a chip to activate it (turns blue)
- Click again to deactivate
- Only one type filter can be active at a time

## Advanced Filters Panel

Click **"More Filters"** to expand the advanced options panel.

### Extensions Filter

Specify exact file extensions to search for.

**Format:** Comma-separated list of extensions (with or without dots)

**Examples:**
```
pdf, doc, docx
.jpg, .png, .gif
py, js, ts
```

**Behavior:**
- Automatically applied as you type
- Multiple extensions are combined with OR logic
- Case-insensitive

### Custom Size Filter

Create custom size filters with specific values.

**Components:**
- **Operator:** >, <, >=, <=, =
- **Value:** Numeric value
- **Unit:** KB, MB, GB

**Examples:**
- `> 500 MB` - Larger than 500 megabytes
- `< 10 KB` - Smaller than 10 kilobytes
- `>= 2 GB` - 2 gigabytes or larger

**Usage:**
1. Select operator
2. Enter value
3. Select unit
4. Click **Apply**

### Custom Date Filter

Create custom date filters with specific dates.

**Components:**
- **Field:** Modified, Created, or Accessed
- **Operator:** >, <, >=, <=, =
- **Date:** Date picker

**Examples:**
- `Modified > 2024-01-01` - Modified after January 1, 2024
- `Created < 2023-12-31` - Created before December 31, 2023
- `Accessed = 2024-06-15` - Accessed on June 15, 2024

**Usage:**
1. Select date field (Modified/Created/Accessed)
2. Select operator
3. Pick date from calendar
4. Click **Apply**

## Active Filters Display

When filters are active, they appear in a dedicated row labeled **"Active:"**

**Features:**
- Shows all currently active filters
- Each filter is displayed as a removable chip
- Click the × on a chip to remove that specific filter
- Human-readable format (e.g., "size: >1mb", "type: document")

## Clear All Filters

The **"Clear All"** button appears when any filters are active.

**Behavior:**
- Removes all active filters
- Resets all chip states
- Clears extension input
- Keeps search query intact

## Combining Filters

Multiple filters can be combined for refined searches:

**Example 1:** Large recent documents
- Size: >10MB
- Date: Week
- Type: Docs

**Example 2:** Code files with specific extensions
- Type: Code
- Extensions: py, js
- Date: Month

**Example 3:** Custom complex filter
- Custom Size: > 100 MB
- Custom Date: Modified > 2024-01-01
- Extensions: mp4, mkv

## Filter Integration with Backend

Filters are automatically converted to query parser format:

### UI Filter → Query String

```python
# UI Filters
{
    'size': '>1mb',
    'type': 'document',
    'modified': 'today'
}

# Converted Query
"invoice size:>1mb type:document modified:today"
```

### Backend Processing

1. **Query Parser** - Parses filter syntax
2. **Filter Chain** - Applies filters sequentially
3. **Results** - Returns filtered search results

## Performance Considerations

### Efficient Filters
- **Size filters** - Very fast (metadata only)
- **Date filters** - Very fast (metadata only)
- **Type filters** - Fast (extension matching)
- **Extension filters** - Fast (pattern matching)

### Resource-Intensive Filters
- **Content search** - Slower (reads file contents)
- Large file sets with multiple filters

### Best Practices

1. **Start broad** - Use type filters first
2. **Refine progressively** - Add size/date filters
3. **Specific extensions** - Use for targeted searches
4. **Content search last** - Only when necessary

## Keyboard Shortcuts

- **Enter** - Execute search with current filters
- **Esc** - Clear search input (keeps filters)
- **Ctrl+F** - Focus search input

## Filter Persistence

Filters remain active across searches:
- Perform multiple searches with same filters
- Modify search query without losing filters
- Clear filters explicitly when done

## Advanced Use Cases

### Finding Large Old Files
```
Size: >100MB
Date: Custom (Modified < 2023-01-01)
```

### Recent Work Files
```
Type: Docs
Date: Week
Path: C:\Users\username\Documents
```

### Code Review
```
Type: Code
Extensions: py, js, ts
Date: Today
Content: "TODO"
```

### Media Organization
```
Type: Videos
Size: >500MB
Date: Month
```

## Troubleshooting

### Filters Not Working

**Check:**
1. Filter is activated (chip is blue)
2. No conflicting filters
3. Backend connection active
4. Search query is valid

### Too Many/Few Results

**Try:**
1. Adjust filter specificity
2. Combine multiple filters
3. Use custom filters for precision
4. Check date range settings

### Performance Issues

**Solutions:**
1. Add size filters to reduce set
2. Use type filters early
3. Avoid broad date ranges
4. Limit extension list

## API Reference

### SearchPanel Signals

```python
# Emitted when search is requested
search_requested = pyqtSignal(dict)  # params with 'query', 'filters', etc.

# Emitted when filters change
filter_changed = pyqtSignal(dict)  # active_filters dict

# Emitted during instant search
instant_search_requested = pyqtSignal(dict)  # params with 'instant': True
```

### SearchPanel Methods

```python
# Get current filters
filters = search_panel.get_active_filters()

# Clear all filters
search_panel.clear_filters()

# Set search text
search_panel.set_search_text("my query")

# Get search text
query = search_panel.get_search_text()
```

### FilterIntegration Utility

```python
from ui.filter_integration import FilterIntegration

# Convert UI filters to query
query = FilterIntegration.ui_filters_to_query("base_query", filters)

# Get filter summary
summary = FilterIntegration.get_filter_summary(filters)

# Validate filters
is_valid, error = FilterIntegration.validate_filters(filters)

# Merge filter sets
merged = FilterIntegration.merge_filters(filters1, filters2)
```

## Examples

### Example 1: Basic Filtering

```python
# Search for large PDF files
search_panel.set_search_text("invoice")
# User clicks: Size >1MB chip
# User clicks: Type Docs chip
# User types in Extensions: pdf
# User clicks Search
```

### Example 2: Advanced Custom Filtering

```python
# Search for recent large video files
# User opens More Filters
# Custom Size: > 500 MB
# Custom Date: Modified > 2024-06-01
# Extensions: mp4, mkv, avi
# User clicks Search
```

### Example 3: Programmatic Filtering

```python
from ui.filter_integration import FilterIntegration

# Build filter dict
filters = {
    'size': '>100mb',
    'type': 'video',
    'modified': 'thismonth',
    'extensions': ['mp4', 'mkv']
}

# Validate
valid, error = FilterIntegration.validate_filters(filters)
if valid:
    query = FilterIntegration.ui_filters_to_query("vacation", filters)
    # Execute search with query
```

## Future Enhancements

Planned features:
- [ ] Filter presets/templates
- [ ] Save filter combinations
- [ ] Filter history
- [ ] Smart filter suggestions
- [ ] Boolean operators (AND/OR)
- [ ] Exclude filters (NOT)
- [ ] Path browser for path filters
- [ ] Content preview for content filters

## Support

For issues or questions:
- Check TROUBLESHOOTING.md
- Review search/query_parser.py documentation
- Review search/filters.py documentation
- Submit issue on GitHub

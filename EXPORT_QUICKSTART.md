# Export Quick Start Guide

## 30-Second Quick Start

### Export to CSV (Fastest)
1. Press `Ctrl+E`
2. Keep CSV selected (default)
3. Click "Browse" and choose location
4. Click "Export"

### Copy to Clipboard (Instant)
1. Press `Ctrl+Shift+C`
2. Paste anywhere (Excel, Notepad, etc.)

## Common Tasks

### Export All Results to Excel
```
File > Export > Export All Results (or Ctrl+E)
→ Select "Excel - XLSX with formatting"
→ Browse to save location
→ Export
```

### Export Selected Files Only
```
1. Select files in results (Ctrl+Click for multiple)
2. Right-click > Export Selected...
3. Choose format
4. Export
```

### Create HTML Report
```
File > Export > Export All Results
→ Select "HTML - Interactive report"
→ Click "HTML Options" tab
→ Set title and theme
→ Export
→ Open in browser
```

### Quick CSV with Custom Settings
```
File > Export > Quick Export to CSV
→ Choose save location
→ Done (uses smart defaults)
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+E` | Export all results |
| `Ctrl+Shift+E` | Export selected only |
| `Ctrl+Shift+C` | Copy to clipboard |

## Export Formats at a Glance

### CSV
- **Best for**: Excel import, data analysis
- **Speed**: Fast
- **Features**: Configurable delimiter, encoding
- **Use when**: You need simple, universal format

### Excel
- **Best for**: Professional reports, sharing
- **Speed**: Medium
- **Features**: Formatting, multiple sheets, summary
- **Use when**: You want polished, interactive spreadsheets

### HTML
- **Best for**: Viewing in browser, sharing online
- **Speed**: Fast
- **Features**: Sortable, searchable, responsive
- **Use when**: You need interactive web reports

### JSON
- **Best for**: Programming, APIs, data processing
- **Speed**: Fast
- **Features**: Structured data, metadata
- **Use when**: You need machine-readable format

### Clipboard
- **Best for**: Quick sharing, one-time use
- **Speed**: Instant
- **Features**: Multiple format options
- **Use when**: You need immediate access

## Quick Tips

### For Best Excel Compatibility
1. Use "UTF-8 with BOM (Excel)" encoding in CSV
2. Or use Excel format directly
3. Enable "Excel compatible format" option

### For Large Datasets
1. Use CSV for speed
2. Set "Max results" limit if needed
3. Split by extension/folder in Excel

### For Sharing
1. HTML reports are self-contained
2. Include summary statistics
3. Enable dark/light theme toggle

### For Processing
1. JSON format preserves data types
2. Use JSON Lines for streaming
3. Include metadata for context

## Default Settings

The export dialog remembers your preferences:
- Last used format
- Column selections
- Output directory
- Format-specific options

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't export | Check you have search results loaded |
| Excel error | Install: `pip install openpyxl` |
| Clipboard fails | Install: `pip install pyperclip` |
| File exists | Enable "Overwrite" or choose new name |
| Slow export | Reduce columns or use CSV format |

## Next Steps

- Read full documentation: `EXPORT_INTEGRATION.md`
- View export backend docs: `export/README.md`
- Run test: `python test_export_integration.py`

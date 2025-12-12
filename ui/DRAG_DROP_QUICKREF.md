# Drag & Drop Quick Reference

## User Actions

### Drag FROM Results Panel

| Action | Result |
|--------|--------|
| Select files + Drag | Multi-file drag with preview |
| Ctrl + Drag | Force COPY operation |
| Shift + Drag | Force MOVE operation |
| Drop to Explorer | Files copied/moved to Explorer |
| Drop to Operations Panel | Context menu: Copy/Move/Add |

### Drop TO Operations Panel

| Action | Result |
|--------|--------|
| Drag files from Explorer | Blue highlight appears |
| Hold Ctrl while hovering | Shows "Drop to COPY" |
| Hold Shift while hovering | Shows "Drop to MOVE" |
| Drop with destination set | Context menu: Copy/Move |
| Drop without destination | Added to file selection |

### Drop TO Directory Tree

| Action | Result |
|--------|--------|
| Drag folder from Explorer | Blue border highlight |
| Drop folder | Added to tree and auto-checked |
| Non-folder dropped | Rejected |

## Visual Feedback

### Results Panel
- **Drag Preview**: File count + first 2 filenames
- **Cursor**: Copy/Move cursor based on modifier

### Operations Panel
- **Hover**: Blue dashed border + light background
- **Info Bar**: "Drop to COPY/MOVE" hint

### Directory Tree
- **Hover**: Blue solid border + light tint
- **Drop**: Folder expands in tree

## Keyboard Shortcuts

| Key | Effect |
|-----|--------|
| Ctrl | Force copy operation |
| Shift | Force move operation |
| Alt | Force link operation (create shortcut) |
| Esc | Cancel drag |

## Common Workflows

### Copy Files to Another Location
1. Select files in Results panel
2. Drag to Operations panel
3. Set destination folder
4. Right-click dropped files → Copy

### Quick Search in Folder
1. Drag folder from Explorer
2. Drop on Directory Tree
3. Folder auto-checked
4. Click Search

### Multi-File Operations
1. Ctrl+Click to select multiple files
2. Drag selection together
3. Drop destination
4. All files processed as batch

## Integration Points

### Components with Drag Support (FROM)
- Results Panel table
- (Future: Operations queue, Preview panel)

### Components with Drop Support (TO)
- Operations Panel (files/folders)
- Directory Tree (folders only)
- (Future: Search panel, Custom lists)

## Code Usage

### Check if Dragging
```python
if self.drag_handler.current_drag_paths:
    # Drag in progress
```

### Get Current Operation
```python
operation = self.drag_handler.drag_operation
# Returns: DragOperation.COPY, .MOVE, or .LINK
```

### Detect Drop Zone
```python
self.drag_handler.files_dropped.connect(
    lambda files, zone: print(f"Dropped to {zone}")
)
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Drag not starting | Move mouse 10px minimum |
| Drop rejected | Check if target accepts that file type |
| No visual feedback | Check `setAcceptDrops(True)` |
| Wrong operation | Check keyboard modifiers |
| Context menu missing | Ensure destination folder set |

## Testing Checklist

- [ ] Single file drag to Explorer
- [ ] Multi-file drag with preview
- [ ] Ctrl+Drag shows copy cursor
- [ ] Shift+Drag shows move cursor
- [ ] Drop to Operations shows context menu
- [ ] Drop folder to Tree adds and checks
- [ ] Hover shows visual feedback
- [ ] Drag leave removes feedback
- [ ] Non-folder rejected by Tree
- [ ] File operations execute correctly

## Performance Tips

- Drag preview cached for same selection
- Drop zones only process when hovering
- Large selections (100+ files) still fast
- Visual feedback CSS-based (no repaints)

## Files Modified

- `ui/drag_drop.py` - NEW (core implementation)
- `ui/results_panel.py` - Added drag support
- `ui/operations_panel.py` - Enhanced drop support
- `ui/directory_tree.py` - Added drop support
- `ui/drag_drop_demo.py` - NEW (demo app)

## Demo

```bash
python -m ui.drag_drop_demo
```

## Version

**1.0.0** - Initial complete implementation
- Full Windows Shell integration
- Multi-file drag with preview
- Context menu on drop
- Visual feedback system
- Keyboard modifier support

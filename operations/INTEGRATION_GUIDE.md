# Integration Guide: File Operations Module with Smart Search Pro

## Overview

This guide shows how to integrate the TeraCopy-style file operations module into Smart Search Pro's UI and backend.

## Quick Integration

### 1. Add Operations Manager to Backend

```python
# In backend.py
from operations import OperationsManager, OperationPriority

class SmartSearchBackend:
    def __init__(self):
        # Existing initialization...
        self.operations_manager = OperationsManager(
            max_concurrent_operations=2,
            history_file="operations_history.json",
            auto_save_history=True
        )

    def shutdown(self):
        """Cleanup on shutdown."""
        if hasattr(self, 'operations_manager'):
            self.operations_manager.shutdown()
```

### 2. Add Context Menu Actions

```python
# Add to context menu in ui.py
def create_context_menu(self, results_table, event):
    """Create context menu for search results."""
    menu = tk.Menu(results_table, tearoff=0)

    # Get selected files
    selected_items = results_table.selection()
    if not selected_items:
        return

    # Copy operations
    menu.add_command(
        label="Copy to...",
        command=lambda: self.copy_files_dialog(selected_items)
    )

    menu.add_command(
        label="Move to...",
        command=lambda: self.move_files_dialog(selected_items)
    )

    menu.add_separator()

    # Verification
    menu.add_command(
        label="Calculate Hash (MD5)",
        command=lambda: self.calculate_hashes(selected_items, 'md5')
    )

    menu.add_command(
        label="Calculate Hash (SHA-256)",
        command=lambda: self.calculate_hashes(selected_items, 'sha256')
    )

    menu.tk_popup(event.x_root, event.y_root)
```

### 3. Implement Copy Dialog

```python
# In ui.py
import tkinter as tk
from tkinter import filedialog, messagebox
from operations import OperationPriority

def copy_files_dialog(self, selected_items):
    """Show copy dialog and execute operation."""
    # Get selected file paths
    file_paths = []
    for item in selected_items:
        values = self.results_table.item(item, 'values')
        if values:
            file_paths.append(values[1])  # Assuming path is in column 1

    if not file_paths:
        messagebox.showwarning("No Files", "No files selected")
        return

    # Select destination
    dest_dir = filedialog.askdirectory(
        title="Select Destination Folder"
    )

    if not dest_dir:
        return

    # Create destination paths
    import os
    dest_paths = [
        os.path.join(dest_dir, os.path.basename(path))
        for path in file_paths
    ]

    # Queue operation
    op_id = self.backend.operations_manager.queue_copy(
        source_paths=file_paths,
        dest_paths=dest_paths,
        priority=OperationPriority.NORMAL,
        verify=True  # Enable verification
    )

    # Show progress window
    self.show_operation_progress(op_id)

    messagebox.showinfo(
        "Copy Started",
        f"Copying {len(file_paths)} files to {dest_dir}\n"
        f"Operation ID: {op_id[:8]}..."
    )
```

### 4. Create Progress Window

```python
# In ui.py
import tkinter as tk
from tkinter import ttk
import time

class OperationProgressWindow:
    """Window to show operation progress."""

    def __init__(self, parent, operations_manager, operation_id):
        self.operations_manager = operations_manager
        self.operation_id = operation_id

        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("File Operation Progress")
        self.window.geometry("600x400")

        # Operation info
        info_frame = ttk.Frame(self.window)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        self.op_label = ttk.Label(
            info_frame,
            text=f"Operation: {operation_id[:16]}...",
            font=('Arial', 10, 'bold')
        )
        self.op_label.pack(anchor=tk.W)

        # Progress bar
        progress_frame = ttk.Frame(self.window)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(progress_frame, text="Overall Progress:").pack(anchor=tk.W)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode='determinate',
            length=580
        )
        self.progress_bar.pack(fill=tk.X, pady=2)

        # Stats labels
        stats_frame = ttk.Frame(self.window)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)

        self.percent_label = ttk.Label(stats_frame, text="0.0%")
        self.percent_label.grid(row=0, column=0, sticky=tk.W)

        self.speed_label = ttk.Label(stats_frame, text="Speed: 0 MB/s")
        self.speed_label.grid(row=0, column=1, padx=20)

        self.eta_label = ttk.Label(stats_frame, text="ETA: Unknown")
        self.eta_label.grid(row=0, column=2, padx=20)

        self.files_label = ttk.Label(stats_frame, text="Files: 0/0")
        self.files_label.grid(row=1, column=0, sticky=tk.W, pady=5)

        # File list
        list_frame = ttk.Frame(self.window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        ttk.Label(list_frame, text="Files:").pack(anchor=tk.W)

        # Scrollable file list
        scroll = ttk.Scrollbar(list_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_list = tk.Listbox(list_frame, yscrollcommand=scroll.set)
        self.file_list.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.file_list.yview)

        # Control buttons
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        self.pause_btn = ttk.Button(
            button_frame,
            text="Pause",
            command=self.toggle_pause
        )
        self.pause_btn.pack(side=tk.LEFT, padx=5)

        self.cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_operation
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Close",
            command=self.window.destroy
        ).pack(side=tk.RIGHT, padx=5)

        # State
        self.paused = False

        # Start update loop
        self.update_progress()

    def update_progress(self):
        """Update progress display."""
        # Get current progress
        progress = self.operations_manager.get_progress(self.operation_id)
        operation = self.operations_manager.get_operation(self.operation_id)

        if not progress or not operation:
            self.window.after(100, self.update_progress)
            return

        # Update progress bar
        self.progress_bar['value'] = progress.progress_percent

        # Update labels
        self.percent_label.config(
            text=f"{progress.progress_percent:.1f}%"
        )

        tracker = self.operations_manager._progress_tracker
        self.speed_label.config(
            text=f"Speed: {tracker.format_speed(progress.current_speed)}"
        )

        self.eta_label.config(
            text=f"ETA: {tracker.format_time(progress.eta_seconds)}"
        )

        self.files_label.config(
            text=f"Files: {progress.completed_files}/{progress.total_files}"
        )

        # Update file list
        self.file_list.delete(0, tk.END)
        for file_path, file_progress in progress.files.items():
            import os
            filename = os.path.basename(file_path)

            if file_progress.error:
                status = "✗ FAILED"
                color = "red"
            elif file_progress.end_time:
                status = "✓ DONE"
                color = "green"
            else:
                status = f"{file_progress.progress_percent:.0f}%"
                color = "blue"

            self.file_list.insert(tk.END, f"{status:>8s}  {filename}")
            # Note: Listbox doesn't support per-item colors in standard tkinter

        # Check if complete
        if operation.status.value in ['completed', 'failed', 'cancelled']:
            self.pause_btn.config(state=tk.DISABLED)
            self.cancel_btn.config(state=tk.DISABLED)

            if operation.status.value == 'completed':
                messagebox.showinfo(
                    "Complete",
                    f"Operation completed successfully!\n"
                    f"Files: {operation.processed_files}/{operation.total_files}"
                )
            elif operation.status.value == 'failed':
                messagebox.showerror(
                    "Failed",
                    f"Operation failed: {operation.error}"
                )
            return

        # Continue updating
        self.window.after(500, self.update_progress)  # Update every 500ms

    def toggle_pause(self):
        """Pause or resume operation."""
        if self.paused:
            self.operations_manager.resume_operation(self.operation_id)
            self.pause_btn.config(text="Pause")
            self.paused = False
        else:
            self.operations_manager.pause_operation(self.operation_id)
            self.pause_btn.config(text="Resume")
            self.paused = True

    def cancel_operation(self):
        """Cancel the operation."""
        result = messagebox.askyesno(
            "Cancel Operation",
            "Are you sure you want to cancel this operation?"
        )

        if result:
            self.operations_manager.cancel_operation(self.operation_id)

# Add to UI class
def show_operation_progress(self, operation_id):
    """Show progress window for an operation."""
    OperationProgressWindow(
        self.root,
        self.backend.operations_manager,
        operation_id
    )
```

### 5. Add Hash Calculation

```python
# In ui.py
from operations.verifier import FileVerifier, HashAlgorithm
import tkinter.scrolledtext as scrolledtext

def calculate_hashes(self, selected_items, algorithm='md5'):
    """Calculate hashes for selected files."""
    # Get selected file paths
    file_paths = []
    for item in selected_items:
        values = self.results_table.item(item, 'values')
        if values:
            file_paths.append(values[1])

    if not file_paths:
        messagebox.showwarning("No Files", "No files selected")
        return

    # Create hash window
    hash_window = tk.Toplevel(self.root)
    hash_window.title(f"{algorithm.upper()} Hashes")
    hash_window.geometry("800x400")

    # Text area
    text = scrolledtext.ScrolledText(
        hash_window,
        font=('Courier', 9),
        wrap=tk.NONE
    )
    text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Calculate hashes
    text.insert(tk.END, f"Calculating {algorithm.upper()} hashes...\n\n")
    hash_window.update()

    algo_map = {
        'crc32': HashAlgorithm.CRC32,
        'md5': HashAlgorithm.MD5,
        'sha256': HashAlgorithm.SHA256,
    }

    verifier = FileVerifier(algorithm=algo_map.get(algorithm, HashAlgorithm.MD5))

    for file_path in file_paths:
        try:
            import os
            filename = os.path.basename(file_path)
            text.insert(tk.END, f"Processing: {filename}\n")
            hash_window.update()

            hash_value = verifier.calculate_hash(file_path)
            text.insert(tk.END, f"{hash_value} *{filename}\n\n")

        except Exception as e:
            text.insert(tk.END, f"Error: {str(e)}\n\n")

        hash_window.update()

    text.insert(tk.END, f"\nCompleted {len(file_paths)} files.")

    # Copy button
    def copy_to_clipboard():
        hash_window.clipboard_clear()
        hash_window.clipboard_append(text.get(1.0, tk.END))
        messagebox.showinfo("Copied", "Hashes copied to clipboard")

    ttk.Button(
        hash_window,
        text="Copy to Clipboard",
        command=copy_to_clipboard
    ).pack(pady=5)
```

### 6. Add Operations History View

```python
# In ui.py
def show_operations_history(self):
    """Show operations history window."""
    history_window = tk.Toplevel(self.root)
    history_window.title("Operations History")
    history_window.geometry("900x500")

    # Create treeview
    columns = ('ID', 'Type', 'Files', 'Status', 'Date')
    tree = ttk.Treeview(history_window, columns=columns, show='headings')

    for col in columns:
        tree.heading(col, text=col)

    tree.column('ID', width=100)
    tree.column('Type', width=80)
    tree.column('Files', width=80)
    tree.column('Status', width=100)
    tree.column('Date', width=150)

    tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Scrollbar
    scrollbar = ttk.Scrollbar(tree, orient=tk.VERTICAL, command=tree.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    tree.configure(yscrollcommand=scrollbar.set)

    # Load operations
    operations = self.backend.operations_manager.get_all_operations()

    for op in sorted(operations, key=lambda x: x.created_at, reverse=True):
        tree.insert('', tk.END, values=(
            op.operation_id[:16] + '...',
            op.operation_type.value,
            f"{op.processed_files}/{op.total_files}",
            op.status.value,
            op.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ))

    # Buttons
    button_frame = ttk.Frame(history_window)
    button_frame.pack(fill=tk.X, padx=5, pady=5)

    ttk.Button(
        button_frame,
        text="Clear Completed",
        command=lambda: self.clear_completed_operations(tree)
    ).pack(side=tk.LEFT, padx=5)

    ttk.Button(
        button_frame,
        text="Refresh",
        command=lambda: self.refresh_operations_history(tree)
    ).pack(side=tk.LEFT, padx=5)

    ttk.Button(
        button_frame,
        text="Close",
        command=history_window.destroy
    ).pack(side=tk.RIGHT, padx=5)

def clear_completed_operations(self, tree):
    """Clear completed operations."""
    count = self.backend.operations_manager.clear_completed()
    messagebox.showinfo("Cleared", f"Removed {count} completed operations")
    self.refresh_operations_history(tree)

def refresh_operations_history(self, tree):
    """Refresh operations history display."""
    # Clear tree
    for item in tree.get_children():
        tree.delete(item)

    # Reload
    operations = self.backend.operations_manager.get_all_operations()
    for op in sorted(operations, key=lambda x: x.created_at, reverse=True):
        tree.insert('', tk.END, values=(
            op.operation_id[:16] + '...',
            op.operation_type.value,
            f"{op.processed_files}/{op.total_files}",
            op.status.value,
            op.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ))
```

### 7. Add to Main Menu

```python
# In ui.py - create_menu_bar method
def create_menu_bar(self):
    """Create application menu bar."""
    menubar = tk.Menu(self.root)
    self.root.config(menu=menubar)

    # ... existing menus ...

    # Add Operations menu
    operations_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Operations", menu=operations_menu)

    operations_menu.add_command(
        label="View History",
        command=self.show_operations_history
    )

    operations_menu.add_command(
        label="Clear Completed",
        command=lambda: self.backend.operations_manager.clear_completed()
    )

    operations_menu.add_separator()

    operations_menu.add_command(
        label="Export History",
        command=self.export_operations_history
    )
```

## Complete Example Integration

Here's a complete minimal example:

```python
# minimal_integration.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from operations import OperationsManager, OperationPriority

class SimpleFileOperationsUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("File Operations Demo")
        self.root.geometry("500x300")

        # Create operations manager
        self.ops_manager = OperationsManager(
            max_concurrent_operations=2
        )

        # UI
        ttk.Label(
            self.root,
            text="Select files and choose operation:",
            font=('Arial', 12)
        ).pack(pady=10)

        # Buttons
        ttk.Button(
            self.root,
            text="Copy Files",
            command=self.copy_files
        ).pack(pady=5)

        ttk.Button(
            self.root,
            text="Move Files",
            command=self.move_files
        ).pack(pady=5)

        ttk.Button(
            self.root,
            text="View History",
            command=self.show_history
        ).pack(pady=5)

    def copy_files(self):
        """Copy files operation."""
        sources = filedialog.askopenfilenames(title="Select files to copy")
        if not sources:
            return

        dest_dir = filedialog.askdirectory(title="Select destination")
        if not dest_dir:
            return

        import os
        dests = [os.path.join(dest_dir, os.path.basename(s)) for s in sources]

        op_id = self.ops_manager.queue_copy(
            list(sources),
            dests,
            priority=OperationPriority.NORMAL,
            verify=True
        )

        messagebox.showinfo("Started", f"Copy operation started: {op_id[:8]}...")

    def move_files(self):
        """Move files operation."""
        sources = filedialog.askopenfilenames(title="Select files to move")
        if not sources:
            return

        dest_dir = filedialog.askdirectory(title="Select destination")
        if not dest_dir:
            return

        import os
        dests = [os.path.join(dest_dir, os.path.basename(s)) for s in sources]

        op_id = self.ops_manager.queue_move(
            list(sources),
            dests,
            priority=OperationPriority.NORMAL
        )

        messagebox.showinfo("Started", f"Move operation started: {op_id[:8]}...")

    def show_history(self):
        """Show operations history."""
        operations = self.ops_manager.get_all_operations()
        history_text = "\n".join([
            f"{op.operation_type.value}: {op.status.value} ({op.processed_files}/{op.total_files})"
            for op in operations
        ])

        messagebox.showinfo("History", history_text or "No operations yet")

    def run(self):
        """Run application."""
        try:
            self.root.mainloop()
        finally:
            self.ops_manager.shutdown()

if __name__ == "__main__":
    app = SimpleFileOperationsUI()
    app.run()
```

## Best Practices

1. **Always cleanup**: Call `operations_manager.shutdown()` on application exit
2. **Enable verification**: Use `verify=True` for important copy operations
3. **Handle errors**: Check operation status and display errors to user
4. **Progress feedback**: Always show progress window for long operations
5. **Save history**: Enable `auto_save_history=True` for audit trail

## Performance Tips

1. Use appropriate worker count based on storage type:
   - SSD to SSD: 4-8 workers
   - HDD to HDD: 2-4 workers
   - Network: 8-16 workers

2. Enable verification only when needed (adds overhead)

3. For large batches, monitor memory usage and process in chunks if needed

## Conclusion

The file operations module integrates seamlessly with Smart Search Pro's existing architecture. All components are thread-safe and designed for production use.

For more examples, see:
- `example_usage.py` - Standalone examples
- `test_operations.py` - Test suite demonstrating all features
- `README.md` - Complete API reference

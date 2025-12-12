"""
Rename History - Track and undo batch rename operations
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class HistoryEntry:
    """Single rename history entry"""
    timestamp: datetime
    operation_id: str
    operations: List[Dict]  # List of {old_path, new_path, success}
    pattern_used: str
    total_files: int
    success_count: int
    can_undo: bool = True

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'operation_id': self.operation_id,
            'operations': self.operations,
            'pattern_used': self.pattern_used,
            'total_files': self.total_files,
            'success_count': self.success_count,
            'can_undo': self.can_undo
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'HistoryEntry':
        """Create from dictionary"""
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            operation_id=data['operation_id'],
            operations=data['operations'],
            pattern_used=data['pattern_used'],
            total_files=data['total_files'],
            success_count=data['success_count'],
            can_undo=data.get('can_undo', True)
        )


class RenameHistory:
    """
    Rename history manager with undo capabilities
    """

    def __init__(self, storage_path: Optional[Path] = None, max_entries: int = 100):
        """
        Initialize rename history

        Args:
            storage_path: Path to JSON file for history storage
            max_entries: Maximum number of history entries to keep
        """
        if storage_path is None:
            storage_path = Path.home() / ".smart_search" / "rename_history.json"

        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        self.max_entries = max_entries
        self.history: List[HistoryEntry] = []
        self._load_history()

    def add_entry(
        self,
        operation_id: str,
        operations: List[Dict],
        pattern_used: str,
        total_files: int,
        success_count: int
    ) -> HistoryEntry:
        """
        Add new history entry

        Args:
            operation_id: Unique operation ID
            operations: List of rename operations
            pattern_used: Pattern string that was used
            total_files: Total number of files
            success_count: Number of successful renames

        Returns:
            Created history entry
        """
        entry = HistoryEntry(
            timestamp=datetime.now(),
            operation_id=operation_id,
            operations=operations,
            pattern_used=pattern_used,
            total_files=total_files,
            success_count=success_count
        )

        self.history.insert(0, entry)  # Add to beginning

        # Trim history if too long
        if len(self.history) > self.max_entries:
            self.history = self.history[:self.max_entries]

        self._save_history()
        return entry

    def get_history(self, limit: Optional[int] = None) -> List[HistoryEntry]:
        """
        Get history entries

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of history entries (newest first)
        """
        if limit:
            return self.history[:limit]
        return self.history.copy()

    def get_entry(self, operation_id: str) -> Optional[HistoryEntry]:
        """Get specific history entry by operation ID"""
        for entry in self.history:
            if entry.operation_id == operation_id:
                return entry
        return None

    def undo_operation(self, operation_id: str) -> tuple[bool, str, int]:
        """
        Undo a rename operation

        Args:
            operation_id: Operation to undo

        Returns:
            Tuple of (success, message, files_reverted)
        """
        entry = self.get_entry(operation_id)
        if not entry:
            return False, "Operation not found in history", 0

        if not entry.can_undo:
            return False, "Operation cannot be undone", 0

        # Verify files still exist and haven't been modified
        reverted = 0
        errors = []

        for op in entry.operations:
            if not op.get('success'):
                continue

            old_path = Path(op['old_path'])
            new_path = Path(op['new_path'])

            try:
                # Check if new file exists
                if not new_path.exists():
                    errors.append(f"File not found: {new_path.name}")
                    continue

                # Check if old path would cause collision
                if old_path.exists():
                    errors.append(f"Cannot restore: {old_path.name} already exists")
                    continue

                # Rename back
                new_path.rename(old_path)
                reverted += 1

            except Exception as e:
                errors.append(f"Error reverting {new_path.name}: {str(e)}")

        # Mark as undone
        entry.can_undo = False
        self._save_history()

        if reverted > 0:
            msg = f"Reverted {reverted} of {entry.success_count} files"
            if errors:
                msg += f" ({len(errors)} errors)"
            return True, msg, reverted
        else:
            return False, "No files could be reverted: " + "; ".join(errors[:3]), 0

    def can_undo(self, operation_id: str) -> bool:
        """Check if operation can be undone"""
        entry = self.get_entry(operation_id)
        return entry is not None and entry.can_undo

    def clear_history(self) -> bool:
        """Clear all history"""
        self.history.clear()
        return self._save_history()

    def export_history(self, file_path: str, limit: Optional[int] = None) -> bool:
        """
        Export history to JSON file

        Args:
            file_path: Output file path
            limit: Maximum entries to export (None = all)

        Returns:
            True if exported successfully
        """
        try:
            entries = self.get_history(limit)
            data = [entry.to_dict() for entry in entries]

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True
        except Exception:
            return False

    def get_statistics(self) -> Dict:
        """Get history statistics"""
        if not self.history:
            return {
                'total_operations': 0,
                'total_files_renamed': 0,
                'average_files_per_operation': 0,
                'success_rate': 0,
                'oldest_entry': None,
                'newest_entry': None
            }

        total_operations = len(self.history)
        total_files = sum(e.total_files for e in self.history)
        total_success = sum(e.success_count for e in self.history)

        return {
            'total_operations': total_operations,
            'total_files_renamed': total_success,
            'total_files_attempted': total_files,
            'average_files_per_operation': total_files / total_operations if total_operations > 0 else 0,
            'success_rate': (total_success / total_files * 100) if total_files > 0 else 0,
            'oldest_entry': self.history[-1].timestamp.isoformat() if self.history else None,
            'newest_entry': self.history[0].timestamp.isoformat() if self.history else None,
        }

    def search_history(
        self,
        pattern: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[HistoryEntry]:
        """
        Search history with filters

        Args:
            pattern: Search in pattern_used field
            start_date: Filter entries after this date
            end_date: Filter entries before this date

        Returns:
            Filtered history entries
        """
        results = self.history.copy()

        if pattern:
            pattern_lower = pattern.lower()
            results = [e for e in results if pattern_lower in e.pattern_used.lower()]

        if start_date:
            results = [e for e in results if e.timestamp >= start_date]

        if end_date:
            results = [e for e in results if e.timestamp <= end_date]

        return results

    def _load_history(self):
        """Load history from storage"""
        if not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.history = [HistoryEntry.from_dict(entry) for entry in data]
        except Exception:
            self.history = []

    def _save_history(self) -> bool:
        """Save history to storage"""
        try:
            data = [entry.to_dict() for entry in self.history]

            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True
        except Exception:
            return False


# Helper function to get default history instance
_default_history = None

def get_rename_history() -> RenameHistory:
    """Get default rename history instance"""
    global _default_history
    if _default_history is None:
        _default_history = RenameHistory()
    return _default_history

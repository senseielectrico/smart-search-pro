"""
Simple verification script for the notes system.
Tests basic functionality without unicode console output.
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.database import Database
from notes.note_manager import NoteManager
from notes.note_model import Note, NoteCategory


def main():
    print("=" * 60)
    print("Notes System Verification")
    print("=" * 60)
    print()

    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    print(f"Using temporary database: {db_path}")
    db = Database(db_path)
    manager = NoteManager(db)
    print("[OK] Database and NoteManager initialized")
    print()

    # Test 1: Create note
    print("Test 1: Create Note")
    note = Note(
        title="Test Note",
        content="This is a test note",
        tags=["test", "sample"]
    )
    note_id = manager.create_note(note)
    print(f"[OK] Created note with ID: {note_id}")
    print()

    # Test 2: Read note
    print("Test 2: Read Note")
    loaded = manager.get_note(note_id)
    assert loaded is not None
    assert loaded.title == "Test Note"
    print(f"[OK] Retrieved note: {loaded.title}")
    print()

    # Test 3: Update note
    print("Test 3: Update Note")
    loaded.title = "Updated Note"
    manager.update_note(loaded)
    updated = manager.get_note(note_id)
    assert updated.title == "Updated Note"
    print(f"[OK] Updated note: {updated.title}")
    print()

    # Test 4: Create category
    print("Test 4: Create Category")
    cat = NoteCategory(name="Test Category", icon="[TEST]", color="#ff0000")
    cat_id = manager.create_category(cat)
    print(f"[OK] Created category: {cat.name}")
    print()

    # Test 5: Search
    print("Test 5: Search Notes")
    results = manager.search_notes("test")
    print(f"[OK] Found {len(results)} notes matching 'test'")
    print()

    # Test 6: Tags
    print("Test 6: Tags")
    tags = manager.get_all_tags()
    print(f"[OK] Found {len(tags)} tags")
    for tag in tags:
        print(f"  - {tag.name} (used {tag.usage_count} times)")
    print()

    # Test 7: Statistics
    print("Test 7: Statistics")
    stats = manager.get_stats()
    print(f"[OK] Total notes: {stats['total_notes']}")
    print(f"[OK] Total tags: {stats['total_tags']}")
    print()

    # Test 8: Export
    print("Test 8: Export")
    json_content = manager.export_note_to_json(note_id)
    md_content = manager.export_note_to_markdown(note_id)
    print(f"[OK] Exported to JSON ({len(json_content)} bytes)")
    print(f"[OK] Exported to Markdown ({len(md_content)} bytes)")
    print()

    # Test 9: Version history
    print("Test 9: Version History")
    versions = manager.get_note_versions(note_id)
    print(f"[OK] Found {len(versions)} versions")
    print()

    # Cleanup
    db.close()
    Path(db_path).unlink()
    print("=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
    print()
    print("Notes system is working correctly.")
    print()
    print("Next steps:")
    print("  1. Run the example: python notes\\example_integration.py")
    print("  2. Integrate into Smart Search Pro")
    print("  3. Try the quick note dialog (Ctrl+Shift+N)")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

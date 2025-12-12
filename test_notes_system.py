"""
Test suite for the notes system.

Tests all components of the notes system including:
- Note CRUD operations
- Category management
- Tag management
- Version history
- Search functionality
- Import/Export
"""

import sys
import tempfile
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.database import Database
from notes.note_manager import NoteManager
from notes.note_model import Note, NoteCategory, NoteTag


def test_note_crud():
    """Test note CRUD operations."""
    print("Testing Note CRUD operations...")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db = Database(f.name)
        manager = NoteManager(db)

        # Create
        note = Note(
            title="Test Note",
            content="This is a test note",
            tags=["test", "sample"]
        )
        note_id = manager.create_note(note)
        assert note_id > 0, "Note ID should be positive"
        print(f"  ✓ Created note with ID: {note_id}")

        # Read
        loaded = manager.get_note(note_id)
        assert loaded is not None, "Note should be found"
        assert loaded.title == "Test Note", "Title should match"
        assert loaded.content == "This is a test note", "Content should match"
        assert "test" in loaded.tags, "Tags should match"
        print(f"  ✓ Retrieved note: {loaded.title}")

        # Update
        loaded.title = "Updated Note"
        loaded.content = "Updated content"
        manager.update_note(loaded)
        updated = manager.get_note(note_id)
        assert updated.title == "Updated Note", "Title should be updated"
        print(f"  ✓ Updated note: {updated.title}")

        # Delete
        manager.delete_note(note_id)
        deleted = manager.get_note(note_id)
        assert deleted is None, "Note should be deleted"
        print(f"  ✓ Deleted note")

        db.close()
        Path(f.name).unlink()

    print("✅ Note CRUD tests passed!\n")


def test_categories():
    """Test category management."""
    print("Testing Category management...")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db = Database(f.name)
        manager = NoteManager(db)

        # Create category
        cat = NoteCategory(
            name="Test Category",
            icon="🧪",
            color="#ff0000",
            description="Test description"
        )
        cat_id = manager.create_category(cat)
        assert cat_id > 0, "Category ID should be positive"
        print(f"  ✓ Created category: {cat.name}")

        # Get all categories
        categories = manager.get_all_categories()
        assert len(categories) == 1, "Should have 1 category"
        print(f"  ✓ Retrieved {len(categories)} categories")

        # Create note with category
        note = Note(
            title="Categorized Note",
            content="Content",
            category_id=cat_id
        )
        note_id = manager.create_note(note)

        # Filter by category
        notes = manager.get_all_notes(category_id=cat_id)
        assert len(notes) == 1, "Should find 1 note in category"
        print(f"  ✓ Found {len(notes)} notes in category")

        # Update category
        cat.name = "Updated Category"
        manager.update_category(cat)
        updated = manager.get_category(cat_id)
        assert updated.name == "Updated Category", "Name should be updated"
        print(f"  ✓ Updated category: {updated.name}")

        # Delete category
        manager.delete_category(cat_id)
        categories = manager.get_all_categories()
        assert len(categories) == 0, "Category should be deleted"
        print(f"  ✓ Deleted category")

        db.close()
        Path(f.name).unlink()

    print("✅ Category tests passed!\n")


def test_tags():
    """Test tag management."""
    print("Testing Tag management...")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db = Database(f.name)
        manager = NoteManager(db)

        # Create notes with tags
        note1 = Note(title="Note 1", content="Content", tags=["python", "coding"])
        note2 = Note(title="Note 2", content="Content", tags=["python", "tutorial"])
        note3 = Note(title="Note 3", content="Content", tags=["javascript"])

        manager.create_note(note1)
        manager.create_note(note2)
        manager.create_note(note3)

        # Get all tags
        tags = manager.get_all_tags()
        assert len(tags) == 3, "Should have 3 unique tags"
        print(f"  ✓ Created {len(tags)} unique tags")

        # Check usage counts
        python_tag = next(t for t in tags if t.name == "python")
        assert python_tag.usage_count == 2, "Python tag should be used 2 times"
        print(f"  ✓ Tag usage counts correct: python={python_tag.usage_count}")

        # Get notes by tag
        python_notes = manager.get_notes_by_tag("python")
        assert len(python_notes) == 2, "Should find 2 notes with python tag"
        print(f"  ✓ Found {len(python_notes)} notes with 'python' tag")

        db.close()
        Path(f.name).unlink()

    print("✅ Tag tests passed!\n")


def test_search():
    """Test full-text search."""
    print("Testing Full-text search...")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db = Database(f.name)
        manager = NoteManager(db)

        # Create notes with searchable content
        notes = [
            Note(title="Python Tutorial", content="Learn Python programming"),
            Note(title="JavaScript Guide", content="Web development with JS"),
            Note(title="Python Advanced", content="Advanced Python techniques"),
        ]

        for note in notes:
            manager.create_note(note)

        # Search for "python"
        results = manager.search_notes("python")
        assert len(results) == 2, "Should find 2 notes containing 'python'"
        print(f"  ✓ Search 'python': found {len(results)} notes")

        # Search for "javascript"
        results = manager.search_notes("javascript")
        assert len(results) == 1, "Should find 1 note containing 'javascript'"
        print(f"  ✓ Search 'javascript': found {len(results)} notes")

        # Search in title
        results = manager.search_notes("tutorial")
        assert len(results) == 1, "Should find 1 note with 'tutorial' in title"
        print(f"  ✓ Search 'tutorial': found {len(results)} notes")

        db.close()
        Path(f.name).unlink()

    print("✅ Search tests passed!\n")


def test_version_history():
    """Test version history."""
    print("Testing Version history...")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db = Database(f.name)
        manager = NoteManager(db)

        # Create note
        note = Note(title="Original Title", content="Original content")
        note_id = manager.create_note(note)

        # Update multiple times
        for i in range(5):
            note.title = f"Version {i+1}"
            note.content = f"Content {i+1}"
            manager.update_note(note)
            time.sleep(0.01)  # Small delay for version ordering

        # Get versions
        versions = manager.get_note_versions(note_id)
        assert len(versions) == 5, "Should have 5 versions"
        print(f"  ✓ Created {len(versions)} versions")

        # Check version content
        assert versions[0].version > versions[-1].version, "Versions should be in DESC order"
        print(f"  ✓ Versions ordered correctly")

        # Restore version
        manager.restore_version(note_id, versions[-1].version)
        restored = manager.get_note(note_id)
        assert restored.title == versions[-1].title, "Should restore to old version"
        print(f"  ✓ Restored to version {versions[-1].version}")

        db.close()
        Path(f.name).unlink()

    print("✅ Version history tests passed!\n")


def test_pinned_notes():
    """Test pinned notes."""
    print("Testing Pinned notes...")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db = Database(f.name)
        manager = NoteManager(db)

        # Create notes
        note1 = Note(title="Regular Note", content="Content", is_pinned=False)
        note2 = Note(title="Pinned Note", content="Content", is_pinned=True)

        manager.create_note(note1)
        manager.create_note(note2)

        # Get pinned notes
        pinned = manager.get_all_notes(pinned_only=True)
        assert len(pinned) == 1, "Should have 1 pinned note"
        assert pinned[0].title == "Pinned Note", "Should get correct pinned note"
        print(f"  ✓ Found {len(pinned)} pinned notes")

        # Get all notes (should sort pinned first)
        all_notes = manager.get_all_notes()
        assert all_notes[0].is_pinned, "First note should be pinned"
        print(f"  ✓ Pinned notes sorted first")

        db.close()
        Path(f.name).unlink()

    print("✅ Pinned notes tests passed!\n")


def test_export_import():
    """Test export and import."""
    print("Testing Export/Import...")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db = Database(f.name)
        manager = NoteManager(db)

        # Create note
        note = Note(
            title="Test Export",
            content="Export content",
            tags=["export", "test"]
        )
        note_id = manager.create_note(note)

        # Export to JSON
        json_content = manager.export_note_to_json(note_id)
        assert "Test Export" in json_content, "JSON should contain title"
        print(f"  ✓ Exported to JSON")

        # Export to Markdown
        md_content = manager.export_note_to_markdown(note_id)
        assert "# Test Export" in md_content, "Markdown should have title as header"
        assert "export" in md_content, "Markdown should contain tags"
        print(f"  ✓ Exported to Markdown")

        # Import from JSON
        imported_id = manager.import_note_from_json(json_content)
        imported = manager.get_note(imported_id)
        assert imported.title == "Test Export", "Imported note should have same title"
        print(f"  ✓ Imported from JSON")

        db.close()
        Path(f.name).unlink()

    print("✅ Export/Import tests passed!\n")


def test_statistics():
    """Test statistics."""
    print("Testing Statistics...")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db = Database(f.name)
        manager = NoteManager(db)

        # Create category
        cat = NoteCategory(name="Test Cat", icon="🧪")
        cat_id = manager.create_category(cat)

        # Create notes
        for i in range(5):
            note = Note(
                title=f"Note {i}",
                content="Content",
                tags=["test", f"tag{i}"],
                category_id=cat_id,
                is_pinned=(i == 0)
            )
            manager.create_note(note)

        # Get stats
        stats = manager.get_stats()
        assert stats['total_notes'] == 5, "Should have 5 notes"
        assert stats['pinned_notes'] == 1, "Should have 1 pinned note"
        assert stats['total_tags'] == 6, "Should have 6 unique tags"
        assert stats['by_category']['Test Cat'] == 5, "Should have 5 notes in category"
        print(f"  ✓ Statistics correct:")
        print(f"    - Total notes: {stats['total_notes']}")
        print(f"    - Pinned: {stats['pinned_notes']}")
        print(f"    - Tags: {stats['total_tags']}")
        print(f"    - Top tag: {stats['top_tags'][0][0]} ({stats['top_tags'][0][1]})")

        db.close()
        Path(f.name).unlink()

    print("✅ Statistics tests passed!\n")


def test_linked_paths():
    """Test linked paths."""
    print("Testing Linked paths...")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db = Database(f.name)
        manager = NoteManager(db)

        # Create notes with linked paths
        note1 = Note(title="Note 1", content="Content", linked_path="/path/to/file1")
        note2 = Note(title="Note 2", content="Content", linked_path="/path/to/file1")
        note3 = Note(title="Note 3", content="Content", linked_path="/path/to/file2")

        manager.create_note(note1)
        manager.create_note(note2)
        manager.create_note(note3)

        # Get notes by path
        notes = manager.get_notes_by_linked_path("/path/to/file1")
        assert len(notes) == 2, "Should find 2 notes linked to file1"
        print(f"  ✓ Found {len(notes)} notes linked to /path/to/file1")

        notes = manager.get_notes_by_linked_path("/path/to/file2")
        assert len(notes) == 1, "Should find 1 note linked to file2"
        print(f"  ✓ Found {len(notes)} notes linked to /path/to/file2")

        db.close()
        Path(f.name).unlink()

    print("✅ Linked paths tests passed!\n")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Notes System Test Suite")
    print("=" * 60)
    print()

    tests = [
        test_note_crud,
        test_categories,
        test_tags,
        test_search,
        test_version_history,
        test_pinned_notes,
        test_export_import,
        test_statistics,
        test_linked_paths,
    ]

    failed = []
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ {test.__name__} FAILED: {e}\n")
            failed.append(test.__name__)

    print("=" * 60)
    if not failed:
        print("✅ ALL TESTS PASSED!")
    else:
        print(f"❌ {len(failed)} TESTS FAILED:")
        for name in failed:
            print(f"  - {name}")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()

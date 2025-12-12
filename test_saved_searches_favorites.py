"""
Test suite for saved searches and favorites system.

Tests all components including:
- Saved searches manager
- Favorites manager
- Smart collections manager
- UI components integration
"""

import os
import sys
import tempfile
from pathlib import Path

# Add search module to path
sys.path.insert(0, str(Path(__file__).parent / 'search'))
sys.path.insert(0, str(Path(__file__).parent / 'ui'))

from search.saved_searches import SavedSearch, SavedSearchManager
from search.favorites_manager import Favorite, FavoritesManager
from search.smart_collections import (
    SmartCollection, SmartCollectionsManager,
    Condition, ConditionType, LogicOperator
)


def test_saved_searches():
    """Test saved searches functionality."""
    print("\n=== Testing Saved Searches ===")

    # Create temp database
    import time
    import random
    db_path = os.path.join(
        tempfile.gettempdir(),
        f'test_searches_{time.time()}_{random.randint(1000, 9999)}.db'
    )

    try:
        manager = SavedSearchManager(db_path)

        # Test 1: Create and save a search
        print("\n1. Creating saved search...")
        search = SavedSearch(
            name="Test Search",
            description="Search for Python files",
            query="*.py",
            category="Development",
            file_types=['.py', '.pyw'],
            sort_order="modified",
            ascending=False,
            shortcut_key=1
        )

        search_id = manager.save(search)
        print(f"   Created search with ID: {search_id}")

        # Test 2: Retrieve search
        print("\n2. Retrieving search...")
        retrieved = manager.get(search_id)
        assert retrieved.name == "Test Search"
        assert retrieved.shortcut_key == 1
        print(f"   Retrieved: {retrieved.name}")

        # Test 3: Get by shortcut
        print("\n3. Getting by shortcut (Ctrl+1)...")
        by_shortcut = manager.get_by_shortcut(1)
        assert by_shortcut.name == "Test Search"
        print(f"   Found: {by_shortcut.name}")

        # Test 4: Get all searches
        print("\n4. Getting all searches...")
        all_searches = manager.get_all()
        print(f"   Total searches: {len(all_searches)}")

        # Test 5: Search within saved searches
        print("\n5. Searching for 'Python'...")
        results = manager.search("Python")
        print(f"   Found {len(results)} matches")

        # Test 6: Update search
        print("\n6. Updating search...")
        retrieved.description = "Updated description"
        manager.save(retrieved)
        updated = manager.get(search_id)
        assert updated.description == "Updated description"
        print("   Updated successfully")

        # Test 7: Duplicate search
        print("\n7. Duplicating search...")
        new_id = manager.duplicate(search_id, "Test Search (Copy)")
        duplicate = manager.get(new_id)
        assert duplicate.name == "Test Search (Copy)"
        assert duplicate.shortcut_key is None
        print(f"   Created duplicate with ID: {new_id}")

        # Test 8: Update run stats
        print("\n8. Updating run statistics...")
        manager.update_run_stats(search_id, 42)
        updated = manager.get(search_id)
        assert updated.run_count == 1
        assert updated.last_result_count == 42
        print(f"   Run count: {updated.run_count}, Results: {updated.last_result_count}")

        # Test 9: Get statistics
        print("\n9. Getting statistics...")
        stats = manager.get_statistics()
        print(f"   Total searches: {stats['total_searches']}")
        print(f"   Categories: {stats['categories']}")
        print(f"   With shortcuts: {stats['with_shortcuts']}")

        # Test 10: Export/Import
        print("\n10. Testing export/import...")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = f.name

        manager.export_to_json(export_path)
        print(f"   Exported to: {export_path}")

        # Create new manager and import
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path2 = f.name

        manager2 = SavedSearchManager(db_path2)
        imported = manager2.import_from_json(export_path, merge=False)
        print(f"   Imported {imported} searches")

        os.unlink(export_path)
        os.unlink(db_path2)

        # Test 11: Delete search
        print("\n11. Deleting search...")
        manager.delete(new_id)
        deleted = manager.get(new_id)
        assert deleted is None
        print("   Deleted successfully")

        print("\nOK: All saved searches tests passed!")

    finally:
        # Close any connections
        import gc
        gc.collect()
        import time
        time.sleep(0.1)

        try:
            if os.path.exists(db_path):
                os.unlink(db_path)
        except Exception:
            pass


def test_favorites():
    """Test favorites functionality."""
    print("\n=== Testing Favorites ===")

    # Create temp database
    import time
    import random
    db_path = os.path.join(
        tempfile.gettempdir(),
        f'test_favorites_{time.time()}_{random.randint(1000, 9999)}.db'
    )

    try:
        manager = FavoritesManager(db_path)

        # Test 1: Add favorite
        print("\n1. Adding favorite...")
        test_file = __file__
        fav_id = manager.add(
            test_file,
            rating=5,
            tags=['test', 'python'],
            category='Development',
            notes='Test file'
        )
        print(f"   Added favorite with ID: {fav_id}")

        # Test 2: Check if favorite
        print("\n2. Checking if favorited...")
        is_fav = manager.is_favorite(test_file)
        assert is_fav
        print("   File is favorited")

        # Test 3: Get favorite
        print("\n3. Retrieving favorite...")
        favorite = manager.get(fav_id)
        assert favorite.rating == 5
        assert 'python' in favorite.tags
        print(f"   Retrieved: {favorite.name} (Rating: {favorite.rating})")

        # Test 4: Get by path
        print("\n4. Getting by path...")
        by_path = manager.get_by_path(test_file)
        assert by_path.id == fav_id
        print(f"   Found: {by_path.name}")

        # Test 5: Update rating
        print("\n5. Updating rating...")
        manager.update_rating(fav_id, 4)
        updated = manager.get(fav_id)
        assert updated.rating == 4
        print(f"   New rating: {updated.rating}")

        # Test 6: Add/remove tags
        print("\n6. Managing tags...")
        manager.add_tag(fav_id, 'important')
        manager.remove_tag(fav_id, 'test')
        updated = manager.get(fav_id)
        assert 'important' in updated.tags
        assert 'test' not in updated.tags
        print(f"   Tags: {updated.tags}")

        # Test 7: Get all favorites
        print("\n7. Getting all favorites...")
        all_favs = manager.get_all(min_rating=3)
        print(f"   Found {len(all_favs)} favorites with rating >= 3")

        # Test 8: Search favorites
        print("\n8. Searching favorites...")
        results = manager.search('test')
        print(f"   Found {len(results)} matches")

        # Test 9: Get categories and tags
        print("\n9. Getting categories and tags...")
        categories = manager.get_categories()
        tags = manager.get_all_tags()
        print(f"   Categories: {categories}")
        print(f"   Tags: {tags}")

        # Test 10: Update access
        print("\n10. Updating access stats...")
        manager.update_access(fav_id)
        updated = manager.get(fav_id)
        assert updated.access_count == 1
        print(f"   Access count: {updated.access_count}")

        # Test 11: Get recent and top-rated
        print("\n11. Getting recent and top-rated...")
        recent = manager.get_recent(limit=5)
        top_rated = manager.get_top_rated(limit=5, min_rating=4)
        print(f"   Recent: {len(recent)}, Top-rated: {len(top_rated)}")

        # Test 12: Statistics
        print("\n12. Getting statistics...")
        stats = manager.get_statistics()
        print(f"   Total favorites: {stats['total_favorites']}")
        print(f"   Average rating: {stats['average_rating']}")
        print(f"   Total tags: {stats['total_tags']}")

        # Test 13: Delete favorite
        print("\n13. Deleting favorite...")
        manager.delete(fav_id)
        deleted = manager.get(fav_id)
        assert deleted is None
        print("   Deleted successfully")

        print("\nOK: All favorites tests passed!")

    finally:
        # Close any connections
        import gc
        gc.collect()
        import time
        time.sleep(0.1)

        try:
            if os.path.exists(db_path):
                os.unlink(db_path)
        except Exception:
            pass


def test_smart_collections():
    """Test smart collections functionality."""
    print("\n=== Testing Smart Collections ===")

    # Create temp database
    import time
    import random
    db_path = os.path.join(
        tempfile.gettempdir(),
        f'test_collections_{time.time()}_{random.randint(1000, 9999)}.db'
    )

    try:
        manager = SmartCollectionsManager(db_path)

        # Test 1: Default collections created
        print("\n1. Checking default collections...")
        all_collections = manager.get_all()
        print(f"   Found {len(all_collections)} default collections")
        for coll in all_collections:
            print(f"   - {coll.name}")

        # Test 2: Create custom collection
        print("\n2. Creating custom collection...")
        collection = SmartCollection(
            name="Large Python Files",
            description="Python files larger than 10MB",
            conditions=[
                Condition(ConditionType.EXTENSION_IS, 'py'),
                Condition(ConditionType.SIZE_GREATER, 10 * 1024 * 1024)
            ],
            match_all=True
        )

        coll_id = manager.save(collection)
        print(f"   Created collection with ID: {coll_id}")

        # Test 3: Retrieve collection
        print("\n3. Retrieving collection...")
        retrieved = manager.get(coll_id)
        assert retrieved.name == "Large Python Files"
        assert len(retrieved.conditions) == 2
        print(f"   Retrieved: {retrieved.name}")

        # Test 4: Get by name
        print("\n4. Getting by name...")
        by_name = manager.get_by_name("Large Python Files")
        assert by_name.id == coll_id
        print(f"   Found: {by_name.name}")

        # Test 5: Test condition evaluation
        print("\n5. Testing condition evaluation...")

        # Create test file info
        test_file = {
            'path': '/test/example.py',
            'size': 15 * 1024 * 1024,  # 15 MB
            'modified': '2024-01-01T00:00:00'
        }

        matches = collection.matches(test_file)
        assert matches
        print(f"   File matches: {matches}")

        # Test non-matching file
        test_file2 = {
            'path': '/test/small.py',
            'size': 1024,  # 1 KB
            'modified': '2024-01-01T00:00:00'
        }

        matches2 = collection.matches(test_file2)
        assert not matches2
        print(f"   Small file matches: {matches2}")

        # Test 6: Evaluate collection
        print("\n6. Evaluating collection against file list...")
        files = [test_file, test_file2]
        results = manager.evaluate(coll_id, files)
        assert len(results) == 1
        print(f"   Matched {len(results)} files")

        # Test 7: Update result count
        print("\n7. Checking updated result count...")
        updated = manager.get(coll_id)
        assert updated.result_count == 1
        print(f"   Result count: {updated.result_count}")

        # Test 8: Test OR logic
        print("\n8. Testing OR logic...")
        or_collection = SmartCollection(
            name="Documents or Images",
            conditions=[
                Condition(ConditionType.EXTENSION_IN, ['doc', 'docx', 'pdf']),
                Condition(ConditionType.EXTENSION_IN, ['jpg', 'png', 'gif'], LogicOperator.OR)
            ],
            match_all=False  # OR logic
        )

        test_doc = {'path': '/test/file.pdf', 'size': 1000}
        test_img = {'path': '/test/image.jpg', 'size': 1000}
        test_other = {'path': '/test/file.txt', 'size': 1000}

        assert or_collection.matches(test_doc)
        assert or_collection.matches(test_img)
        assert not or_collection.matches(test_other)
        print("   OR logic works correctly")

        # Test 9: Delete collection
        print("\n9. Deleting collection...")
        manager.delete(coll_id)
        deleted = manager.get(coll_id)
        assert deleted is None
        print("   Deleted successfully")

        print("\nOK: All smart collections tests passed!")

    finally:
        # Close any connections
        import gc
        gc.collect()
        import time
        time.sleep(0.1)

        try:
            if os.path.exists(db_path):
                os.unlink(db_path)
        except Exception:
            pass


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Saved Searches & Favorites System - Test Suite")
    print("=" * 60)

    try:
        test_saved_searches()
        test_favorites()
        test_smart_collections()

        print("\n" + "=" * 60)
        print("SUCCESS: ALL TESTS PASSED!")
        print("=" * 60)
        return True

    except AssertionError as e:
        print(f"\nFAILED: TEST ASSERTION: {e}")
        import traceback
        traceback.print_exc()
        return False

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

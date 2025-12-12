"""Quick test to verify all imports work correctly."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    # Test imports
    from core.exceptions import SmartSearchError
    from core.logger import get_logger, setup_logging
    from core.config import Config
    from core.cache import LRUCache
    from core.eventbus import EventBus, Event
    from core.database import Database

    print("SUCCESS: All modules imported successfully")

    # Test basic functionality
    config = Config()
    config.validate()
    print("SUCCESS: Config validation passed")

    cache = LRUCache(max_size=10)
    cache.set("test", "value")
    assert cache.get("test") == "value"
    print("SUCCESS: Cache operations work")

    bus = EventBus()
    received = []
    bus.subscribe("test", lambda e: received.append(e.data))
    bus.publish("test", {"key": "value"})
    assert len(received) == 1
    print("SUCCESS: Event bus works")

    print("\n" + "="*50)
    print("ALL CORE COMPONENTS FUNCTIONAL!")
    print("="*50)

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

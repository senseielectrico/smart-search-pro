"""
Window state persistence for Smart Search Pro.

Manages saving and restoring window positions, sizes, and search states
across application sessions.
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .exceptions import ConfigLoadError
from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class WindowGeometry:
    """Window geometry information."""

    x: int = 100
    y: int = 100
    width: int = 1200
    height: int = 700
    is_maximized: bool = False
    is_minimized: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WindowGeometry':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class SearchState:
    """Search state for a window."""

    query: str = ""
    directory_paths: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    sort_by: str = "name"
    sort_ascending: bool = True
    selected_tab: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchState':
        """Create from dictionary."""
        return cls(
            query=data.get('query', ''),
            directory_paths=data.get('directory_paths', []),
            filters=data.get('filters', {}),
            sort_by=data.get('sort_by', 'name'),
            sort_ascending=data.get('sort_ascending', True),
            selected_tab=data.get('selected_tab', 0)
        )


@dataclass
class WindowState:
    """Complete window state."""

    window_id: str
    geometry: WindowGeometry = field(default_factory=WindowGeometry)
    search_state: SearchState = field(default_factory=SearchState)
    is_primary: bool = False
    created_at: float = 0.0
    last_active: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'window_id': self.window_id,
            'geometry': self.geometry.to_dict(),
            'search_state': self.search_state.to_dict(),
            'is_primary': self.is_primary,
            'created_at': self.created_at,
            'last_active': self.last_active
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WindowState':
        """Create from dictionary."""
        return cls(
            window_id=data.get('window_id', ''),
            geometry=WindowGeometry.from_dict(data.get('geometry', {})),
            search_state=SearchState.from_dict(data.get('search_state', {})),
            is_primary=data.get('is_primary', False),
            created_at=data.get('created_at', 0.0),
            last_active=data.get('last_active', 0.0)
        )


@dataclass
class ApplicationState:
    """Complete application state with all windows."""

    windows: List[WindowState] = field(default_factory=list)
    active_window_id: Optional[str] = None
    window_layout: str = "cascade"  # cascade, tile_horizontal, tile_vertical
    version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'windows': [w.to_dict() for w in self.windows],
            'active_window_id': self.active_window_id,
            'window_layout': self.window_layout,
            'version': self.version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApplicationState':
        """Create from dictionary."""
        return cls(
            windows=[WindowState.from_dict(w) for w in data.get('windows', [])],
            active_window_id=data.get('active_window_id'),
            window_layout=data.get('window_layout', 'cascade'),
            version=data.get('version', '1.0.0')
        )


class WindowStateManager:
    """
    Manages window state persistence.

    Handles saving and restoring window positions, sizes, and search states.
    Thread-safe for multi-window scenarios.
    """

    def __init__(self, state_file: Optional[Path] = None):
        """
        Initialize window state manager.

        Args:
            state_file: Path to state file (defaults to data/window_state.json)
        """
        if state_file is None:
            from .config import get_config
            config = get_config()
            state_file = config.get_data_dir() / "window_state.json"

        self.state_file = Path(state_file)
        self._state = ApplicationState()
        self._load_state()

    def _load_state(self) -> None:
        """Load state from file."""
        if not self.state_file.exists():
            logger.info("No window state file found, using defaults")
            return

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self._state = ApplicationState.from_dict(data)
            logger.info(
                "Window state loaded",
                windows=len(self._state.windows),
                file=str(self.state_file)
            )

        except Exception as e:
            logger.warning(
                "Failed to load window state",
                error=str(e),
                file=str(self.state_file)
            )
            self._state = ApplicationState()

    def save_state(self) -> None:
        """Save current state to file."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(
                    self._state.to_dict(),
                    f,
                    indent=2,
                    ensure_ascii=False
                )

            logger.debug(
                "Window state saved",
                windows=len(self._state.windows),
                file=str(self.state_file)
            )

        except Exception as e:
            logger.error(
                "Failed to save window state",
                error=str(e),
                file=str(self.state_file)
            )

    def add_window(self, window_state: WindowState) -> None:
        """
        Add or update window state.

        Args:
            window_state: Window state to add/update
        """
        # Remove existing state with same ID
        self._state.windows = [
            w for w in self._state.windows
            if w.window_id != window_state.window_id
        ]

        # Add new state
        self._state.windows.append(window_state)

        logger.debug(
            "Window state added",
            window_id=window_state.window_id,
            total_windows=len(self._state.windows)
        )

    def remove_window(self, window_id: str) -> None:
        """
        Remove window state.

        Args:
            window_id: Window ID to remove
        """
        initial_count = len(self._state.windows)
        self._state.windows = [
            w for w in self._state.windows
            if w.window_id != window_id
        ]

        if len(self._state.windows) < initial_count:
            logger.debug(
                "Window state removed",
                window_id=window_id,
                remaining_windows=len(self._state.windows)
            )

        # Clear active window if it was removed
        if self._state.active_window_id == window_id:
            self._state.active_window_id = None
            if self._state.windows:
                self._state.active_window_id = self._state.windows[0].window_id

    def get_window_state(self, window_id: str) -> Optional[WindowState]:
        """
        Get window state by ID.

        Args:
            window_id: Window ID

        Returns:
            Window state or None if not found
        """
        for window in self._state.windows:
            if window.window_id == window_id:
                return window
        return None

    def get_all_windows(self) -> List[WindowState]:
        """
        Get all window states.

        Returns:
            List of window states
        """
        return self._state.windows.copy()

    def set_active_window(self, window_id: str) -> None:
        """
        Set active window.

        Args:
            window_id: Window ID to set as active
        """
        if any(w.window_id == window_id for w in self._state.windows):
            self._state.active_window_id = window_id
            logger.debug("Active window changed", window_id=window_id)

    def get_active_window_id(self) -> Optional[str]:
        """
        Get active window ID.

        Returns:
            Active window ID or None
        """
        return self._state.active_window_id

    def set_layout(self, layout: str) -> None:
        """
        Set window layout mode.

        Args:
            layout: Layout mode (cascade, tile_horizontal, tile_vertical)
        """
        if layout in ['cascade', 'tile_horizontal', 'tile_vertical']:
            self._state.window_layout = layout
            logger.debug("Window layout changed", layout=layout)

    def get_layout(self) -> str:
        """
        Get current window layout.

        Returns:
            Current layout mode
        """
        return self._state.window_layout

    def clear_all(self) -> None:
        """Clear all window states."""
        self._state = ApplicationState()
        logger.info("All window states cleared")

    def get_next_window_position(self, index: int) -> tuple[int, int]:
        """
        Get position for next window based on layout.

        Args:
            index: Window index

        Returns:
            Tuple of (x, y) position
        """
        base_x = 100
        base_y = 100
        offset = 40

        if self._state.window_layout == 'cascade':
            return (base_x + index * offset, base_y + index * offset)
        elif self._state.window_layout == 'tile_horizontal':
            # Side by side
            screen_width = 1920  # Default, should get from screen
            window_width = 1200
            return (base_x + (index % 2) * (window_width + 20), base_y)
        elif self._state.window_layout == 'tile_vertical':
            # Stacked
            screen_height = 1080  # Default, should get from screen
            window_height = 700
            return (base_x, base_y + (index % 2) * (window_height + 50))

        return (base_x, base_y)


# Global instance
_state_manager: Optional[WindowStateManager] = None


def get_window_state_manager() -> WindowStateManager:
    """
    Get global window state manager instance.

    Returns:
        WindowStateManager instance
    """
    global _state_manager
    if _state_manager is None:
        _state_manager = WindowStateManager()
    return _state_manager

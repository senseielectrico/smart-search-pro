"""
Filter Integration Examples

Complete code examples for integrating advanced filters into your application.
"""

from typing import Dict, List
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSlot

# Example 1: Basic Integration
# ============================================================

class BasicSearchWindow(QMainWindow):
    """
    Basic example showing minimal filter integration.
    """

    def __init__(self):
        super().__init__()
        from ui.search_panel import SearchPanel

        # Create search panel
        self.search_panel = SearchPanel()

        # Connect signals
        self.search_panel.search_requested.connect(self.on_search_requested)
        self.search_panel.filter_changed.connect(self.on_filter_changed)

        # Add to UI
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self.search_panel)
        self.setCentralWidget(central)

    @pyqtSlot(dict)
    def on_search_requested(self, params: Dict):
        """Handle search request"""
        query = params['query']  # Full query with filters
        print(f"Searching for: {query}")

        # Execute your search here
        # results = your_search_function(query)

    @pyqtSlot(dict)
    def on_filter_changed(self, filters: Dict):
        """Handle filter change"""
        print(f"Filters changed: {filters}")

        # Optional: Update UI, save preferences, etc.


# Example 2: Advanced Integration with Backend
# ============================================================

class AdvancedSearchWindow(QMainWindow):
    """
    Advanced example with full backend integration.
    """

    def __init__(self):
        super().__init__()
        from ui.search_panel import SearchPanel
        from ui.filter_integration import FilterIntegration
        from search.query_parser import QueryParser
        from search.filters import create_filter_chain_from_query

        self.search_panel = SearchPanel()
        self.query_parser = QueryParser()

        # Connect signals
        self.search_panel.search_requested.connect(self.on_search_requested)
        self.search_panel.instant_search_requested.connect(self.on_instant_search)

        # Setup UI
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self.search_panel)
        self.setCentralWidget(central)

    @pyqtSlot(dict)
    def on_search_requested(self, params: Dict):
        """Handle full search with filters"""
        query_string = params['query']
        filters = params['filters']

        # Parse query
        parsed_query = self.query_parser.parse(query_string)

        # Create filter chain
        from search.filters import create_filter_chain_from_query
        filter_chain = create_filter_chain_from_query(parsed_query)

        # Execute search (your backend here)
        raw_results = self.execute_backend_search(parsed_query)

        # Apply filters
        filtered_results = [
            result for result in raw_results
            if filter_chain.matches(result)
        ]

        # Display results
        self.display_results(filtered_results)

        # Mark search as complete
        self.search_panel.set_search_complete()

    @pyqtSlot(dict)
    def on_instant_search(self, params: Dict):
        """Handle instant search (as-you-type)"""
        query_string = params['query']

        # Parse query
        parsed_query = self.query_parser.parse(query_string)

        # Execute lightweight search (top N results)
        results = self.execute_instant_search(parsed_query, limit=100)

        # Display quick results
        self.display_quick_results(results)

    def execute_backend_search(self, parsed_query):
        """Execute search with your backend"""
        # Placeholder - implement your search here
        # Example with Everything SDK:
        # everything_query = self.query_parser.build_everything_query(parsed_query)
        # results = everything_search(everything_query)
        return []

    def execute_instant_search(self, parsed_query, limit=100):
        """Execute fast instant search"""
        # Placeholder - implement instant search
        return []

    def display_results(self, results: List):
        """Display full search results"""
        # Placeholder - implement results display
        pass

    def display_quick_results(self, results: List):
        """Display instant search results"""
        # Placeholder - implement quick results display
        pass


# Example 3: Programmatic Filter Control
# ============================================================

def programmatic_filter_example():
    """
    Example of controlling filters programmatically.
    """
    from ui.search_panel import SearchPanel
    from ui.filter_integration import FilterIntegration

    panel = SearchPanel()

    # Set search text
    panel.set_search_text("invoice")

    # Programmatically activate filters
    # Note: This would need additional methods in SearchPanel
    # For now, filters are activated via UI interaction

    # Get current filters
    active_filters = panel.get_active_filters()
    print(f"Active filters: {active_filters}")

    # Convert to query
    query = FilterIntegration.ui_filters_to_query("test", active_filters)
    print(f"Query: {query}")

    # Validate filters
    is_valid, error = FilterIntegration.validate_filters(active_filters)
    if is_valid:
        print("Filters are valid")
    else:
        print(f"Filter error: {error}")


# Example 4: Filter State Persistence
# ============================================================

class PersistentFiltersWindow(QMainWindow):
    """
    Example showing how to save and restore filter state.
    """

    def __init__(self):
        super().__init__()
        from ui.search_panel import SearchPanel
        from PyQt6.QtCore import QSettings

        self.settings = QSettings("SmartSearch", "Filters")
        self.search_panel = SearchPanel()

        # Connect signals
        self.search_panel.filter_changed.connect(self.on_filter_changed)

        # Load saved filters
        self.load_filters()

        # Setup UI
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self.search_panel)
        self.setCentralWidget(central)

    @pyqtSlot(dict)
    def on_filter_changed(self, filters: Dict):
        """Save filters when they change"""
        self.save_filters(filters)

    def save_filters(self, filters: Dict):
        """Save filter state to settings"""
        import json
        self.settings.setValue("last_filters", json.dumps(filters))

    def load_filters(self):
        """Load filter state from settings"""
        import json
        filter_json = self.settings.value("last_filters", "{}")
        try:
            filters = json.loads(filter_json)
            # Apply filters to panel
            # Note: Would need method to restore filter state
            print(f"Loaded filters: {filters}")
        except json.JSONDecodeError:
            print("No saved filters found")


# Example 5: Custom Filter Validation
# ============================================================

class ValidatedSearchWindow(QMainWindow):
    """
    Example with custom filter validation and error handling.
    """

    def __init__(self):
        super().__init__()
        from ui.search_panel import SearchPanel
        from ui.filter_integration import FilterIntegration
        from PyQt6.QtWidgets import QMessageBox

        self.search_panel = SearchPanel()
        self.search_panel.search_requested.connect(self.on_search_with_validation)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self.search_panel)
        self.setCentralWidget(central)

    @pyqtSlot(dict)
    def on_search_with_validation(self, params: Dict):
        """Search with comprehensive validation"""
        from ui.filter_integration import FilterIntegration
        from PyQt6.QtWidgets import QMessageBox

        query = params['query']
        filters = params['filters']

        # Validate filters
        is_valid, error = FilterIntegration.validate_filters(filters)
        if not is_valid:
            QMessageBox.warning(
                self,
                "Invalid Filters",
                f"Filter validation failed: {error}\n\nPlease adjust your filters.",
                QMessageBox.StandardButton.Ok
            )
            return

        # Custom validation
        if not query and not filters:
            QMessageBox.information(
                self,
                "No Search Criteria",
                "Please enter a search query or select filters.",
                QMessageBox.StandardButton.Ok
            )
            return

        # Execute search
        print(f"Valid search: {query}")
        # ... rest of search logic


# Example 6: Filter Analytics
# ============================================================

class AnalyticsSearchWindow(QMainWindow):
    """
    Example tracking filter usage for analytics.
    """

    def __init__(self):
        super().__init__()
        from ui.search_panel import SearchPanel
        from collections import defaultdict

        self.search_panel = SearchPanel()
        self.filter_stats = defaultdict(int)

        # Connect signals
        self.search_panel.filter_changed.connect(self.track_filter_usage)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self.search_panel)
        self.setCentralWidget(central)

    @pyqtSlot(dict)
    def track_filter_usage(self, filters: Dict):
        """Track which filters are used"""
        for key, value in filters.items():
            self.filter_stats[key] += 1

        print(f"Filter usage stats: {dict(self.filter_stats)}")

    def get_popular_filters(self, top_n: int = 5) -> List:
        """Get most used filters"""
        sorted_filters = sorted(
            self.filter_stats.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_filters[:top_n]


# Example 7: Multi-Query Search with Filters
# ============================================================

def multi_query_example():
    """
    Example of searching with multiple queries and same filters.
    """
    from ui.filter_integration import FilterIntegration

    # Common filters
    filters = {
        'size': '>1mb',
        'type': 'document',
        'modified': 'thisweek'
    }

    # Multiple queries
    queries = ['invoice', 'receipt', 'statement']

    for query in queries:
        full_query = FilterIntegration.ui_filters_to_query(query, filters)
        print(f"Query for '{query}': {full_query}")

        # Execute search with full_query
        # results = search(full_query)


# Example 8: Filter Presets
# ============================================================

class FilterPresetsWindow(QMainWindow):
    """
    Example with predefined filter presets.
    """

    PRESETS = {
        'large_documents': {
            'size': '>10mb',
            'type': 'document'
        },
        'recent_images': {
            'modified': 'thisweek',
            'type': 'image'
        },
        'old_videos': {
            'size': '>100mb',
            'type': 'video',
            'modified': '<2023-01-01'
        }
    }

    def __init__(self):
        super().__init__()
        from ui.search_panel import SearchPanel
        from PyQt6.QtWidgets import QPushButton, QHBoxLayout

        self.search_panel = SearchPanel()

        # Preset buttons
        preset_layout = QHBoxLayout()
        for name, filters in self.PRESETS.items():
            btn = QPushButton(name.replace('_', ' ').title())
            btn.clicked.connect(lambda checked, f=filters: self.apply_preset(f))
            preset_layout.addWidget(btn)

        # Main layout
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addLayout(preset_layout)
        layout.addWidget(self.search_panel)
        self.setCentralWidget(central)

    def apply_preset(self, preset_filters: Dict):
        """Apply preset filters"""
        # Note: Would need method to programmatically set filters
        print(f"Applying preset: {preset_filters}")
        # For now, show what would be applied
        from ui.filter_integration import FilterIntegration
        summary = FilterIntegration.get_filter_summary(preset_filters)
        print(f"Preset summary: {summary}")


# Example 9: Dynamic Filter Options
# ============================================================

class DynamicFiltersWindow(QMainWindow):
    """
    Example with dynamically updated filter options.
    """

    def __init__(self):
        super().__init__()
        from ui.search_panel import SearchPanel

        self.search_panel = SearchPanel()
        self.search_panel.filter_changed.connect(self.update_filter_suggestions)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self.search_panel)
        self.setCentralWidget(central)

    @pyqtSlot(dict)
    def update_filter_suggestions(self, filters: Dict):
        """Update filter suggestions based on current filters"""
        suggestions = []

        # Suggest complementary filters
        if 'type' in filters:
            file_type = filters['type']
            if file_type == 'video':
                suggestions.append('Consider adding size filter for large videos')
            elif file_type == 'image':
                suggestions.append('Try recent date filter for latest photos')

        if 'size' in filters and filters['size'].startswith('>'):
            suggestions.append('Consider adding date filter to narrow results')

        print(f"Filter suggestions: {suggestions}")


# Example 10: Export Filter Configuration
# ============================================================

def export_filter_config(filters: Dict, filename: str):
    """
    Export filter configuration to file.
    """
    import json

    config = {
        'filters': filters,
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        'version': '1.0'
    }

    with open(filename, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"Filters exported to {filename}")


def import_filter_config(filename: str) -> Dict:
    """
    Import filter configuration from file.
    """
    import json

    with open(filename, 'r') as f:
        config = json.load(f)

    filters = config.get('filters', {})
    print(f"Filters imported: {filters}")

    return filters


# Main demonstration
if __name__ == "__main__":
    print("Filter Integration Examples")
    print("-" * 50)

    # Run simple examples
    print("\n1. Programmatic Filter Example:")
    # programmatic_filter_example()  # Uncomment to run

    print("\n2. Multi-Query Example:")
    multi_query_example()

    print("\n3. Export/Import Example:")
    test_filters = {
        'size': '>1mb',
        'type': 'document',
        'modified': 'thisweek'
    }
    # export_filter_config(test_filters, 'test_filters.json')  # Uncomment to run
    # imported = import_filter_config('test_filters.json')  # Uncomment to run

    print("\nSee class examples above for full GUI integration")
    print("Run with: python -m ui.FILTER_INTEGRATION_EXAMPLES")

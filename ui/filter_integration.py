"""
Filter Integration - Bridge between UI filters and search backend

Converts UI filter states to query parser format and vice versa.
"""

from typing import Dict, List, Optional
from datetime import datetime


class FilterIntegration:
    """
    Integration layer between UI filters and backend query parser.

    Converts UI filter dictionary to query string format compatible
    with QueryParser and Everything search backend.
    """

    @staticmethod
    def ui_filters_to_query(base_query: str, filters: Dict) -> str:
        """
        Convert UI filters to query string format.

        Args:
            base_query: Base search query text
            filters: Dictionary of active filters from UI

        Returns:
            Complete query string with filters applied

        Example:
            >>> filters = {'size': '>1mb', 'type': 'document', 'modified': 'today'}
            >>> FilterIntegration.ui_filters_to_query('invoice', filters)
            'invoice size:>1mb type:document modified:today'
        """
        query_parts = [base_query] if base_query else []

        # Size filter
        if 'size' in filters:
            size_value = filters['size']
            query_parts.append(f"size:{size_value}")

        # Date filters (modified, created, accessed)
        for date_field in ['modified', 'created', 'accessed']:
            if date_field in filters:
                date_value = filters[date_field]
                query_parts.append(f"{date_field}:{date_value}")

        # Type filter
        if 'type' in filters:
            type_value = filters['type']
            query_parts.append(f"type:{type_value}")

        # Extensions filter
        if 'extensions' in filters:
            extensions = filters['extensions']
            if isinstance(extensions, list):
                for ext in extensions:
                    query_parts.append(f"ext:{ext}")
            else:
                query_parts.append(f"ext:{extensions}")

        # Path filter
        if 'path' in filters:
            path_value = filters['path']
            query_parts.append(f'path:"{path_value}"')

        # Content search
        if 'content' in filters:
            content_value = filters['content']
            query_parts.append(f'content:"{content_value}"')

        return " ".join(query_parts)

    @staticmethod
    def parse_filter_badge_text(badge_text: str) -> str:
        """
        Parse filter badge text to human-readable format.

        Args:
            badge_text: Filter text from UI badge

        Returns:
            Human-readable filter description
        """
        # Size badges
        size_map = {
            '>1kb': 'Larger than 1 KB',
            '>1mb': 'Larger than 1 MB',
            '>100mb': 'Larger than 100 MB',
            '>1gb': 'Larger than 1 GB',
        }

        if badge_text.lower() in size_map:
            return size_map[badge_text.lower()]

        # Date badges
        date_map = {
            'today': 'Modified today',
            'thisweek': 'Modified this week',
            'thismonth': 'Modified this month',
            'thisyear': 'Modified this year',
        }

        if badge_text.lower() in date_map:
            return date_map[badge_text.lower()]

        # Type badges
        type_map = {
            'document': 'Documents',
            'image': 'Images',
            'video': 'Videos',
            'audio': 'Audio files',
            'archive': 'Archives',
            'code': 'Code files',
        }

        if badge_text.lower() in type_map:
            return type_map[badge_text.lower()]

        return badge_text

    @staticmethod
    def get_filter_summary(filters: Dict) -> str:
        """
        Get human-readable summary of active filters.

        Args:
            filters: Dictionary of active filters

        Returns:
            Human-readable summary string

        Example:
            >>> filters = {'size': '>1mb', 'type': 'document', 'modified': 'today'}
            >>> FilterIntegration.get_filter_summary(filters)
            '3 filters: Size > 1 MB, Documents, Modified today'
        """
        if not filters:
            return "No filters active"

        summaries = []

        for key, value in filters.items():
            if key == 'size':
                summaries.append(FilterIntegration.parse_filter_badge_text(value))
            elif key in ['modified', 'created', 'accessed']:
                field_name = key.capitalize()
                summaries.append(f"{field_name}: {FilterIntegration.parse_filter_badge_text(value)}")
            elif key == 'type':
                summaries.append(FilterIntegration.parse_filter_badge_text(value))
            elif key == 'extensions':
                if isinstance(value, list):
                    summaries.append(f"Extensions: {', '.join(value)}")
                else:
                    summaries.append(f"Extension: {value}")
            elif key == 'path':
                summaries.append(f"Path: {value}")
            elif key == 'content':
                summaries.append(f"Contains: {value}")

        count = len(summaries)
        return f"{count} filter{'s' if count != 1 else ''}: {', '.join(summaries)}"

    @staticmethod
    def validate_filters(filters: Dict) -> tuple[bool, Optional[str]]:
        """
        Validate filter dictionary.

        Args:
            filters: Dictionary of filters to validate

        Returns:
            Tuple of (is_valid, error_message)

        Example:
            >>> filters = {'size': 'invalid', 'type': 'document'}
            >>> valid, error = FilterIntegration.validate_filters(filters)
            >>> print(valid, error)
            False, "Invalid size filter format"
        """
        # Validate size filter
        if 'size' in filters:
            size_value = filters['size']
            if not isinstance(size_value, str):
                return False, "Size filter must be a string"

            # Check format: operator + number + unit
            import re
            if not re.match(r'^[><]=?\d+[kmgt]?b$', size_value, re.IGNORECASE):
                return False, f"Invalid size filter format: {size_value}"

        # Validate type filter
        if 'type' in filters:
            valid_types = ['document', 'image', 'video', 'audio', 'archive', 'code', 'executable', 'font']
            type_value = filters['type']
            if type_value not in valid_types:
                return False, f"Invalid file type: {type_value}"

        # Validate date filters
        for date_field in ['modified', 'created', 'accessed']:
            if date_field in filters:
                date_value = filters[date_field]
                if not isinstance(date_value, str):
                    return False, f"{date_field} filter must be a string"

                # Check if it's a preset or custom date
                valid_presets = ['today', 'yesterday', 'thisweek', 'lastweek', 'thismonth', 'lastmonth', 'thisyear', 'lastyear']

                import re
                # Check preset or date format
                if date_value not in valid_presets:
                    if not re.match(r'^[><]=?\d{4}-\d{2}-\d{2}$', date_value):
                        return False, f"Invalid {date_field} filter format: {date_value}"

        # Validate extensions
        if 'extensions' in filters:
            extensions = filters['extensions']
            if not isinstance(extensions, (list, str)):
                return False, "Extensions must be a string or list"

            if isinstance(extensions, list):
                for ext in extensions:
                    if not isinstance(ext, str):
                        return False, "All extensions must be strings"

        return True, None

    @staticmethod
    def merge_filters(filters1: Dict, filters2: Dict, strategy: str = 'replace') -> Dict:
        """
        Merge two filter dictionaries.

        Args:
            filters1: First filter dictionary
            filters2: Second filter dictionary
            strategy: Merge strategy ('replace', 'append', 'combine')

        Returns:
            Merged filter dictionary

        Example:
            >>> f1 = {'size': '>1mb', 'type': 'document'}
            >>> f2 = {'modified': 'today', 'extensions': ['pdf']}
            >>> FilterIntegration.merge_filters(f1, f2)
            {'size': '>1mb', 'type': 'document', 'modified': 'today', 'extensions': ['pdf']}
        """
        result = filters1.copy()

        if strategy == 'replace':
            # Replace existing keys
            result.update(filters2)

        elif strategy == 'append':
            # Append to list values, replace others
            for key, value in filters2.items():
                if key in result:
                    if isinstance(result[key], list) and isinstance(value, list):
                        result[key].extend(value)
                    else:
                        result[key] = value
                else:
                    result[key] = value

        elif strategy == 'combine':
            # Combine filters intelligently
            for key, value in filters2.items():
                if key == 'extensions':
                    # Combine extensions
                    if key in result:
                        existing = result[key]
                        if isinstance(existing, list):
                            if isinstance(value, list):
                                result[key] = list(set(existing + value))
                            else:
                                result[key] = list(set(existing + [value]))
                        else:
                            if isinstance(value, list):
                                result[key] = list(set([existing] + value))
                            else:
                                result[key] = list(set([existing, value]))
                    else:
                        result[key] = value
                else:
                    # For other filters, replace
                    result[key] = value

        return result

    @staticmethod
    def filter_to_dict(filter_string: str) -> Dict:
        """
        Parse filter string to dictionary format.

        Args:
            filter_string: Filter string (e.g., "size:>1mb type:document")

        Returns:
            Dictionary of filters

        Example:
            >>> FilterIntegration.filter_to_dict("size:>1mb type:document modified:today")
            {'size': '>1mb', 'type': 'document', 'modified': 'today'}
        """
        import re

        filters = {}

        # Pattern: key:value (with optional quotes)
        pattern = r'(\w+):("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|[^\s]+)'

        matches = re.finditer(pattern, filter_string)

        for match in matches:
            key = match.group(1)
            value = match.group(2).strip('\'"')

            # Handle extensions specially (can have multiple)
            if key == 'ext':
                if 'extensions' not in filters:
                    filters['extensions'] = []
                filters['extensions'].append(value)
            else:
                filters[key] = value

        return filters

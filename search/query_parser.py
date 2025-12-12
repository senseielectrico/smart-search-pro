"""
Query parser for advanced search queries.

Supports:
- Multiple keywords separated by *
- Regex patterns (prefix: regex:)
- File type filters (ext:pdf, type:image)
- Size filters (size:>10mb, size:<1gb)
- Date filters (modified:today, modified:thisweek, created:2024)
- Path filters (path:documents, folder:downloads)
- Content search (content:keyword)
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


class FilterType(Enum):
    """Types of filters supported."""

    EXTENSION = "ext"
    TYPE = "type"
    SIZE = "size"
    MODIFIED = "modified"
    CREATED = "created"
    ACCESSED = "accessed"
    PATH = "path"
    FOLDER = "folder"
    CONTENT = "content"
    REGEX = "regex"


class SizeOperator(Enum):
    """Size comparison operators."""

    GREATER = ">"
    LESS = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    EQUAL = "="


class DatePreset(Enum):
    """Date filter presets."""

    TODAY = "today"
    YESTERDAY = "yesterday"
    THIS_WEEK = "thisweek"
    LAST_WEEK = "lastweek"
    THIS_MONTH = "thismonth"
    LAST_MONTH = "lastmonth"
    THIS_YEAR = "thisyear"
    LAST_YEAR = "lastyear"


@dataclass
class SizeFilter:
    """Size filter specification."""

    operator: SizeOperator
    value: int  # Size in bytes
    unit: str  # Original unit (kb, mb, gb, tb)


@dataclass
class DateFilter:
    """Date filter specification."""

    field: str  # modified, created, accessed
    preset: Optional[DatePreset] = None
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    operator: Optional[SizeOperator] = None
    date: Optional[datetime] = None


@dataclass
class PathFilter:
    """Path filter specification."""

    path: str
    exact: bool = False  # Exact match vs contains


@dataclass
class ParsedQuery:
    """Parsed search query with all components."""

    keywords: List[str] = field(default_factory=list)
    extensions: Set[str] = field(default_factory=set)
    file_types: Set[str] = field(default_factory=set)
    size_filters: List[SizeFilter] = field(default_factory=list)
    date_filters: List[DateFilter] = field(default_factory=list)
    path_filters: List[PathFilter] = field(default_factory=list)
    content_keywords: List[str] = field(default_factory=list)
    regex_pattern: Optional[str] = None
    is_regex: bool = False
    exclude_patterns: List[str] = field(default_factory=list)

    def has_filters(self) -> bool:
        """Check if any filters are applied."""
        return bool(
            self.extensions
            or self.file_types
            or self.size_filters
            or self.date_filters
            or self.path_filters
            or self.content_keywords
            or self.regex_pattern
            or self.exclude_patterns
        )


class QueryParser:
    """
    Advanced query parser for search queries.

    Supports complex query syntax with multiple filter types and operators.
    """

    # File type mappings
    FILE_TYPE_MAPPINGS = {
        "image": ["jpg", "jpeg", "png", "gif", "bmp", "svg", "webp", "tiff", "ico"],
        "video": ["mp4", "avi", "mkv", "mov", "wmv", "flv", "webm", "m4v", "mpg", "mpeg"],
        "audio": ["mp3", "wav", "flac", "aac", "ogg", "wma", "m4a", "opus"],
        "document": ["doc", "docx", "pdf", "txt", "rtf", "odt", "pages"],
        "spreadsheet": ["xls", "xlsx", "csv", "ods", "numbers"],
        "presentation": ["ppt", "pptx", "odp", "key"],
        "archive": ["zip", "rar", "7z", "tar", "gz", "bz2", "xz"],
        "code": ["py", "js", "ts", "java", "cpp", "c", "h", "cs", "go", "rs", "rb"],
        "executable": ["exe", "msi", "bat", "cmd", "sh", "app", "dmg"],
        "font": ["ttf", "otf", "woff", "woff2"],
    }

    # Size unit multipliers (to bytes)
    SIZE_UNITS = {
        "b": 1,
        "byte": 1,
        "bytes": 1,
        "kb": 1024,
        "mb": 1024**2,
        "gb": 1024**3,
        "tb": 1024**4,
    }

    def __init__(self):
        """Initialize query parser."""
        self._filter_pattern = re.compile(
            r'(\w+):("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|[^\s]+)',
            re.IGNORECASE,
        )

    def parse(self, query: str) -> ParsedQuery:
        """
        Parse search query into structured components.

        Args:
            query: Raw search query string

        Returns:
            ParsedQuery object with parsed components
        """
        parsed = ParsedQuery()

        # Extract filters first
        filters = self._extract_filters(query)

        # Remove filters from query to get keywords
        remaining_query = query
        for match in self._filter_pattern.finditer(query):
            remaining_query = remaining_query.replace(match.group(0), "", 1)

        # Parse remaining keywords
        parsed.keywords = self._parse_keywords(remaining_query.strip())

        # Process filters
        for filter_type, value in filters:
            self._process_filter(parsed, filter_type, value)

        return parsed

    def _extract_filters(self, query: str) -> List[Tuple[str, str]]:
        """Extract filter specifications from query."""
        filters = []
        for match in self._filter_pattern.finditer(query):
            filter_name = match.group(1).lower()
            filter_value = match.group(2).strip('\'"')
            filters.append((filter_name, filter_value))
        return filters

    def _parse_keywords(self, text: str) -> List[str]:
        """Parse keywords from remaining query text."""
        if not text:
            return []

        # Split by * for multiple keywords
        keywords = [kw.strip() for kw in text.split("*") if kw.strip()]

        # Also handle quoted strings
        quoted_pattern = re.compile(r'"([^"]+)"|\'([^\']+)\'')
        matches = quoted_pattern.findall(text)
        for match in matches:
            keyword = match[0] or match[1]
            if keyword and keyword not in keywords:
                keywords.append(keyword)

        # Handle space-separated keywords if no * separator
        if not keywords and text:
            keywords = [kw for kw in text.split() if kw and not kw.startswith("-")]

        return keywords

    def _process_filter(self, parsed: ParsedQuery, filter_type: str, value: str):
        """Process individual filter and add to parsed query."""
        if filter_type in ("ext", "extension"):
            parsed.extensions.add(value.lstrip(".").lower())

        elif filter_type == "type":
            value_lower = value.lower()
            if value_lower in self.FILE_TYPE_MAPPINGS:
                parsed.file_types.add(value_lower)
                parsed.extensions.update(self.FILE_TYPE_MAPPINGS[value_lower])
            else:
                # Treat as extension
                parsed.extensions.add(value_lower)

        elif filter_type == "size":
            size_filter = self._parse_size_filter(value)
            if size_filter:
                parsed.size_filters.append(size_filter)

        elif filter_type in ("modified", "created", "accessed"):
            date_filter = self._parse_date_filter(filter_type, value)
            if date_filter:
                parsed.date_filters.append(date_filter)

        elif filter_type in ("path", "folder", "dir", "directory"):
            parsed.path_filters.append(
                PathFilter(path=value, exact=filter_type == "path")
            )

        elif filter_type == "content":
            parsed.content_keywords.append(value)

        elif filter_type == "regex":
            parsed.regex_pattern = value
            parsed.is_regex = True

        elif filter_type in ("not", "exclude", "-"):
            parsed.exclude_patterns.append(value)

    def _parse_size_filter(self, value: str) -> Optional[SizeFilter]:
        """
        Parse size filter specification.

        Examples: >10mb, <1gb, >=500kb
        """
        # Extract operator
        operator_match = re.match(r"^(>=|<=|>|<|=)?(.+)", value)
        if not operator_match:
            return None

        operator_str = operator_match.group(1) or "="
        size_str = operator_match.group(2).strip()

        # Map operator
        operator_map = {
            ">": SizeOperator.GREATER,
            "<": SizeOperator.LESS,
            ">=": SizeOperator.GREATER_EQUAL,
            "<=": SizeOperator.LESS_EQUAL,
            "=": SizeOperator.EQUAL,
        }
        operator = operator_map.get(operator_str, SizeOperator.EQUAL)

        # Extract value and unit
        size_match = re.match(r"^([\d.]+)\s*([a-z]+)?$", size_str, re.IGNORECASE)
        if not size_match:
            return None

        size_value = float(size_match.group(1))
        unit = (size_match.group(2) or "bytes").lower()

        # Convert to bytes
        multiplier = self.SIZE_UNITS.get(unit, 1)
        size_bytes = int(size_value * multiplier)

        return SizeFilter(operator=operator, value=size_bytes, unit=unit)

    def _parse_date_filter(self, field: str, value: str) -> Optional[DateFilter]:
        """
        Parse date filter specification.

        Examples: today, thisweek, 2024, 2024-03, 2024-03-15, >2024-01-01
        """
        value_lower = value.lower()

        # Check for preset
        for preset in DatePreset:
            if preset.value == value_lower:
                return DateFilter(field=field, preset=preset)

        # Check for operator prefix
        operator_match = re.match(r"^(>=|<=|>|<|=)?(.+)", value)
        if not operator_match:
            return None

        operator_str = operator_match.group(1)
        date_str = operator_match.group(2).strip()

        operator = None
        if operator_str:
            operator_map = {
                ">": SizeOperator.GREATER,
                "<": SizeOperator.LESS,
                ">=": SizeOperator.GREATER_EQUAL,
                "<=": SizeOperator.LESS_EQUAL,
                "=": SizeOperator.EQUAL,
            }
            operator = operator_map.get(operator_str)

        # Parse date components
        date_parts = date_str.split("-")

        if len(date_parts) == 1:
            # Year only
            try:
                year = int(date_parts[0])
                return DateFilter(field=field, year=year, operator=operator)
            except ValueError:
                return None

        elif len(date_parts) == 2:
            # Year-Month
            try:
                year = int(date_parts[0])
                month = int(date_parts[1])
                return DateFilter(
                    field=field, year=year, month=month, operator=operator
                )
            except ValueError:
                return None

        elif len(date_parts) == 3:
            # Year-Month-Day
            try:
                year = int(date_parts[0])
                month = int(date_parts[1])
                day = int(date_parts[2])
                date = datetime(year, month, day)
                return DateFilter(
                    field=field,
                    year=year,
                    month=month,
                    day=day,
                    date=date,
                    operator=operator,
                )
            except (ValueError, TypeError):
                return None

        return None

    def build_everything_query(self, parsed: ParsedQuery) -> str:
        """
        Build Everything search syntax query from parsed query.

        Args:
            parsed: ParsedQuery object

        Returns:
            Everything-compatible query string
        """
        query_parts = []

        # Add keywords
        if parsed.keywords:
            keywords_query = " ".join(f'"{kw}"' for kw in parsed.keywords)
            query_parts.append(keywords_query)

        # Add extensions
        if parsed.extensions:
            ext_query = " | ".join(f"*.{ext}" for ext in parsed.extensions)
            query_parts.append(f"({ext_query})")

        # Add path filters
        for path_filter in parsed.path_filters:
            if path_filter.exact:
                query_parts.append(f'path:"{path_filter.path}"')
            else:
                query_parts.append(f'"{path_filter.path}"')

        # Add size filters
        for size_filter in parsed.size_filters:
            operator_map = {
                SizeOperator.GREATER: ">",
                SizeOperator.LESS: "<",
                SizeOperator.GREATER_EQUAL: ">=",
                SizeOperator.LESS_EQUAL: "<=",
                SizeOperator.EQUAL: "",
            }
            op = operator_map[size_filter.operator]
            # Convert to appropriate unit for readability
            if size_filter.value >= self.SIZE_UNITS["gb"]:
                size_val = size_filter.value / self.SIZE_UNITS["gb"]
                unit = "gb"
            elif size_filter.value >= self.SIZE_UNITS["mb"]:
                size_val = size_filter.value / self.SIZE_UNITS["mb"]
                unit = "mb"
            elif size_filter.value >= self.SIZE_UNITS["kb"]:
                size_val = size_filter.value / self.SIZE_UNITS["kb"]
                unit = "kb"
            else:
                size_val = size_filter.value
                unit = ""

            query_parts.append(f"size:{op}{size_val}{unit}")

        # Add date filters
        for date_filter in parsed.date_filters:
            date_query = self._build_date_query(date_filter)
            if date_query:
                query_parts.append(date_query)

        # Add exclude patterns
        for pattern in parsed.exclude_patterns:
            query_parts.append(f'!"{pattern}"')

        # Combine all parts
        return " ".join(query_parts)

    def _build_date_query(self, date_filter: DateFilter) -> str:
        """Build Everything date query from date filter."""
        field_map = {
            "modified": "dm",
            "created": "dc",
            "accessed": "da",
        }
        field = field_map.get(date_filter.field, "dm")

        if date_filter.preset:
            preset_map = {
                DatePreset.TODAY: "today",
                DatePreset.YESTERDAY: "yesterday",
                DatePreset.THIS_WEEK: "thisweek",
                DatePreset.LAST_WEEK: "lastweek",
                DatePreset.THIS_MONTH: "thismonth",
                DatePreset.LAST_MONTH: "lastmonth",
                DatePreset.THIS_YEAR: "thisyear",
                DatePreset.LAST_YEAR: "lastyear",
            }
            preset_val = preset_map.get(date_filter.preset)
            if preset_val:
                return f"{field}:{preset_val}"

        elif date_filter.date:
            date_str = date_filter.date.strftime("%Y-%m-%d")
            if date_filter.operator:
                operator_map = {
                    SizeOperator.GREATER: ">",
                    SizeOperator.LESS: "<",
                    SizeOperator.GREATER_EQUAL: ">=",
                    SizeOperator.LESS_EQUAL: "<=",
                }
                op = operator_map.get(date_filter.operator, "")
                return f"{field}:{op}{date_str}"
            return f"{field}:{date_str}"

        elif date_filter.year:
            if date_filter.month and date_filter.day:
                date_str = f"{date_filter.year}-{date_filter.month:02d}-{date_filter.day:02d}"
            elif date_filter.month:
                date_str = f"{date_filter.year}-{date_filter.month:02d}"
            else:
                date_str = str(date_filter.year)

            if date_filter.operator:
                operator_map = {
                    SizeOperator.GREATER: ">",
                    SizeOperator.LESS: "<",
                    SizeOperator.GREATER_EQUAL: ">=",
                    SizeOperator.LESS_EQUAL: "<=",
                }
                op = operator_map.get(date_filter.operator, "")
                return f"{field}:{op}{date_str}"
            return f"{field}:{date_str}"

        return ""

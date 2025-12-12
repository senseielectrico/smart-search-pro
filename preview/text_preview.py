"""
Text file preview with syntax highlighting and encoding detection.

Supports:
- Syntax highlighting for common programming languages
- Line numbers
- Automatic encoding detection
- Large file handling (preview first 10KB)
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class TextPreviewer:
    """Generate previews for text files with syntax highlighting."""

    # Maximum bytes to read for preview
    MAX_PREVIEW_SIZE = 10 * 1024  # 10KB
    MAX_LINES = 500  # Maximum lines to show

    # Common encodings to try
    ENCODINGS = ['utf-8', 'utf-16', 'latin-1', 'cp1252', 'ascii']

    # File extensions mapped to language names for syntax highlighting (40+ languages)
    LANGUAGE_MAP = {
        # Python
        '.py': 'python',
        '.pyw': 'python',
        '.pyi': 'python',
        # JavaScript/TypeScript
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.mjs': 'javascript',
        '.cjs': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        # Web
        '.html': 'html',
        '.htm': 'html',
        '.xhtml': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sass': 'sass',
        '.less': 'less',
        # Data formats
        '.json': 'json',
        '.json5': 'json',
        '.jsonc': 'json',
        '.xml': 'xml',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.toml': 'toml',
        '.csv': 'text',
        # Markdown & Documentation
        '.md': 'markdown',
        '.markdown': 'markdown',
        '.rst': 'rst',
        '.tex': 'latex',
        # Shell
        '.sh': 'bash',
        '.bash': 'bash',
        '.zsh': 'bash',
        '.fish': 'fish',
        '.bat': 'batch',
        '.cmd': 'batch',
        '.ps1': 'powershell',
        # SQL
        '.sql': 'sql',
        '.mysql': 'mysql',
        '.pgsql': 'postgresql',
        # C/C++
        '.c': 'c',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.c++': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',
        '.hh': 'cpp',
        '.hxx': 'cpp',
        # C#
        '.cs': 'csharp',
        # Java
        '.java': 'java',
        '.class': 'java',
        # PHP
        '.php': 'php',
        '.php3': 'php',
        '.php4': 'php',
        '.php5': 'php',
        # Ruby
        '.rb': 'ruby',
        '.rbw': 'ruby',
        # Go
        '.go': 'go',
        # Rust
        '.rs': 'rust',
        # Swift
        '.swift': 'swift',
        # Kotlin
        '.kt': 'kotlin',
        '.kts': 'kotlin',
        # R
        '.r': 'r',
        '.R': 'r',
        # Matlab
        '.m': 'matlab',
        # Lua
        '.lua': 'lua',
        # Perl
        '.pl': 'perl',
        '.pm': 'perl',
        # Scala
        '.scala': 'scala',
        # Vim
        '.vim': 'vim',
        # Diff/Patch
        '.diff': 'diff',
        '.patch': 'diff',
        # Docker
        '.dockerfile': 'docker',
        # Config files
        '.ini': 'ini',
        '.cfg': 'ini',
        '.conf': 'ini',
        '.config': 'ini',
        '.properties': 'properties',
        # Elixir
        '.ex': 'elixir',
        '.exs': 'elixir',
        # Erlang
        '.erl': 'erlang',
        # Haskell
        '.hs': 'haskell',
        # Clojure
        '.clj': 'clojure',
        '.cljs': 'clojure',
        # Dart
        '.dart': 'dart',
        # Vue
        '.vue': 'vue',
        # GraphQL
        '.graphql': 'graphql',
        '.gql': 'graphql',
        # Svelte
        '.svelte': 'svelte',
        # Groovy
        '.groovy': 'groovy',
        # Nim
        '.nim': 'nim',
        # Crystal
        '.cr': 'crystal',
        # Julia
        '.jl': 'julia',
        # F#
        '.fs': 'fsharp',
        '.fsx': 'fsharp',
        # Objective-C
        '.mm': 'objectivec',
        # Assembly
        '.asm': 'nasm',
        '.s': 'gas',
    }

    def __init__(self):
        """Initialize text previewer."""
        self._pygments_available = False
        self._markdown_available = False

        try:
            import pygments
            from pygments import lexers, formatters
            self._pygments_available = True
        except ImportError:
            logger.debug("Pygments not available for syntax highlighting")

        try:
            import markdown
            self._markdown_available = True
        except ImportError:
            logger.debug("Markdown not available for rendering")

    def generate_preview(self, file_path: str) -> Dict[str, Any]:
        """
        Generate text preview with optional syntax highlighting.

        Args:
            file_path: Path to text file

        Returns:
            Dictionary containing:
                - text: Preview text
                - highlighted: HTML with syntax highlighting (if available)
                - encoding: Detected encoding
                - lines: Number of lines
                - truncated: Whether file was truncated
                - language: Detected language
        """
        if not os.path.exists(file_path):
            return {'error': 'File not found'}

        # Detect encoding and read content
        content, encoding = self._read_with_encoding(file_path)
        if content is None:
            return {'error': 'Could not decode file'}

        # Check file size
        file_size = os.path.getsize(file_path)
        truncated = file_size > self.MAX_PREVIEW_SIZE

        # Split into lines
        lines = content.splitlines()
        total_lines = len(lines)

        # Truncate if too many lines
        if len(lines) > self.MAX_LINES:
            lines = lines[:self.MAX_LINES]
            truncated = True

        # Get language for syntax highlighting
        language = self._detect_language(file_path, content)

        # Generate line-numbered text
        numbered_text = self._add_line_numbers(lines)

        result = {
            'text': numbered_text,
            'encoding': encoding,
            'lines': total_lines,
            'truncated': truncated,
            'language': language,
        }

        # Add syntax highlighting if available
        if self._pygments_available and language:
            highlighted = self._highlight_code('\n'.join(lines), language)
            if highlighted:
                result['highlighted'] = highlighted

        return result

    def _read_with_encoding(self, file_path: str) -> tuple[Optional[str], Optional[str]]:
        """
        Read file content with automatic encoding detection.

        Args:
            file_path: Path to file

        Returns:
            Tuple of (content, encoding) or (None, None) if failed
        """
        # Try each encoding
        for encoding in self.ENCODINGS:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read(self.MAX_PREVIEW_SIZE)
                    return content, encoding
            except (UnicodeDecodeError, LookupError):
                continue

        # Try with chardet if available
        try:
            import chardet

            with open(file_path, 'rb') as f:
                raw_data = f.read(self.MAX_PREVIEW_SIZE)
                result = chardet.detect(raw_data)
                encoding = result['encoding']

                if encoding:
                    try:
                        content = raw_data.decode(encoding)
                        return content, encoding
                    except (UnicodeDecodeError, LookupError):
                        pass
        except ImportError:
            pass

        # Last resort: read as binary and replace errors
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(self.MAX_PREVIEW_SIZE)
                content = raw_data.decode('utf-8', errors='replace')
                return content, 'utf-8 (with errors)'
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None, None

    def _detect_language(self, file_path: str, content: str) -> Optional[str]:
        """
        Detect programming language from file extension or content.

        Args:
            file_path: Path to file
            content: File content

        Returns:
            Language name or None
        """
        # Check by extension
        ext = Path(file_path).suffix.lower()
        if ext in self.LANGUAGE_MAP:
            return self.LANGUAGE_MAP[ext]

        # Special cases based on filename
        filename = Path(file_path).name.lower()
        if filename == 'dockerfile':
            return 'docker'
        elif filename == 'makefile':
            return 'makefile'
        elif filename == '.gitignore' or filename.endswith('ignore'):
            return 'gitignore'

        # Try to detect from shebang
        if content.startswith('#!'):
            first_line = content.split('\n')[0].lower()
            if 'python' in first_line:
                return 'python'
            elif 'bash' in first_line or 'sh' in first_line:
                return 'bash'
            elif 'node' in first_line:
                return 'javascript'

        return None

    def _add_line_numbers(self, lines: list[str]) -> str:
        """
        Add line numbers to text.

        Args:
            lines: List of text lines

        Returns:
            Text with line numbers
        """
        if not lines:
            return ''

        # Calculate padding for line numbers
        max_line_num = len(lines)
        padding = len(str(max_line_num))

        numbered_lines = []
        for i, line in enumerate(lines, 1):
            numbered_lines.append(f"{i:>{padding}} | {line}")

        return '\n'.join(numbered_lines)

    def _highlight_code(self, code: str, language: str) -> Optional[str]:
        """
        Apply syntax highlighting to code.

        Args:
            code: Source code
            language: Programming language

        Returns:
            HTML with syntax highlighting or None
        """
        if not self._pygments_available:
            return None

        try:
            from pygments import highlight
            from pygments.lexers import get_lexer_by_name
            from pygments.formatters import HtmlFormatter

            lexer = get_lexer_by_name(language, stripall=True)
            formatter = HtmlFormatter(
                linenos='table',
                cssclass='source',
                style='monokai',
                noclasses=True,
            )

            highlighted = highlight(code, lexer, formatter)
            return highlighted

        except Exception as e:
            logger.debug(f"Error highlighting code: {e}")
            return None

    def is_text_file(self, file_path: str) -> bool:
        """
        Check if file is likely a text file.

        Args:
            file_path: Path to file

        Returns:
            True if file appears to be text
        """
        # Check by extension
        ext = Path(file_path).suffix.lower()
        if ext in self.LANGUAGE_MAP:
            return True

        # Common text file extensions
        text_extensions = {
            '.txt', '.log', '.csv', '.tsv', '.rtf',
            '.tex', '.readme', '.license', '.authors',
            '.gitignore', '.dockerignore', '.env',
        }
        if ext in text_extensions:
            return True

        # Check by reading first few bytes
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(512)

            # Check for null bytes (binary indicator)
            if b'\x00' in chunk:
                return False

            # Try to decode as text
            try:
                chunk.decode('utf-8')
                return True
            except UnicodeDecodeError:
                pass

            try:
                chunk.decode('latin-1')
                return True
            except UnicodeDecodeError:
                return False

        except Exception:
            return False

    def format_json(self, json_str: str, indent: int = 2) -> str:
        """
        Format JSON with indentation.

        Args:
            json_str: JSON string
            indent: Indentation spaces

        Returns:
            Formatted JSON string
        """
        try:
            import json
            obj = json.loads(json_str)
            return json.dumps(obj, indent=indent, ensure_ascii=False, sort_keys=False)
        except Exception as e:
            logger.debug(f"Error formatting JSON: {e}")
            return json_str

    def render_markdown(self, markdown_text: str) -> Optional[str]:
        """
        Render Markdown to HTML.

        Args:
            markdown_text: Markdown text

        Returns:
            HTML string or None
        """
        if not self._markdown_available:
            return None

        try:
            import markdown
            md = markdown.Markdown(
                extensions=['fenced_code', 'tables', 'nl2br', 'codehilite'],
                extension_configs={
                    'codehilite': {
                        'noclasses': True,
                        'pygments_style': 'monokai'
                    }
                }
            )
            html = md.convert(markdown_text)

            # Add CSS styling
            styled_html = f"""
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                code {{ background: #2d2d2d; color: #f8f8f2; padding: 2px 6px; border-radius: 3px; }}
                pre {{ background: #2d2d2d; color: #f8f8f2; padding: 12px; border-radius: 6px; overflow-x: auto; }}
                table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background: #f2f2f2; font-weight: 600; }}
                blockquote {{ border-left: 4px solid #0078D4; padding-left: 12px; color: #666; margin: 10px 0; }}
                h1, h2, h3 {{ margin-top: 20px; margin-bottom: 10px; }}
                a {{ color: #0078D4; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
            {html}
            """
            return styled_html
        except Exception as e:
            logger.debug(f"Error rendering markdown: {e}")
            return None

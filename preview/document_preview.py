"""
Document preview for PDF and Office files.

Supports:
- PDF first page rendering
- PDF text extraction
- Office document metadata (Word, Excel, PowerPoint)
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import io

logger = logging.getLogger(__name__)


class DocumentPreviewer:
    """Generate previews for documents (PDF, Office)."""

    # Maximum text length to extract from PDF
    MAX_TEXT_LENGTH = 5000

    def __init__(self):
        """Initialize document previewer."""
        self._pypdf_available = False
        self._pdf2image_available = False
        self._office_available = False

        try:
            import pypdf
            self._pypdf_available = True
        except ImportError:
            logger.debug("pypdf not available for PDF preview")

        try:
            from pdf2image import convert_from_path
            self._pdf2image_available = True
        except ImportError:
            logger.debug("pdf2image not available for PDF rendering")

        try:
            import olefile
            self._office_available = True
        except ImportError:
            logger.debug("olefile not available for Office preview")

    def is_supported(self, file_path: str) -> bool:
        """
        Check if file format is supported.

        Args:
            file_path: Path to file

        Returns:
            True if format is supported
        """
        ext = Path(file_path).suffix.lower()
        supported = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'}
        return ext in supported

    def generate_preview(self, file_path: str) -> Dict[str, Any]:
        """
        Generate document preview.

        Args:
            file_path: Path to document

        Returns:
            Dictionary containing preview data
        """
        if not os.path.exists(file_path):
            return {'error': 'File not found'}

        ext = Path(file_path).suffix.lower()

        if ext == '.pdf':
            return self._preview_pdf(file_path)
        elif ext in {'.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'}:
            return self._preview_office(file_path)
        else:
            return {'error': 'Unsupported document format'}

    def _preview_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Generate PDF preview.

        Args:
            file_path: Path to PDF file

        Returns:
            Dictionary with PDF preview data
        """
        if not self._pypdf_available:
            return {'error': 'pypdf not available'}

        try:
            import pypdf

            result = {
                'type': 'pdf',
                'file_size': os.path.getsize(file_path),
            }

            with open(file_path, 'rb') as f:
                pdf = pypdf.PdfReader(f)

                # Basic info
                result['pages'] = len(pdf.pages)

                # Extract metadata
                if pdf.metadata:
                    metadata = {}
                    for key, value in pdf.metadata.items():
                        clean_key = key.lstrip('/')
                        metadata[clean_key] = str(value)
                    result['metadata'] = metadata

                    # Extract common fields
                    if '/Title' in pdf.metadata:
                        result['title'] = str(pdf.metadata['/Title'])
                    if '/Author' in pdf.metadata:
                        result['author'] = str(pdf.metadata['/Author'])
                    if '/Subject' in pdf.metadata:
                        result['subject'] = str(pdf.metadata['/Subject'])

                # Extract text from first page
                if len(pdf.pages) > 0:
                    try:
                        first_page = pdf.pages[0]
                        text = first_page.extract_text()

                        # Limit text length
                        if len(text) > self.MAX_TEXT_LENGTH:
                            text = text[:self.MAX_TEXT_LENGTH] + '...'

                        result['first_page_text'] = text
                    except Exception as e:
                        logger.debug(f"Error extracting text from PDF: {e}")

                # Try to render first page as image
                if self._pdf2image_available:
                    try:
                        from pdf2image import convert_from_path

                        images = convert_from_path(
                            file_path,
                            first_page=1,
                            last_page=1,
                            dpi=150
                        )

                        if images:
                            # Convert to base64
                            img = images[0]
                            buffer = io.BytesIO()
                            img.save(buffer, format='PNG')
                            buffer.seek(0)

                            import base64
                            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                            result['first_page_image'] = f"data:image/png;base64,{img_base64}"

                    except Exception as e:
                        logger.debug(f"Error rendering PDF page: {e}")

            return result

        except Exception as e:
            logger.error(f"Error previewing PDF: {e}")
            return {'error': str(e)}

    def _preview_office(self, file_path: str) -> Dict[str, Any]:
        """
        Generate Office document preview.

        Args:
            file_path: Path to Office document

        Returns:
            Dictionary with document preview data
        """
        ext = Path(file_path).suffix.lower()

        result = {
            'type': self._get_office_type(ext),
            'file_size': os.path.getsize(file_path),
        }

        # Try to extract metadata with olefile (for .doc, .xls, .ppt)
        if ext in {'.doc', '.xls', '.ppt'} and self._office_available:
            try:
                import olefile

                if olefile.isOleFile(file_path):
                    ole = olefile.OleFileIO(file_path)
                    meta = ole.get_metadata()

                    metadata = {}
                    if meta.author:
                        metadata['author'] = meta.author
                        result['author'] = meta.author
                    if meta.title:
                        metadata['title'] = meta.title
                        result['title'] = meta.title
                    if meta.subject:
                        metadata['subject'] = meta.subject
                        result['subject'] = meta.subject
                    if meta.comments:
                        metadata['comments'] = meta.comments
                    if meta.create_time:
                        metadata['created'] = meta.create_time.isoformat()
                    if meta.last_saved_time:
                        metadata['modified'] = meta.last_saved_time.isoformat()

                    result['metadata'] = metadata
                    ole.close()

            except Exception as e:
                logger.debug(f"Error extracting Office metadata: {e}")

        # For newer formats (.docx, .xlsx, .pptx), they are ZIP files
        elif ext in {'.docx', '.xlsx', '.pptx'}:
            try:
                import zipfile
                import xml.etree.ElementTree as ET

                with zipfile.ZipFile(file_path, 'r') as zf:
                    # Try to read core properties
                    if 'docProps/core.xml' in zf.namelist():
                        core_xml = zf.read('docProps/core.xml')
                        root = ET.fromstring(core_xml)

                        # Define namespaces
                        ns = {
                            'dc': 'http://purl.org/dc/elements/1.1/',
                            'dcterms': 'http://purl.org/dc/terms/',
                            'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
                        }

                        metadata = {}

                        # Extract common fields
                        title = root.find('.//dc:title', ns)
                        if title is not None and title.text:
                            result['title'] = title.text
                            metadata['title'] = title.text

                        creator = root.find('.//dc:creator', ns)
                        if creator is not None and creator.text:
                            result['author'] = creator.text
                            metadata['creator'] = creator.text

                        subject = root.find('.//dc:subject', ns)
                        if subject is not None and subject.text:
                            result['subject'] = subject.text
                            metadata['subject'] = subject.text

                        created = root.find('.//dcterms:created', ns)
                        if created is not None and created.text:
                            metadata['created'] = created.text

                        modified = root.find('.//dcterms:modified', ns)
                        if modified is not None and modified.text:
                            metadata['modified'] = modified.text

                        if metadata:
                            result['metadata'] = metadata

                    # Count pages/sheets/slides
                    if ext == '.docx':
                        result['document_type'] = 'Word Document'
                    elif ext == '.xlsx':
                        result['document_type'] = 'Excel Spreadsheet'
                        # Count sheets
                        if 'xl/workbook.xml' in zf.namelist():
                            wb_xml = zf.read('xl/workbook.xml')
                            wb_root = ET.fromstring(wb_xml)
                            sheets = wb_root.findall('.//{*}sheet')
                            result['sheets'] = len(sheets)
                    elif ext == '.pptx':
                        result['document_type'] = 'PowerPoint Presentation'
                        # Count slides
                        slides = [name for name in zf.namelist() if name.startswith('ppt/slides/slide')]
                        result['slides'] = len(slides)

            except Exception as e:
                logger.debug(f"Error extracting Office XML metadata: {e}")

        return result

    def _get_office_type(self, ext: str) -> str:
        """
        Get Office document type from extension.

        Args:
            ext: File extension

        Returns:
            Document type string
        """
        type_map = {
            '.doc': 'word',
            '.docx': 'word',
            '.xls': 'excel',
            '.xlsx': 'excel',
            '.ppt': 'powerpoint',
            '.pptx': 'powerpoint',
        }
        return type_map.get(ext, 'office')

    def extract_text(self, file_path: str, max_length: Optional[int] = None) -> str:
        """
        Extract text from PDF document.

        Args:
            file_path: Path to PDF file
            max_length: Maximum text length to extract

        Returns:
            Extracted text
        """
        if not self._pypdf_available:
            return ""

        ext = Path(file_path).suffix.lower()
        if ext != '.pdf':
            return ""

        try:
            import pypdf

            text_parts = []
            total_length = 0
            max_len = max_length or self.MAX_TEXT_LENGTH

            with open(file_path, 'rb') as f:
                pdf = pypdf.PdfReader(f)

                for page in pdf.pages:
                    try:
                        page_text = page.extract_text()
                        text_parts.append(page_text)
                        total_length += len(page_text)

                        if total_length >= max_len:
                            break
                    except Exception as e:
                        logger.debug(f"Error extracting text from page: {e}")
                        continue

            text = '\n'.join(text_parts)

            if len(text) > max_len:
                text = text[:max_len] + '...'

            return text

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""

    def render_pdf_pages(
        self,
        file_path: str,
        start_page: int = 1,
        end_page: Optional[int] = None,
        dpi: int = 150
    ) -> list[str]:
        """
        Render multiple PDF pages as base64 images.

        Args:
            file_path: Path to PDF file
            start_page: Starting page number (1-indexed)
            end_page: Ending page number (None = all pages)
            dpi: Rendering DPI

        Returns:
            List of base64-encoded images
        """
        if not self._pdf2image_available:
            return []

        try:
            from pdf2image import convert_from_path
            import base64
            import io

            images = convert_from_path(
                file_path,
                first_page=start_page,
                last_page=end_page,
                dpi=dpi
            )

            result = []
            for img in images:
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                buffer.seek(0)
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                result.append(f"data:image/png;base64,{img_base64}")

            return result

        except Exception as e:
            logger.error(f"Error rendering PDF pages: {e}")
            return []

    def extract_text_from_docx(self, file_path: str) -> str:
        """
        Extract text from Word DOCX file.

        Args:
            file_path: Path to DOCX file

        Returns:
            Extracted text
        """
        try:
            # Try with python-docx if available
            try:
                import docx
                doc = docx.Document(file_path)
                paragraphs = [p.text for p in doc.paragraphs]
                return '\n'.join(paragraphs)
            except ImportError:
                pass

            # Fallback: extract from XML
            import zipfile
            import xml.etree.ElementTree as ET

            with zipfile.ZipFile(file_path, 'r') as zf:
                if 'word/document.xml' not in zf.namelist():
                    return ""

                doc_xml = zf.read('word/document.xml')
                root = ET.fromstring(doc_xml)

                # Define namespace
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

                # Extract text from paragraphs
                paragraphs = []
                for p in root.findall('.//w:p', ns):
                    texts = []
                    for t in p.findall('.//w:t', ns):
                        if t.text:
                            texts.append(t.text)
                    if texts:
                        paragraphs.append(''.join(texts))

                return '\n'.join(paragraphs)

        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {e}")
            return ""

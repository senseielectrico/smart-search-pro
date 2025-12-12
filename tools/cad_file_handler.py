"""
CAD File Handler - Specialized tools for CAD file access

Handles:
- Navisworks (.nwd, .nwf, .nwc) files
- AutoCAD (.dwg, .dxf) files
- Revit (.rvt) files
- Remove preview locks
- Force read access
- Extract embedded data

These file types are commonly locked by their respective applications
and require special handling to access while locked.

SECURITY WARNING:
Forcefully accessing locked CAD files may cause:
- Data corruption if files are being written
- Application crashes
- Loss of unsaved work
Use with caution and only on your own files.
"""

import os
import sys
import struct
import json
from typing import Dict, List, Optional, Tuple, BinaryIO
from pathlib import Path
import logging
import shutil
import tempfile

import win32api
import win32con
import win32file
import pywintypes

logger = logging.getLogger(__name__)


class CADFileHandler:
    """
    Specialized handler for CAD files

    Features:
    - Detect CAD file types
    - Extract metadata without opening
    - Clone files to bypass locks
    - Parse file headers
    - Extract preview images
    - Read embedded data

    Supported formats:
    - Navisworks: .nwd (native), .nwf (fileset), .nwc (cache)
    - AutoCAD: .dwg (drawing), .dxf (exchange)
    - Revit: .rvt (project), .rfa (family), .rte (template)
    """

    # File signatures
    SIGNATURES = {
        'DWG': {
            'AC1.40': b'AC1.40',  # AutoCAD R13
            'AC1.50': b'AC1.50',  # AutoCAD R14
            'AC1015': b'AC1015',  # AutoCAD 2000
            'AC1018': b'AC1018',  # AutoCAD 2004
            'AC1021': b'AC1021',  # AutoCAD 2007
            'AC1024': b'AC1024',  # AutoCAD 2010
            'AC1027': b'AC1027',  # AutoCAD 2013
            'AC1032': b'AC1032',  # AutoCAD 2018
        },
        'NWD': b'NAVW',  # Navisworks native
        'NWC': b'NAVW',  # Navisworks cache (similar header)
        'RVT': b'RVT',   # Revit (simplified, actual is more complex)
    }

    def __init__(self):
        self._temp_dir = None

    def __enter__(self):
        self._temp_dir = tempfile.mkdtemp()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._temp_dir and os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir, ignore_errors=True)

    def detect_cad_type(self, file_path: str) -> Dict:
        """
        Detect CAD file type and version

        Args:
            file_path: Path to CAD file

        Returns:
            Dictionary with file type information
        """
        result = {
            'path': file_path,
            'is_cad': False,
            'type': None,
            'version': None,
            'details': {}
        }

        try:
            with open(file_path, 'rb') as f:
                header = f.read(128)

                # Check file extension
                ext = os.path.splitext(file_path)[1].lower()
                result['extension'] = ext

                # Check DWG
                if ext == '.dwg':
                    for version, sig in self.SIGNATURES['DWG'].items():
                        if header.startswith(sig):
                            result['is_cad'] = True
                            result['type'] = 'AutoCAD DWG'
                            result['version'] = version
                            result['details'] = self._parse_dwg_header(header)
                            break

                # Check DXF (ASCII or Binary)
                elif ext == '.dxf':
                    result['is_cad'] = True
                    result['type'] = 'AutoCAD DXF'
                    try:
                        # Try ASCII
                        header_str = header.decode('utf-8', errors='ignore')
                        if '0\nSECTION' in header_str:
                            result['version'] = 'ASCII'
                    except:
                        result['version'] = 'Binary'

                # Check Navisworks
                elif ext in ['.nwd', '.nwf', '.nwc']:
                    if header.startswith(self.SIGNATURES.get('NWD', b'')):
                        result['is_cad'] = True
                        result['type'] = f'Navisworks {ext[1:].upper()}'
                        result['details'] = self._parse_navisworks_header(header, ext)

                # Check Revit
                elif ext in ['.rvt', '.rfa', '.rte']:
                    result['is_cad'] = True
                    result['type'] = f'Revit {ext[1:].upper()}'
                    result['details'] = self._parse_revit_header(header)

        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error detecting CAD type: {e}")

        return result

    def _parse_dwg_header(self, header: bytes) -> Dict:
        """Parse DWG file header"""
        details = {}

        try:
            # DWG files have complex binary format
            # This is a simplified parser for metadata
            if len(header) >= 6:
                details['version_string'] = header[:6].decode('ascii', errors='ignore')

            # Additional parsing would require full DWG spec
            details['note'] = 'Full DWG parsing requires specialized library'

        except Exception as e:
            logger.debug(f"Error parsing DWG header: {e}")

        return details

    def _parse_navisworks_header(self, header: bytes, ext: str) -> Dict:
        """Parse Navisworks file header"""
        details = {}

        try:
            # Navisworks files are compressed compound documents
            details['format'] = 'Compound Document'

            if ext == '.nwf':
                details['type'] = 'Fileset (references external files)'
            elif ext == '.nwc':
                details['type'] = 'Cache (converted model)'
            else:
                details['type'] = 'Native (consolidated model)'

            details['note'] = 'Navisworks files require OLE/Compound Document parser for full access'

        except Exception as e:
            logger.debug(f"Error parsing Navisworks header: {e}")

        return details

    def _parse_revit_header(self, header: bytes) -> Dict:
        """Parse Revit file header"""
        details = {}

        try:
            # Revit files are OLE compound documents
            # Check for OLE signature
            if header[:8] == b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1':
                details['format'] = 'OLE Compound Document'

            details['note'] = 'Revit files require OLE parser for full access'

        except Exception as e:
            logger.debug(f"Error parsing Revit header: {e}")

        return details

    def clone_for_readonly_access(self, file_path: str, output_path: Optional[str] = None) -> Dict:
        """
        Clone CAD file to bypass locks (shadow copy)

        Creates a copy using Windows Volume Shadow Copy Service
        or falls back to direct copy if VSS unavailable.

        Args:
            file_path: Path to locked CAD file
            output_path: Where to save clone (default: temp)

        Returns:
            Dictionary with clone result
        """
        result = {
            'success': False,
            'source': file_path,
            'clone_path': None,
            'method': None,
            'errors': []
        }

        try:
            if output_path is None:
                ext = os.path.splitext(file_path)[1]
                output_path = os.path.join(
                    self._temp_dir or tempfile.gettempdir(),
                    f'cad_clone_{os.path.basename(file_path)}'
                )

            # Method 1: Direct copy with share permissions
            try:
                # Open with FILE_SHARE_READ to allow reading locked files
                handle = win32file.CreateFile(
                    file_path,
                    win32con.GENERIC_READ,
                    win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
                    None,
                    win32con.OPEN_EXISTING,
                    win32con.FILE_FLAG_BACKUP_SEMANTICS,
                    None
                )

                try:
                    # Read in chunks
                    with open(output_path, 'wb') as out_file:
                        while True:
                            hr, data = win32file.ReadFile(handle, 64 * 1024)
                            if not data:
                                break
                            out_file.write(data)

                    result['success'] = True
                    result['clone_path'] = output_path
                    result['method'] = 'Shared Read'
                    logger.info(f"Successfully cloned CAD file: {file_path}")

                finally:
                    win32file.CloseHandle(handle)

            except pywintypes.error as e:
                logger.debug(f"Shared read failed: {e}")

                # Method 2: VSS snapshot (requires admin)
                try:
                    vss_result = self._create_vss_snapshot(file_path, output_path)
                    if vss_result:
                        result['success'] = True
                        result['clone_path'] = output_path
                        result['method'] = 'VSS Snapshot'
                        return result
                except Exception as vss_error:
                    logger.debug(f"VSS snapshot failed: {vss_error}")

                # Method 3: Fallback to standard copy
                try:
                    shutil.copy2(file_path, output_path)
                    result['success'] = True
                    result['clone_path'] = output_path
                    result['method'] = 'Standard Copy'
                except Exception as copy_error:
                    result['errors'].append(f"All clone methods failed: {copy_error}")

        except Exception as e:
            result['errors'].append(str(e))
            logger.error(f"Error cloning CAD file: {e}")

        return result

    def _create_vss_snapshot(self, file_path: str, output_path: str) -> bool:
        """
        Create Volume Shadow Copy snapshot

        This is a simplified implementation. Full VSS requires COM automation.
        """
        try:
            # Using wmi or comtypes would be more robust
            # This is a placeholder for the concept

            # In practice, you would:
            # 1. Create shadow copy using VSS COM API
            # 2. Mount the shadow copy
            # 3. Copy the file from shadow
            # 4. Dismount shadow copy

            logger.warning("VSS snapshot not fully implemented - requires COM automation")
            return False

        except Exception as e:
            logger.error(f"VSS snapshot error: {e}")
            return False

    def extract_metadata(self, file_path: str) -> Dict:
        """
        Extract metadata from CAD file without opening

        Args:
            file_path: Path to CAD file

        Returns:
            Dictionary with metadata
        """
        metadata = {
            'path': file_path,
            'type_detection': self.detect_cad_type(file_path),
            'file_info': {},
            'embedded_data': {}
        }

        try:
            # Get file system metadata
            stat = os.stat(file_path)
            metadata['file_info'] = {
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'accessed': stat.st_atime
            }

            # Try to extract embedded metadata based on type
            ext = os.path.splitext(file_path)[1].lower()

            if ext == '.dxf':
                # DXF is text-based, can parse easily
                metadata['embedded_data'] = self._extract_dxf_metadata(file_path)

            elif ext in ['.nwd', '.nwf', '.nwc']:
                # Navisworks files need OLE parser
                metadata['embedded_data'] = self._extract_navisworks_metadata(file_path)

            # For other formats, use clone method
            elif ext in ['.dwg', '.rvt', '.rfa', '.rte']:
                metadata['note'] = 'Binary format requires specialized parser'

        except Exception as e:
            metadata['error'] = str(e)
            logger.error(f"Error extracting metadata: {e}")

        return metadata

    def _extract_dxf_metadata(self, file_path: str) -> Dict:
        """Extract metadata from DXF file"""
        metadata = {}

        try:
            # DXF files have a HEADER section with metadata
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                in_header = False
                current_var = None

                for line in f:
                    line = line.strip()

                    if line == '0' and f.readline().strip() == 'SECTION':
                        next_line = f.readline().strip()
                        if next_line == '2':
                            section_name = f.readline().strip()
                            if section_name == 'HEADER':
                                in_header = True

                    if in_header:
                        if line == '9':
                            current_var = f.readline().strip()
                        elif current_var and line in ['1', '2', '3', '70']:
                            value = f.readline().strip()
                            metadata[current_var] = value

                    if line == 'ENDSEC':
                        if in_header:
                            break

        except Exception as e:
            logger.debug(f"Error parsing DXF metadata: {e}")

        return metadata

    def _extract_navisworks_metadata(self, file_path: str) -> Dict:
        """Extract metadata from Navisworks file"""
        metadata = {}

        try:
            # Navisworks files are OLE compound documents
            # Would need python-oletools or similar to parse

            metadata['note'] = 'OLE parsing requires additional libraries'

            # Basic file reading
            with open(file_path, 'rb') as f:
                header = f.read(512)
                if header[:8] == b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1':
                    metadata['ole_format'] = 'CFB (Compound File Binary)'

        except Exception as e:
            logger.debug(f"Error parsing Navisworks metadata: {e}")

        return metadata

    def force_readonly_handle(self, file_path: str) -> Optional[int]:
        """
        Get read-only handle to locked file

        Args:
            file_path: Path to file

        Returns:
            File handle or None
        """
        try:
            handle = win32file.CreateFile(
                file_path,
                win32con.GENERIC_READ,
                win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
                None,
                win32con.OPEN_EXISTING,
                win32con.FILE_FLAG_BACKUP_SEMANTICS,
                None
            )

            return handle

        except pywintypes.error as e:
            logger.error(f"Error opening file: {e}")
            return None

    def read_locked_file(self, file_path: str, output_path: Optional[str] = None) -> Dict:
        """
        Read locked CAD file into memory or file

        Args:
            file_path: Path to locked file
            output_path: Where to save (optional)

        Returns:
            Dictionary with read result
        """
        result = {
            'success': False,
            'path': file_path,
            'bytes_read': 0,
            'output_path': output_path
        }

        try:
            handle = self.force_readonly_handle(file_path)
            if not handle:
                result['error'] = 'Could not open file'
                return result

            try:
                if output_path:
                    # Read to file
                    with open(output_path, 'wb') as out_file:
                        while True:
                            hr, data = win32file.ReadFile(handle, 64 * 1024)
                            if not data:
                                break
                            out_file.write(data)
                            result['bytes_read'] += len(data)
                else:
                    # Read to memory
                    chunks = []
                    while True:
                        hr, data = win32file.ReadFile(handle, 64 * 1024)
                        if not data:
                            break
                        chunks.append(data)
                        result['bytes_read'] += len(data)

                    result['data'] = b''.join(chunks)

                result['success'] = True
                logger.info(f"Successfully read {result['bytes_read']} bytes from: {file_path}")

            finally:
                win32file.CloseHandle(handle)

        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error reading locked file: {e}")

        return result


# Convenience functions
def is_cad_file(file_path: str) -> bool:
    """Check if file is a CAD file"""
    handler = CADFileHandler()
    result = handler.detect_cad_type(file_path)
    return result.get('is_cad', False)


def clone_cad_file(file_path: str) -> Optional[str]:
    """Clone locked CAD file"""
    with CADFileHandler() as handler:
        result = handler.clone_for_readonly_access(file_path)
        return result.get('clone_path') if result.get('success') else None


if __name__ == '__main__':
    # Test/demo code
    import argparse

    parser = argparse.ArgumentParser(description='CAD File Handler - Access locked CAD files')
    parser.add_argument('file', help='CAD file to process')
    parser.add_argument('--detect', action='store_true', help='Detect file type')
    parser.add_argument('--metadata', action='store_true', help='Extract metadata')
    parser.add_argument('--clone', action='store_true', help='Clone file')
    parser.add_argument('--output', '-o', help='Output path')

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    with CADFileHandler() as handler:
        if args.detect:
            result = handler.detect_cad_type(args.file)
            print(f"\nCAD File Detection:")
            print(f"  Path: {result['path']}")
            print(f"  Is CAD: {result['is_cad']}")
            if result['is_cad']:
                print(f"  Type: {result['type']}")
                print(f"  Version: {result.get('version', 'Unknown')}")
                if result.get('details'):
                    print(f"  Details: {json.dumps(result['details'], indent=2)}")

        elif args.metadata:
            metadata = handler.extract_metadata(args.file)
            print(f"\nMetadata for: {args.file}")
            print(json.dumps(metadata, indent=2, default=str))

        elif args.clone:
            result = handler.clone_for_readonly_access(args.file, args.output)
            print(f"\nClone Result:")
            print(f"  Success: {result['success']}")
            if result['success']:
                print(f"  Clone Path: {result['clone_path']}")
                print(f"  Method: {result['method']}")
            elif result.get('errors'):
                print(f"  Errors: {', '.join(result['errors'])}")

        else:
            # Default: show all info
            detection = handler.detect_cad_type(args.file)
            print(f"\nCAD File Analysis:")
            print(f"  Is CAD: {detection['is_cad']}")
            if detection['is_cad']:
                print(f"  Type: {detection['type']}")
                print(f"  Version: {detection.get('version', 'Unknown')}")

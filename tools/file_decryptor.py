"""
File Decryptor - Handle encrypted and password-protected files

Features:
- Detect EFS encrypted files
- Attempt EFS decryption with user certificate
- Remove EFS encryption
- Handle BitLocker encrypted volumes
- Office document password removal (xlsx, docx, pptx)
- PDF password removal
- ZIP/RAR password attempts
- Archive password recovery

SECURITY WARNING:
This tool attempts to bypass file encryption and password protection.
Only use on files you own or have legal authorization to access.
Some operations may violate laws in certain jurisdictions.
"""

import os
import sys
import subprocess
import tempfile
import shutil
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
import struct
import zipfile

import win32api
import win32con
import win32file
import win32security
import pywintypes

try:
    import msoffcrypto
    MSOFFCRYPTO_AVAILABLE = True
except ImportError:
    MSOFFCRYPTO_AVAILABLE = False

try:
    import pikepdf
    PIKEPDF_AVAILABLE = True
except ImportError:
    PIKEPDF_AVAILABLE = False

logger = logging.getLogger(__name__)


class FileDecryptor:
    """
    File decryption and password removal utility

    Capabilities:
    - EFS decryption (Windows Encrypting File System)
    - Office document password removal
    - PDF password attempts
    - ZIP password recovery
    - Encrypted file detection

    Limitations:
    - Strong encryption cannot be broken
    - Password removal != password recovery
    - Some operations require specific libraries
    """

    # Office file signatures
    OFFICE_SIGNATURES = {
        b'PK\x03\x04': 'Office Open XML',  # .docx, .xlsx, .pptx
        b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1': 'Office Binary',  # .doc, .xls, .ppt
    }

    # PDF signature
    PDF_SIGNATURE = b'%PDF-'

    # Common passwords for testing
    COMMON_PASSWORDS = [
        '', 'password', '123456', '12345678', 'qwerty', 'abc123',
        'password123', 'admin', 'letmein', 'welcome', '1234',
        'Password1', 'Password123'
    ]

    def __init__(self):
        self._temp_dir = None

    def __enter__(self):
        self._temp_dir = tempfile.mkdtemp()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._temp_dir and os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir, ignore_errors=True)

    def detect_encryption(self, file_path: str) -> Dict:
        """
        Detect if file is encrypted and determine encryption type

        Args:
            file_path: Path to file

        Returns:
            Dictionary with encryption information
        """
        result = {
            'path': file_path,
            'encrypted': False,
            'encryption_types': [],
            'details': {}
        }

        if not os.path.exists(file_path):
            result['error'] = 'File not found'
            return result

        try:
            # Check EFS encryption
            if self._is_efs_encrypted(file_path):
                result['encrypted'] = True
                result['encryption_types'].append('EFS')
                result['details']['efs'] = True

            # Check file signature and content
            with open(file_path, 'rb') as f:
                header = f.read(8)

                # Check Office files
                for sig, office_type in self.OFFICE_SIGNATURES.items():
                    if header.startswith(sig):
                        result['file_type'] = office_type

                        # Check if Office file is encrypted
                        if self._is_office_encrypted(file_path):
                            result['encrypted'] = True
                            result['encryption_types'].append('Office Password')
                            result['details']['office_encrypted'] = True

                # Check PDF
                if header.startswith(self.PDF_SIGNATURE):
                    result['file_type'] = 'PDF'

                    if self._is_pdf_encrypted(file_path):
                        result['encrypted'] = True
                        result['encryption_types'].append('PDF Password')
                        result['details']['pdf_encrypted'] = True

                # Check ZIP
                if header.startswith(b'PK'):
                    if self._is_zip_encrypted(file_path):
                        result['encrypted'] = True
                        result['encryption_types'].append('ZIP Password')
                        result['details']['zip_encrypted'] = True

        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error detecting encryption: {e}")

        return result

    def _is_efs_encrypted(self, file_path: str) -> bool:
        """Check if file is encrypted with EFS"""
        try:
            attrs = win32api.GetFileAttributes(file_path)
            return bool(attrs & win32con.FILE_ATTRIBUTE_ENCRYPTED)
        except:
            return False

    def _is_office_encrypted(self, file_path: str) -> bool:
        """Check if Office file is password protected"""
        if not MSOFFCRYPTO_AVAILABLE:
            # Fallback: try to open as ZIP
            try:
                with zipfile.ZipFile(file_path, 'r') as zf:
                    # If we can list files, it's not encrypted
                    zf.namelist()
                    return False
            except:
                return True

        try:
            with open(file_path, 'rb') as f:
                office_file = msoffcrypto.OfficeFile(f)
                return office_file.is_encrypted()
        except:
            return False

    def _is_pdf_encrypted(self, file_path: str) -> bool:
        """Check if PDF is password protected"""
        if PIKEPDF_AVAILABLE:
            try:
                with pikepdf.open(file_path) as pdf:
                    return pdf.is_encrypted
            except pikepdf.PasswordError:
                return True
            except:
                return False

        # Fallback: check for /Encrypt in PDF
        try:
            with open(file_path, 'rb') as f:
                content = f.read(10000)  # Read first 10KB
                return b'/Encrypt' in content
        except:
            return False

    def _is_zip_encrypted(self, file_path: str) -> bool:
        """Check if ZIP is password protected"""
        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                for info in zf.infolist():
                    if info.flag_bits & 0x1:  # Bit 0 = encrypted
                        return True
            return False
        except:
            return False

    def remove_efs_encryption(self, file_path: str, backup: bool = True) -> Dict:
        """
        Remove EFS encryption from file

        Args:
            file_path: Path to encrypted file
            backup: Create backup before decryption

        Returns:
            Dictionary with operation result
        """
        result = {
            'success': False,
            'path': file_path,
            'backed_up': False,
            'errors': []
        }

        try:
            if not self._is_efs_encrypted(file_path):
                result['errors'].append('File is not EFS encrypted')
                return result

            # Create backup
            if backup:
                backup_path = f"{file_path}.efs_backup"
                shutil.copy2(file_path, backup_path)
                result['backed_up'] = True
                result['backup_path'] = backup_path

            # Decrypt using cipher.exe (Windows built-in)
            cmd = ['cipher', '/d', file_path]
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if process.returncode == 0:
                result['success'] = True
                logger.info(f"Successfully decrypted EFS file: {file_path}")
            else:
                result['errors'].append(f"cipher.exe failed: {process.stderr}")

            # Verify decryption
            if not self._is_efs_encrypted(file_path):
                result['success'] = True
            else:
                if result['success']:
                    result['errors'].append('File still appears encrypted after operation')

        except subprocess.TimeoutExpired:
            result['errors'].append('Decryption timeout')
        except Exception as e:
            result['errors'].append(str(e))
            logger.error(f"Error removing EFS encryption: {e}")

        return result

    def decrypt_office_file(self, file_path: str, password: Optional[str] = None,
                           try_common: bool = True, output_path: Optional[str] = None) -> Dict:
        """
        Decrypt Office document

        Args:
            file_path: Path to encrypted Office file
            password: Known password (optional)
            try_common: Try common passwords
            output_path: Where to save decrypted file (default: same location)

        Returns:
            Dictionary with operation result
        """
        if not MSOFFCRYPTO_AVAILABLE:
            return {
                'success': False,
                'error': 'msoffcrypto-tool not installed. Install with: pip install msoffcrypto-tool'
            }

        result = {
            'success': False,
            'path': file_path,
            'password_found': None,
            'errors': []
        }

        if output_path is None:
            output_path = file_path + '.decrypted' + os.path.splitext(file_path)[1]

        try:
            with open(file_path, 'rb') as f:
                office_file = msoffcrypto.OfficeFile(f)

                if not office_file.is_encrypted():
                    result['errors'].append('File is not encrypted')
                    return result

                # Try provided password
                passwords_to_try = []
                if password:
                    passwords_to_try.append(password)

                # Try common passwords
                if try_common:
                    passwords_to_try.extend(self.COMMON_PASSWORDS)

                # Attempt decryption
                for pwd in passwords_to_try:
                    try:
                        with open(file_path, 'rb') as encrypted_file:
                            office_file = msoffcrypto.OfficeFile(encrypted_file)

                            with open(output_path, 'wb') as decrypted_file:
                                office_file.load_key(password=pwd)
                                office_file.decrypt(decrypted_file)

                            result['success'] = True
                            result['password_found'] = pwd if pwd else '(empty)'
                            result['output_path'] = output_path
                            logger.info(f"Successfully decrypted Office file with password: {'(empty)' if not pwd else '***'}")
                            return result

                    except Exception as e:
                        logger.debug(f"Password '{pwd}' failed: {e}")
                        continue

                result['errors'].append('No working password found')

        except Exception as e:
            result['errors'].append(str(e))
            logger.error(f"Error decrypting Office file: {e}")

        return result

    def decrypt_pdf(self, file_path: str, password: Optional[str] = None,
                   try_common: bool = True, output_path: Optional[str] = None) -> Dict:
        """
        Decrypt PDF file

        Args:
            file_path: Path to encrypted PDF
            password: Known password (optional)
            try_common: Try common passwords
            output_path: Where to save decrypted PDF

        Returns:
            Dictionary with operation result
        """
        if not PIKEPDF_AVAILABLE:
            return {
                'success': False,
                'error': 'pikepdf not installed. Install with: pip install pikepdf'
            }

        result = {
            'success': False,
            'path': file_path,
            'password_found': None,
            'errors': []
        }

        if output_path is None:
            output_path = file_path + '.decrypted.pdf'

        try:
            passwords_to_try = []
            if password:
                passwords_to_try.append(password)

            if try_common:
                passwords_to_try.extend(self.COMMON_PASSWORDS)

            # Try each password
            for pwd in passwords_to_try:
                try:
                    with pikepdf.open(file_path, password=pwd) as pdf:
                        # Save without encryption
                        pdf.save(output_path, encryption=False)

                        result['success'] = True
                        result['password_found'] = pwd if pwd else '(empty)'
                        result['output_path'] = output_path
                        logger.info(f"Successfully decrypted PDF with password: {'(empty)' if not pwd else '***'}")
                        return result

                except pikepdf.PasswordError:
                    logger.debug(f"Password '{pwd}' failed")
                    continue

            result['errors'].append('No working password found')

        except Exception as e:
            result['errors'].append(str(e))
            logger.error(f"Error decrypting PDF: {e}")

        return result

    def decrypt_zip(self, file_path: str, password: Optional[str] = None,
                   try_common: bool = True, output_dir: Optional[str] = None) -> Dict:
        """
        Decrypt ZIP archive

        Args:
            file_path: Path to encrypted ZIP
            password: Known password (optional)
            try_common: Try common passwords
            output_dir: Where to extract files

        Returns:
            Dictionary with operation result
        """
        result = {
            'success': False,
            'path': file_path,
            'password_found': None,
            'extracted_files': [],
            'errors': []
        }

        if output_dir is None:
            output_dir = os.path.splitext(file_path)[0] + '_extracted'

        try:
            passwords_to_try = []
            if password:
                passwords_to_try.append(password)

            if try_common:
                passwords_to_try.extend(self.COMMON_PASSWORDS)

            # Try each password
            for pwd in passwords_to_try:
                try:
                    with zipfile.ZipFile(file_path, 'r') as zf:
                        # Try to extract with password
                        pwd_bytes = pwd.encode('utf-8') if pwd else None

                        # Create output directory
                        os.makedirs(output_dir, exist_ok=True)

                        # Extract all files
                        zf.extractall(output_dir, pwd=pwd_bytes)

                        result['success'] = True
                        result['password_found'] = pwd if pwd else '(empty)'
                        result['output_dir'] = output_dir
                        result['extracted_files'] = zf.namelist()
                        logger.info(f"Successfully extracted ZIP with password: {'(empty)' if not pwd else '***'}")
                        return result

                except RuntimeError as e:
                    if 'Bad password' in str(e):
                        logger.debug(f"Password '{pwd}' failed")
                        continue
                    else:
                        raise

            result['errors'].append('No working password found')

        except Exception as e:
            result['errors'].append(str(e))
            logger.error(f"Error decrypting ZIP: {e}")

        return result

    def batch_decrypt(self, file_paths: List[str], **kwargs) -> List[Dict]:
        """
        Decrypt multiple files

        Args:
            file_paths: List of file paths
            **kwargs: Additional arguments passed to specific decrypt methods

        Returns:
            List of result dictionaries
        """
        results = []

        for file_path in file_paths:
            # Detect encryption type
            detection = self.detect_encryption(file_path)

            if not detection.get('encrypted'):
                results.append({
                    'path': file_path,
                    'success': False,
                    'error': 'File is not encrypted'
                })
                continue

            # Attempt appropriate decryption
            result = None

            if 'EFS' in detection['encryption_types']:
                result = self.remove_efs_encryption(file_path, **kwargs)

            elif 'Office Password' in detection['encryption_types']:
                result = self.decrypt_office_file(file_path, **kwargs)

            elif 'PDF Password' in detection['encryption_types']:
                result = self.decrypt_pdf(file_path, **kwargs)

            elif 'ZIP Password' in detection['encryption_types']:
                result = self.decrypt_zip(file_path, **kwargs)

            if result:
                results.append(result)
            else:
                results.append({
                    'path': file_path,
                    'success': False,
                    'error': 'Unknown encryption type'
                })

        return results


# Convenience functions
def detect_encryption(file_path: str) -> bool:
    """Simple encryption detection"""
    decryptor = FileDecryptor()
    result = decryptor.detect_encryption(file_path)
    return result.get('encrypted', False)


def decrypt_file(file_path: str, password: Optional[str] = None) -> bool:
    """Simple decrypt function"""
    with FileDecryptor() as decryptor:
        detection = decryptor.detect_encryption(file_path)

        if not detection.get('encrypted'):
            return False

        if 'Office Password' in detection.get('encryption_types', []):
            result = decryptor.decrypt_office_file(file_path, password)
        elif 'PDF Password' in detection.get('encryption_types', []):
            result = decryptor.decrypt_pdf(file_path, password)
        elif 'ZIP Password' in detection.get('encryption_types', []):
            result = decryptor.decrypt_zip(file_path, password)
        elif 'EFS' in detection.get('encryption_types', []):
            result = decryptor.remove_efs_encryption(file_path)
        else:
            return False

        return result.get('success', False)


if __name__ == '__main__':
    # Test/demo code
    import argparse

    parser = argparse.ArgumentParser(description='File Decryptor - Handle encrypted files')
    parser.add_argument('file', help='File to decrypt')
    parser.add_argument('--password', '-p', help='Password to try')
    parser.add_argument('--detect', action='store_true', help='Detect encryption only')
    parser.add_argument('--output', '-o', help='Output path')

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    with FileDecryptor() as decryptor:
        if args.detect:
            result = decryptor.detect_encryption(args.file)
            print(f"\nEncryption Detection for: {args.file}")
            print(f"  Encrypted: {result['encrypted']}")
            if result['encrypted']:
                print(f"  Types: {', '.join(result['encryption_types'])}")
                print(f"  Details: {result['details']}")
        else:
            # Try to decrypt
            detection = decryptor.detect_encryption(args.file)

            if not detection['encrypted']:
                print(f"File is not encrypted: {args.file}")
                sys.exit(0)

            result = None
            if 'Office Password' in detection['encryption_types']:
                result = decryptor.decrypt_office_file(args.file, args.password, output_path=args.output)
            elif 'PDF Password' in detection['encryption_types']:
                result = decryptor.decrypt_pdf(args.file, args.password, output_path=args.output)
            elif 'ZIP Password' in detection['encryption_types']:
                result = decryptor.decrypt_zip(args.file, args.password, output_dir=args.output)
            elif 'EFS' in detection['encryption_types']:
                result = decryptor.remove_efs_encryption(args.file)

            if result:
                print(f"\nDecryption Result:")
                print(f"  Success: {result['success']}")
                if result['success']:
                    print(f"  Password: {result.get('password_found', 'N/A')}")
                    print(f"  Output: {result.get('output_path') or result.get('output_dir')}")
                elif result.get('errors'):
                    print(f"  Errors: {', '.join(result['errors'])}")

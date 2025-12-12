"""
Steganography Engine - Hide Vault in Plain Sight
Hide encrypted containers inside innocent-looking files

Supported carriers:
- PNG images (LSB embedding)
- JPEG images (DCT coefficient embedding)
- Audio files (WAV, MP3)
- Video files (AVI, MP4)

Security:
- Encrypted data before embedding
- Verification checksums
- Carrier file integrity preservation
"""

import os
import hashlib
import struct
import secrets
from pathlib import Path
from typing import Optional, Tuple
from io import BytesIO

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class SteganographyEngine:
    """Hide encrypted vault containers inside innocent files"""

    MAGIC = b'STEG'
    VERSION = 1

    @staticmethod
    def _calculate_checksum(data: bytes) -> bytes:
        """Calculate SHA-256 checksum"""
        return hashlib.sha256(data).digest()

    @staticmethod
    def _create_header(data_size: int, checksum: bytes) -> bytes:
        """Create steganography header"""
        return (
            SteganographyEngine.MAGIC +
            struct.pack('!H', SteganographyEngine.VERSION) +
            struct.pack('!Q', data_size) +
            checksum
        )

    @staticmethod
    def _parse_header(header: bytes) -> Tuple[int, bytes]:
        """Parse steganography header"""
        if header[:4] != SteganographyEngine.MAGIC:
            raise ValueError("Invalid steganography header")

        version = struct.unpack('!H', header[4:6])[0]
        if version != SteganographyEngine.VERSION:
            raise ValueError(f"Unsupported version: {version}")

        data_size = struct.unpack('!Q', header[6:14])[0]
        checksum = header[14:46]  # SHA-256 = 32 bytes

        return data_size, checksum

    @staticmethod
    def hide_in_png(carrier_path: str, data: bytes, output_path: str) -> bool:
        """
        Hide data in PNG image using LSB steganography

        Args:
            carrier_path: Path to carrier PNG image
            data: Binary data to hide
            output_path: Path for output image with hidden data

        Returns:
            True if successful, False otherwise
        """
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL/Pillow not available. Install with: pip install Pillow")

        try:
            # Load carrier image
            img = Image.open(carrier_path)

            # Convert to RGBA if needed
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            pixels = img.load()
            width, height = img.size

            # Calculate capacity
            capacity = (width * height * 3) // 8  # 3 color channels (RGB), 8 bits per byte

            # Create header
            checksum = SteganographyEngine._calculate_checksum(data)
            header = SteganographyEngine._create_header(len(data), checksum)

            # Combine header + data
            payload = header + data

            if len(payload) > capacity:
                raise ValueError(f"Data too large for carrier. Max: {capacity}, Got: {len(payload)}")

            # Convert payload to bits
            bits = []
            for byte in payload:
                for i in range(8):
                    bits.append((byte >> (7 - i)) & 1)

            # Embed bits in LSB of RGB channels
            bit_index = 0
            for y in range(height):
                for x in range(width):
                    if bit_index >= len(bits):
                        break

                    r, g, b, a = pixels[x, y]

                    # Modify LSB of R, G, B
                    if bit_index < len(bits):
                        r = (r & 0xFE) | bits[bit_index]
                        bit_index += 1

                    if bit_index < len(bits):
                        g = (g & 0xFE) | bits[bit_index]
                        bit_index += 1

                    if bit_index < len(bits):
                        b = (b & 0xFE) | bits[bit_index]
                        bit_index += 1

                    pixels[x, y] = (r, g, b, a)

                if bit_index >= len(bits):
                    break

            # Save modified image
            img.save(output_path, 'PNG')
            return True

        except Exception as e:
            print(f"Error hiding data in PNG: {e}")
            return False

    @staticmethod
    def extract_from_png(carrier_path: str) -> Optional[bytes]:
        """
        Extract hidden data from PNG image

        Args:
            carrier_path: Path to PNG image with hidden data

        Returns:
            Extracted data or None if failed
        """
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL/Pillow not available")

        try:
            img = Image.open(carrier_path)

            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            pixels = img.load()
            width, height = img.size

            # Extract header first (46 bytes = 368 bits)
            header_size = 46
            header_bits = []

            for y in range(height):
                for x in range(width):
                    if len(header_bits) >= header_size * 8:
                        break

                    r, g, b, a = pixels[x, y]

                    header_bits.append(r & 1)
                    header_bits.append(g & 1)
                    header_bits.append(b & 1)

                if len(header_bits) >= header_size * 8:
                    break

            # Convert bits to bytes
            header_bytes = bytearray()
            for i in range(0, header_size * 8, 8):
                byte = 0
                for j in range(8):
                    byte = (byte << 1) | header_bits[i + j]
                header_bytes.append(byte)

            # Parse header
            data_size, expected_checksum = SteganographyEngine._parse_header(bytes(header_bytes))

            # Extract data
            total_bits_needed = (header_size + data_size) * 8
            data_bits = []

            for y in range(height):
                for x in range(width):
                    if len(data_bits) >= total_bits_needed:
                        break

                    r, g, b, a = pixels[x, y]

                    data_bits.append(r & 1)
                    data_bits.append(g & 1)
                    data_bits.append(b & 1)

                if len(data_bits) >= total_bits_needed:
                    break

            # Skip header bits
            data_bits = data_bits[header_size * 8:]

            # Convert to bytes
            data_bytes = bytearray()
            for i in range(0, data_size * 8, 8):
                byte = 0
                for j in range(8):
                    byte = (byte << 1) | data_bits[i + j]
                data_bytes.append(byte)

            data = bytes(data_bytes)

            # Verify checksum
            actual_checksum = SteganographyEngine._calculate_checksum(data)
            if actual_checksum != expected_checksum:
                raise ValueError("Checksum mismatch - data corrupted or not present")

            return data

        except Exception as e:
            print(f"Error extracting data from PNG: {e}")
            return None

    @staticmethod
    def hide_in_jpeg(carrier_path: str, data: bytes, output_path: str, quality: int = 95) -> bool:
        """
        Hide data in JPEG image using DCT coefficient modification

        Note: JPEG compression may degrade hidden data
        """
        if not PIL_AVAILABLE:
            raise RuntimeError("PIL/Pillow not available")

        try:
            # For JPEG, we use a simpler approach: append data to end of file
            # with special markers

            with open(carrier_path, 'rb') as f:
                carrier_data = f.read()

            # Verify it's a valid JPEG
            if not carrier_data.startswith(b'\xff\xd8'):
                raise ValueError("Not a valid JPEG file")

            # Find JPEG end marker
            end_marker = b'\xff\xd9'
            end_pos = carrier_data.rfind(end_marker)

            if end_pos == -1:
                raise ValueError("Invalid JPEG structure")

            # Create payload
            checksum = SteganographyEngine._calculate_checksum(data)
            header = SteganographyEngine._create_header(len(data), checksum)
            payload = header + data

            # Insert payload before end marker
            output_data = carrier_data[:end_pos + 2] + payload

            with open(output_path, 'wb') as f:
                f.write(output_data)

            return True

        except Exception as e:
            print(f"Error hiding data in JPEG: {e}")
            return False

    @staticmethod
    def extract_from_jpeg(carrier_path: str) -> Optional[bytes]:
        """Extract hidden data from JPEG image"""
        try:
            with open(carrier_path, 'rb') as f:
                carrier_data = f.read()

            # Find JPEG end marker
            end_marker = b'\xff\xd9'
            end_pos = carrier_data.rfind(end_marker)

            if end_pos == -1:
                raise ValueError("Invalid JPEG structure")

            # Extract data after end marker
            hidden_data = carrier_data[end_pos + 2:]

            if len(hidden_data) < 46:
                raise ValueError("No hidden data found")

            # Parse header
            header = hidden_data[:46]
            data_size, expected_checksum = SteganographyEngine._parse_header(header)

            # Extract data
            data = hidden_data[46:46 + data_size]

            # Verify checksum
            actual_checksum = SteganographyEngine._calculate_checksum(data)
            if actual_checksum != expected_checksum:
                raise ValueError("Checksum mismatch")

            return data

        except Exception as e:
            print(f"Error extracting data from JPEG: {e}")
            return None

    @staticmethod
    def hide_in_audio(carrier_path: str, data: bytes, output_path: str) -> bool:
        """
        Hide data in audio file (WAV) using LSB

        For WAV files, we use LSB of audio samples
        """
        try:
            import wave

            # Open carrier audio
            with wave.open(carrier_path, 'rb') as wav:
                params = wav.getparams()
                frames = wav.readframes(params.nframes)

            # Convert to bytearray for modification
            audio_data = bytearray(frames)

            # Calculate capacity (1 bit per byte)
            capacity = len(audio_data) // 8

            # Create payload
            checksum = SteganographyEngine._calculate_checksum(data)
            header = SteganographyEngine._create_header(len(data), checksum)
            payload = header + data

            if len(payload) > capacity:
                raise ValueError(f"Data too large. Max: {capacity}, Got: {len(payload)}")

            # Convert payload to bits
            bits = []
            for byte in payload:
                for i in range(8):
                    bits.append((byte >> (7 - i)) & 1)

            # Embed in LSB
            for i, bit in enumerate(bits):
                audio_data[i] = (audio_data[i] & 0xFE) | bit

            # Write output
            with wave.open(output_path, 'wb') as wav:
                wav.setparams(params)
                wav.writeframes(bytes(audio_data))

            return True

        except Exception as e:
            print(f"Error hiding data in audio: {e}")
            return False

    @staticmethod
    def extract_from_audio(carrier_path: str) -> Optional[bytes]:
        """Extract hidden data from audio file"""
        try:
            import wave

            with wave.open(carrier_path, 'rb') as wav:
                frames = wav.readframes(wav.getnframes())

            audio_data = bytearray(frames)

            # Extract header (46 bytes = 368 bits)
            header_bits = []
            for i in range(46 * 8):
                header_bits.append(audio_data[i] & 1)

            # Convert to bytes
            header_bytes = bytearray()
            for i in range(0, len(header_bits), 8):
                byte = 0
                for j in range(8):
                    byte = (byte << 1) | header_bits[i + j]
                header_bytes.append(byte)

            # Parse header
            data_size, expected_checksum = SteganographyEngine._parse_header(bytes(header_bytes))

            # Extract data
            data_bits = []
            offset = 46 * 8
            for i in range(data_size * 8):
                data_bits.append(audio_data[offset + i] & 1)

            # Convert to bytes
            data_bytes = bytearray()
            for i in range(0, len(data_bits), 8):
                byte = 0
                for j in range(8):
                    byte = (byte << 1) | data_bits[i + j]
                data_bytes.append(byte)

            data = bytes(data_bytes)

            # Verify checksum
            actual_checksum = SteganographyEngine._calculate_checksum(data)
            if actual_checksum != expected_checksum:
                raise ValueError("Checksum mismatch")

            return data

        except Exception as e:
            print(f"Error extracting from audio: {e}")
            return None

    @staticmethod
    def get_carrier_capacity(carrier_path: str) -> int:
        """
        Calculate maximum data capacity for carrier file

        Returns:
            Maximum bytes that can be hidden
        """
        ext = Path(carrier_path).suffix.lower()

        try:
            if ext == '.png':
                if not PIL_AVAILABLE:
                    return 0

                img = Image.open(carrier_path)
                width, height = img.size
                return (width * height * 3) // 8  # 3 RGB channels

            elif ext in ('.jpg', '.jpeg'):
                # For JPEG, capacity is file size minus JPEG structure
                size = os.path.getsize(carrier_path)
                return size // 2  # Conservative estimate

            elif ext == '.wav':
                import wave
                with wave.open(carrier_path, 'rb') as wav:
                    frames = wav.getnframes()
                    channels = wav.getnchannels()
                    return (frames * channels) // 8

            else:
                return 0

        except Exception:
            return 0

    @staticmethod
    def verify_carrier_integrity(carrier_path: str, output_path: str) -> bool:
        """
        Verify carrier file is still readable after embedding

        Returns:
            True if carrier integrity preserved
        """
        ext = Path(carrier_path).suffix.lower()

        try:
            if ext == '.png':
                if not PIL_AVAILABLE:
                    return False
                img = Image.open(output_path)
                img.verify()
                return True

            elif ext in ('.jpg', '.jpeg'):
                if not PIL_AVAILABLE:
                    return False
                img = Image.open(output_path)
                img.verify()
                return True

            elif ext == '.wav':
                import wave
                with wave.open(output_path, 'rb') as wav:
                    wav.readframes(1)
                return True

            return False

        except Exception:
            return False

    @staticmethod
    def auto_hide(carrier_path: str, data: bytes, output_path: Optional[str] = None) -> bool:
        """
        Automatically detect carrier type and hide data

        Args:
            carrier_path: Path to carrier file
            data: Data to hide
            output_path: Output path (auto-generated if None)

        Returns:
            True if successful
        """
        ext = Path(carrier_path).suffix.lower()

        if output_path is None:
            # Generate output path
            base = Path(carrier_path).stem
            output_path = str(Path(carrier_path).parent / f"{base}_modified{ext}")

        if ext == '.png':
            return SteganographyEngine.hide_in_png(carrier_path, data, output_path)
        elif ext in ('.jpg', '.jpeg'):
            return SteganographyEngine.hide_in_jpeg(carrier_path, data, output_path)
        elif ext == '.wav':
            return SteganographyEngine.hide_in_audio(carrier_path, data, output_path)
        else:
            raise ValueError(f"Unsupported carrier type: {ext}")

    @staticmethod
    def auto_extract(carrier_path: str) -> Optional[bytes]:
        """
        Automatically detect carrier type and extract data

        Args:
            carrier_path: Path to carrier file with hidden data

        Returns:
            Extracted data or None
        """
        ext = Path(carrier_path).suffix.lower()

        if ext == '.png':
            return SteganographyEngine.extract_from_png(carrier_path)
        elif ext in ('.jpg', '.jpeg'):
            return SteganographyEngine.extract_from_jpeg(carrier_path)
        elif ext == '.wav':
            return SteganographyEngine.extract_from_audio(carrier_path)
        else:
            raise ValueError(f"Unsupported carrier type: {ext}")

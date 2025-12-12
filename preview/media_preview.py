"""
Media preview for audio and video files.

Supports:
- Audio/video duration extraction
- Video thumbnail generation (with ffmpeg)
- Audio waveform visualization (optional)
- Codec and format information
"""

import os
import logging
import subprocess
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class MediaPreviewer:
    """Generate previews for audio and video files."""

    def __init__(self):
        """Initialize media previewer."""
        self._mutagen_available = False
        self._ffmpeg_available = False

        try:
            import mutagen
            self._mutagen_available = True
        except ImportError:
            logger.debug("Mutagen not available for media metadata")

        # Check if ffmpeg is available
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            self._ffmpeg_available = result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.debug("ffmpeg not available for video thumbnails")

    def is_supported(self, file_path: str) -> bool:
        """
        Check if file format is supported.

        Args:
            file_path: Path to file

        Returns:
            True if format is supported
        """
        ext = Path(file_path).suffix.lower()
        audio_formats = {'.mp3', '.flac', '.ogg', '.m4a', '.wav', '.wma', '.aac', '.opus'}
        video_formats = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
        return ext in audio_formats or ext in video_formats

    def generate_preview(self, file_path: str) -> Dict[str, Any]:
        """
        Generate media preview.

        Args:
            file_path: Path to media file

        Returns:
            Dictionary containing preview data
        """
        if not os.path.exists(file_path):
            return {'error': 'File not found'}

        ext = Path(file_path).suffix.lower()

        # Determine if audio or video
        audio_formats = {'.mp3', '.flac', '.ogg', '.m4a', '.wav', '.wma', '.aac', '.opus'}
        video_formats = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}

        if ext in audio_formats:
            return self._preview_audio(file_path)
        elif ext in video_formats:
            return self._preview_video(file_path)
        else:
            return {'error': 'Unsupported media format'}

    def _preview_audio(self, file_path: str) -> Dict[str, Any]:
        """
        Generate audio preview.

        Args:
            file_path: Path to audio file

        Returns:
            Dictionary with audio preview data
        """
        result = {
            'type': 'audio',
            'file_size': os.path.getsize(file_path),
        }

        if self._mutagen_available:
            try:
                import mutagen

                audio = mutagen.File(file_path)
                if audio is not None:
                    # Duration
                    if hasattr(audio.info, 'length'):
                        result['duration'] = self._format_duration(audio.info.length)
                        result['duration_seconds'] = audio.info.length

                    # Bitrate
                    if hasattr(audio.info, 'bitrate'):
                        result['bitrate'] = f"{audio.info.bitrate // 1000} kbps"
                        result['bitrate_value'] = audio.info.bitrate

                    # Sample rate
                    if hasattr(audio.info, 'sample_rate'):
                        result['sample_rate'] = f"{audio.info.sample_rate} Hz"
                        result['sample_rate_value'] = audio.info.sample_rate

                    # Channels
                    if hasattr(audio.info, 'channels'):
                        result['channels'] = audio.info.channels

                    # Tags/Metadata
                    if audio.tags:
                        tags = {}
                        for key, value in audio.tags.items():
                            if isinstance(value, list):
                                tags[key] = ', '.join(str(v) for v in value)
                            else:
                                tags[key] = str(value)

                        # Extract common fields
                        for field in ['title', 'artist', 'album', 'date', 'genre', 'albumartist']:
                            for tag_key, tag_value in tags.items():
                                if field in tag_key.lower():
                                    result[field] = tag_value
                                    break

                        result['tags'] = tags

            except Exception as e:
                logger.error(f"Error extracting audio metadata: {e}")

        # Fallback to ffprobe if mutagen failed
        if 'duration' not in result and self._ffmpeg_available:
            ffprobe_data = self._get_ffprobe_data(file_path)
            if ffprobe_data:
                result.update(ffprobe_data)

        return result

    def _preview_video(self, file_path: str) -> Dict[str, Any]:
        """
        Generate video preview.

        Args:
            file_path: Path to video file

        Returns:
            Dictionary with video preview data
        """
        result = {
            'type': 'video',
            'file_size': os.path.getsize(file_path),
        }

        # Try mutagen first
        if self._mutagen_available:
            try:
                import mutagen

                video = mutagen.File(file_path)
                if video is not None:
                    if hasattr(video.info, 'length'):
                        result['duration'] = self._format_duration(video.info.length)
                        result['duration_seconds'] = video.info.length

                    if hasattr(video.info, 'width'):
                        result['width'] = video.info.width
                    if hasattr(video.info, 'height'):
                        result['height'] = video.info.height
                        if 'width' in result:
                            result['resolution'] = f"{result['width']}x{result['height']}"

                    if hasattr(video.info, 'bitrate'):
                        result['bitrate'] = f"{video.info.bitrate // 1000} kbps"
                        result['bitrate_value'] = video.info.bitrate

            except Exception as e:
                logger.debug(f"Error extracting video metadata with mutagen: {e}")

        # Use ffprobe for more detailed info
        if self._ffmpeg_available:
            ffprobe_data = self._get_ffprobe_data(file_path)
            if ffprobe_data:
                result.update(ffprobe_data)

        return result

    def _get_ffprobe_data(self, file_path: str) -> Dict[str, Any]:
        """
        Extract media info using ffprobe.

        Args:
            file_path: Path to media file

        Returns:
            Dictionary with media info
        """
        if not self._ffmpeg_available:
            return {}

        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)

                info = {}

                # Format info
                if 'format' in data:
                    fmt = data['format']
                    if 'duration' in fmt:
                        duration = float(fmt['duration'])
                        info['duration'] = self._format_duration(duration)
                        info['duration_seconds'] = duration

                    if 'bit_rate' in fmt:
                        bitrate = int(fmt['bit_rate'])
                        info['bitrate'] = f"{bitrate // 1000} kbps"
                        info['bitrate_value'] = bitrate

                    if 'tags' in fmt:
                        tags = fmt['tags']
                        for key in ['title', 'artist', 'album', 'date', 'genre']:
                            if key in tags:
                                info[key] = tags[key]

                # Stream info
                if 'streams' in data:
                    for stream in data['streams']:
                        codec_type = stream.get('codec_type')

                        if codec_type == 'video':
                            info['video_codec'] = stream.get('codec_name', 'unknown')
                            if 'width' in stream:
                                info['width'] = stream['width']
                            if 'height' in stream:
                                info['height'] = stream['height']
                            if 'width' in info and 'height' in info:
                                info['resolution'] = f"{info['width']}x{info['height']}"

                            # Frame rate
                            if 'r_frame_rate' in stream:
                                try:
                                    num, den = stream['r_frame_rate'].split('/')
                                    fps = float(num) / float(den)
                                    info['fps'] = round(fps, 2)
                                except Exception:
                                    pass

                        elif codec_type == 'audio':
                            info['audio_codec'] = stream.get('codec_name', 'unknown')
                            if 'sample_rate' in stream:
                                info['sample_rate'] = f"{stream['sample_rate']} Hz"
                                info['sample_rate_value'] = int(stream['sample_rate'])
                            if 'channels' in stream:
                                info['channels'] = stream['channels']

                return info

        except Exception as e:
            logger.error(f"Error running ffprobe: {e}")

        return {}

    def generate_video_thumbnail(
        self,
        file_path: str,
        output_path: str,
        time_offset: float = 1.0
    ) -> bool:
        """
        Generate video thumbnail using ffmpeg.

        Args:
            file_path: Path to video file
            output_path: Path to save thumbnail
            time_offset: Time offset in seconds for thumbnail

        Returns:
            True if successful
        """
        if not self._ffmpeg_available:
            return False

        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            cmd = [
                'ffmpeg',
                '-ss', str(time_offset),
                '-i', file_path,
                '-vframes', '1',
                '-q:v', '2',
                '-y',  # Overwrite output file
                output_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            return result.returncode == 0 and os.path.exists(output_path)

        except Exception as e:
            logger.error(f"Error generating video thumbnail: {e}")
            return False

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """
        Format duration in seconds to HH:MM:SS or MM:SS.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted duration string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

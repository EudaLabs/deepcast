import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
import time
import re
import hashlib
import asyncio
from concurrent.futures import ThreadPoolExecutor

import requests
import fal
from pydub import AudioSegment
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..models.audio_config import (
    AudioConfig, BackgroundMusicType, VoiceEmotion,
    MUSIC_URLS, EMOTION_MODIFIERS, ALLOWED_FORMATS
)

logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
MAX_TRANSCRIPT_LENGTH = 10000  # Maximum characters for transcript
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB max file size
CHUNK_SIZE = 8192  # 8KB chunks for downloading
MAX_CONCURRENT_DOWNLOADS = 3
DOWNLOAD_TIMEOUT = 30  # seconds
API_TIMEOUT = 300  # 5 minutes
TEMP_DIR_PREFIX = "deepcast_"

class AudioProcessingError(Exception):
    """Custom exception for audio processing errors."""
    pass

class AudioService:
    """Service for audio processing and generation."""
    
    _session: Optional[requests.Session] = None
    _executor: Optional[ThreadPoolExecutor] = None
    
    @classmethod
    def _get_session(cls) -> requests.Session:
        """Get or create a requests session with retry configuration."""
        if cls._session is None:
            retry_strategy = Retry(
                total=MAX_RETRIES,
                backoff_factor=0.5,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            cls._session = requests.Session()
            cls._session.mount("http://", adapter)
            cls._session.mount("https://", adapter)
        return cls._session
    
    @classmethod
    def _get_executor(cls) -> ThreadPoolExecutor:
        """Get or create thread pool executor."""
        if cls._executor is None:
            cls._executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_DOWNLOADS)
        return cls._executor
    
    @staticmethod
    def _validate_transcript(transcript: str) -> bool:
        """Validate transcript length and content."""
        if not transcript or not transcript.strip():
            logger.error("Transcript is empty")
            return False
        if len(transcript) > MAX_TRANSCRIPT_LENGTH:
            logger.error(f"Transcript exceeds maximum length of {MAX_TRANSCRIPT_LENGTH} characters")
            return False
        # Check for potentially harmful content
        if re.search(r"[<>]|javascript:|data:", transcript, re.IGNORECASE):
            logger.error("Transcript contains potentially harmful content")
            return False
        return True

    @staticmethod
    def _validate_config(config: AudioConfig) -> bool:
        """Validate audio configuration."""
        try:
            if not config.speakers:
                logger.error("No speakers configured")
                return False
            if not 0.0 <= config.music_volume <= 1.0:
                logger.error("Invalid music volume (must be between 0.0 and 1.0)")
                return False
            if config.output_format.lower() not in ALLOWED_FORMATS:
                logger.error(f"Invalid output format (must be one of {', '.join(ALLOWED_FORMATS)})")
                return False
            if not config.validate_voice_compatibility():
                logger.error("Incompatible voice languages detected")
                return False
            return True
        except Exception as e:
            logger.error(f"Invalid audio configuration: {str(e)}")
            return False

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe file operations."""
        # Remove or replace unsafe characters
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Ensure filename is not too long
        return safe_filename[:255]

    @staticmethod
    def _compute_file_hash(file_path: str) -> str:
        """Compute SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(CHUNK_SIZE), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    @classmethod
    async def _download_file(cls, url: str, target_path: str) -> bool:
        """Download a file from URL with size and content type validation."""
        try:
            session = cls._get_session()
            
            # Validate URL
            if not url.startswith(('http://', 'https://')):
                logger.error("Invalid URL scheme")
                return False
                
            # Make HEAD request first to check content type and size
            head_response = await asyncio.get_event_loop().run_in_executor(
                cls._get_executor(),
                lambda: session.head(url, timeout=DOWNLOAD_TIMEOUT)
            )
            head_response.raise_for_status()
            
            # Validate content type
            content_type = head_response.headers.get('content-type', '')
            if not content_type.startswith('audio/') and not content_type.startswith('application/octet-stream'):
                logger.error(f"Invalid content type: {content_type}")
                return False
                
            # Check file size
            content_length = int(head_response.headers.get('content-length', 0))
            if content_length > MAX_FILE_SIZE:
                logger.error(f"File size exceeds maximum limit of {MAX_FILE_SIZE} bytes")
                return False
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # Download with progress tracking
            response = await asyncio.get_event_loop().run_in_executor(
                cls._get_executor(),
                lambda: session.get(url, stream=True, timeout=DOWNLOAD_TIMEOUT)
            )
            response.raise_for_status()
            
            downloaded_size = 0
            temp_path = f"{target_path}.tmp"
            
            try:
                with open(temp_path, 'wb') as f:
                    async for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                        downloaded_size += len(chunk)
                        if downloaded_size > MAX_FILE_SIZE:
                            logger.error("File size exceeded limit during download")
                            return False
                        f.write(chunk)
                
                # Verify file integrity
                if content_length > 0 and downloaded_size != content_length:
                    logger.error("Downloaded file size mismatch")
                    return False
                
                # Move temp file to target path
                os.replace(temp_path, target_path)
                return True
                
            except Exception as e:
                logger.error(f"Error writing file: {str(e)}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return False
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Download failed: {str(e)}")
            return False
        except OSError as e:
            logger.error(f"File system error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during download: {str(e)}")
            return False

    @classmethod
    async def _make_tts_request(cls, transcript: str, config: AudioConfig, retry: int = 0) -> Optional[Dict[str, Any]]:
        """Make TTS API request with retry logic and error handling."""
        try:
            # Validate inputs
            if not cls._validate_transcript(transcript):
                return None
            if not cls._validate_config(config):
                return None
            
            # Prepare speakers with emotion modifiers
            speakers = []
            for speaker_id, speaker_config in config.speakers.items():
                modifiers = EMOTION_MODIFIERS.get(speaker_config.emotion, EMOTION_MODIFIERS[VoiceEmotion.NEUTRAL])
                speakers.append({
                    "voice": speaker_config.voice,
                    "turn_prefix": speaker_config.turn_prefix,
                    "stability": modifiers["stability"],
                    "similarity_boost": modifiers["similarity_boost"]
                })
            
            # Make API request with timeout
            return await asyncio.get_event_loop().run_in_executor(
                cls._get_executor(),
                lambda: fal.subscribe(
                    "fal-ai/playht/tts/ldm",
                    {
                        "input": transcript,
                        "voices": speakers
                    },
                    timeout=API_TIMEOUT
                )
            )
        except fal.exceptions.SubscriptionError as e:
            logger.error(f"FAL API error: {str(e)}")
        except Exception as e:
            logger.error(f"TTS request failed: {str(e)}")
            
        if retry < MAX_RETRIES:
            logger.warning(f"Attempt {retry + 1} failed, retrying in {RETRY_DELAY}s")
            await asyncio.sleep(RETRY_DELAY)
            # Try fallback voices on subsequent retries
            if retry > 0:
                for speaker in config.speakers.values():
                    if speaker.fallback_voice:
                        speaker.voice, speaker.fallback_voice = speaker.fallback_voice, speaker.voice
            return await cls._make_tts_request(transcript, config, retry + 1)
            
        logger.error(f"Failed to generate audio after {MAX_RETRIES} attempts")
        return None

    @classmethod
    async def _process_audio(cls, voice_url: str, config: AudioConfig) -> Optional[str]:
        """Process audio with background music and effects."""
        try:
            with tempfile.TemporaryDirectory(prefix=TEMP_DIR_PREFIX) as temp_dir:
                # Download voice audio
                voice_path = os.path.join(temp_dir, "voice.mp3")
                if not await cls._download_file(voice_url, voice_path):
                    return None
                
                try:
                    # Load voice audio
                    voice_audio = AudioSegment.from_mp3(voice_path)
                    
                    # Add background music if specified
                    if config.background_music != BackgroundMusicType.NONE:
                        music_url = MUSIC_URLS.get(config.background_music)
                        if not music_url:
                            logger.error(f"Invalid background music type: {config.background_music}")
                            return None
                            
                        music_path = os.path.join(temp_dir, "music.mp3")
                        
                        if await cls._download_file(music_url, music_path):
                            try:
                                # Load and adjust music
                                music = AudioSegment.from_mp3(music_path)
                                
                                # Loop music if needed
                                while len(music) < len(voice_audio):
                                    music = music + music
                                
                                # Trim music to match voice length
                                music = music[:len(voice_audio)]
                                
                                # Adjust volume and overlay
                                music = music - (20 - (20 * config.music_volume))
                                voice_audio = voice_audio.overlay(music)
                            except Exception as e:
                                logger.error(f"Failed to process background music: {str(e)}")
                    
                    # Save final audio
                    output_format = config.output_format.lower()
                    if output_format not in ALLOWED_FORMATS:
                        output_format = "mp3"  # Default to MP3 if invalid format
                        
                    output_path = os.path.join(temp_dir, f"output.{output_format}")
                    voice_audio.export(output_path, format=output_format)
                    
                    # Save locally if requested
                    if config.save_locally:
                        try:
                            save_dir = Path("output")
                            save_dir.mkdir(exist_ok=True)
                            timestamp = time.strftime("%Y%m%d_%H%M%S")
                            filename = cls._sanitize_filename(f"podcast_{timestamp}.{output_format}")
                            save_path = save_dir / filename
                            
                            # Verify output directory is writable
                            if not os.access(str(save_dir), os.W_OK):
                                raise AudioProcessingError("Output directory is not writable")
                            
                            # Export with file hash verification
                            voice_audio.export(str(save_path), format=output_format)
                            
                            # Verify file integrity
                            if not os.path.exists(str(save_path)):
                                raise AudioProcessingError("Failed to save audio file")
                                
                            logger.info(f"Audio saved locally: {save_path}")
                        except Exception as e:
                            logger.error(f"Failed to save audio locally: {str(e)}")
                    
                    # Return the processed audio URL
                    return voice_url  # For now, return original URL
                    
                except Exception as e:
                    logger.error(f"Failed to process audio: {str(e)}")
                    return None
                    
        except Exception as e:
            logger.error(f"Unexpected error in audio processing: {str(e)}")
            return None

    @classmethod
    async def generate_audio(cls, transcript: str, config: AudioConfig) -> Optional[str]:
        """Generate and process audio with the given configuration."""
        try:
            # Validate inputs
            if not cls._validate_transcript(transcript):
                return None
            if not cls._validate_config(config):
                return None
                
            # Generate base audio
            result = await cls._make_tts_request(transcript, config)
            if not result or 'audio' not in result or 'url' not in result['audio']:
                logger.error("Invalid TTS API response")
                return None
                
            # Process audio with effects and music
            return await cls._process_audio(result['audio']['url'], config)
            
        except Exception as e:
            logger.error(f"Failed to generate audio: {str(e)}")
            return None
        finally:
            # Clean up resources
            if cls._executor is not None:
                cls._executor.shutdown(wait=True)
                cls._executor = None
            if cls._session is not None:
                cls._session.close()
                cls._session = None 
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
import time
import re

import requests
import fal
from pydub import AudioSegment

from ..models.audio_config import (
    AudioConfig, BackgroundMusicType, VoiceEmotion,
    MUSIC_URLS, EMOTION_MODIFIERS
)

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
MAX_TRANSCRIPT_LENGTH = 10000  # Maximum characters for transcript
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB max file size
ALLOWED_FORMATS = {"mp3", "wav", "ogg"}  # Allowed audio formats

class AudioService:
    """Service for audio processing and generation."""
    
    @staticmethod
    def _validate_transcript(transcript: str) -> bool:
        """Validate transcript length and content."""
        if not transcript or not transcript.strip():
            logger.error("Transcript is empty")
            return False
        if len(transcript) > MAX_TRANSCRIPT_LENGTH:
            logger.error(f"Transcript exceeds maximum length of {MAX_TRANSCRIPT_LENGTH} characters")
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
    def _download_file(url: str, target_path: str) -> bool:
        """Download a file from URL with size and content type validation."""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Validate content type
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('audio/') and not content_type.startswith('application/octet-stream'):
                logger.error(f"Invalid content type: {content_type}")
                return False
                
            # Check file size
            content_length = int(response.headers.get('content-length', 0))
            if content_length > MAX_FILE_SIZE:
                logger.error(f"File size exceeds maximum limit of {MAX_FILE_SIZE} bytes")
                return False
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # Download with progress tracking
            downloaded_size = 0
            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    downloaded_size += len(chunk)
                    if downloaded_size > MAX_FILE_SIZE:
                        logger.error("File size exceeded limit during download")
                        f.close()
                        os.remove(target_path)
                        return False
                    f.write(chunk)
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Download failed: {str(e)}")
            return False
        except OSError as e:
            logger.error(f"File system error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during download: {str(e)}")
            return False
    
    @staticmethod
    def _make_tts_request(transcript: str, config: AudioConfig, retry: int = 0) -> Optional[Dict[str, Any]]:
        """Make TTS API request with retry logic and error handling."""
        try:
            # Validate inputs
            if not AudioService._validate_transcript(transcript):
                return None
            if not AudioService._validate_config(config):
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
            return fal.subscribe(
                "fal-ai/playht/tts/ldm",
                {
                    "input": transcript,
                    "voices": speakers
                },
                timeout=300  # 5 minutes timeout
            )
        except fal.exceptions.SubscriptionError as e:
            logger.error(f"FAL API error: {str(e)}")
        except Exception as e:
            logger.error(f"TTS request failed: {str(e)}")
            
        if retry < MAX_RETRIES:
            logger.warning(f"Attempt {retry + 1} failed, retrying in {RETRY_DELAY}s")
            time.sleep(RETRY_DELAY)
            # Try fallback voices on subsequent retries
            if retry > 0:
                for speaker in config.speakers.values():
                    if speaker.fallback_voice:
                        speaker.voice, speaker.fallback_voice = speaker.fallback_voice, speaker.voice
            return AudioService._make_tts_request(transcript, config, retry + 1)
            
        logger.error(f"Failed to generate audio after {MAX_RETRIES} attempts")
        return None
    
    @staticmethod
    def _process_audio(voice_url: str, config: AudioConfig) -> Optional[str]:
        """Process audio with background music and effects."""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Download voice audio
                voice_path = os.path.join(temp_dir, "voice.mp3")
                if not AudioService._download_file(voice_url, voice_path):
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
                        
                        if AudioService._download_file(music_url, music_path):
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
                            filename = AudioService._sanitize_filename(f"podcast_{timestamp}.{output_format}")
                            save_path = save_dir / filename
                            voice_audio.export(str(save_path), format=output_format)
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
    
    @staticmethod
    def generate_audio(transcript: str, config: AudioConfig) -> Optional[str]:
        """Generate and process audio with the given configuration."""
        try:
            # Validate inputs
            if not AudioService._validate_transcript(transcript):
                return None
            if not AudioService._validate_config(config):
                return None
                
            # Generate base audio
            result = AudioService._make_tts_request(transcript, config)
            if not result or 'audio' not in result or 'url' not in result['audio']:
                logger.error("Invalid TTS API response")
                return None
                
            # Process audio with effects and music
            return AudioService._process_audio(result['audio']['url'], config)
            
        except Exception as e:
            logger.error(f"Failed to generate audio: {str(e)}")
            return None 
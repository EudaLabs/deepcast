import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
import time

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

class AudioService:
    """Service for audio processing and generation."""
    
    @staticmethod
    def _download_file(url: str, target_path: str) -> bool:
        """Download a file from URL."""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
            
        except Exception as e:
            logger.error(f"Failed to download file: {str(e)}")
            return False
    
    @staticmethod
    def _make_tts_request(transcript: str, config: AudioConfig, retry: int = 0) -> Optional[Dict[str, Any]]:
        """Make TTS API request with retry logic."""
        try:
            # Prepare speakers with emotion modifiers
            speakers = []
            for speaker_id, speaker_config in config.speakers.items():
                modifiers = EMOTION_MODIFIERS[speaker_config.emotion]
                speakers.append({
                    "voice": speaker_config.voice,
                    "turn_prefix": speaker_config.turn_prefix,
                    "stability": modifiers["stability"],
                    "similarity_boost": modifiers["similarity_boost"]
                })
            
            return fal.subscribe(
                "fal-ai/playht/tts/ldm",
                {
                    "input": transcript,
                    "voices": speakers
                }
            )
        except Exception as e:
            if retry < MAX_RETRIES:
                logger.warning(f"Attempt {retry + 1} failed, retrying in {RETRY_DELAY}s: {str(e)}")
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
                
                # Load voice audio
                voice_audio = AudioSegment.from_mp3(voice_path)
                
                # Add background music if specified
                if config.background_music != BackgroundMusicType.NONE:
                    music_url = MUSIC_URLS[config.background_music]
                    music_path = os.path.join(temp_dir, "music.mp3")
                    
                    if AudioService._download_file(music_url, music_path):
                        # Load and adjust music
                        music = AudioSegment.from_mp3(music_path)
                        
                        # Loop music if needed
                        while len(music) < len(voice_audio):
                            music = music + music
                        
                        # Trim music to match voice length
                        music = music[:len(voice_audio)]
                        
                        # Adjust volume and overlay
                        music = music - (20 - (20 * config.music_volume))  # Adjust volume
                        voice_audio = voice_audio.overlay(music)
                
                # Save final audio
                output_path = os.path.join(temp_dir, f"output.{config.output_format}")
                voice_audio.export(output_path, format=config.output_format)
                
                # Save locally if requested
                if config.save_locally:
                    save_dir = Path("output")
                    save_dir.mkdir(exist_ok=True)
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    save_path = save_dir / f"podcast_{timestamp}.{config.output_format}"
                    voice_audio.export(str(save_path), format=config.output_format)
                    logger.info(f"Audio saved locally: {save_path}")
                
                # Upload to temporary storage and return URL
                # Note: In a real implementation, you'd use a proper storage service
                return voice_url  # For now, return original URL
                
        except Exception as e:
            logger.error(f"Failed to process audio: {str(e)}")
            return None
    
    @staticmethod
    def generate_audio(transcript: str, config: AudioConfig) -> Optional[str]:
        """Generate and process audio with the given configuration."""
        if not transcript.strip():
            logger.error("Transcript cannot be empty")
            return None
            
        # Generate base audio
        result = AudioService._make_tts_request(transcript, config)
        if not result or 'audio' not in result or 'url' not in result['audio']:
            return None
            
        # Process audio with effects and music
        return AudioService._process_audio(result['audio']['url'], config) 
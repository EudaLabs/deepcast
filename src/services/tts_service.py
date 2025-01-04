import logging
import time
from typing import Optional, Dict, Any

import fal

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

VOICES: Dict[str, Dict[str, str]] = {
    "speaker1": {
        "voice": "Jennifer (English (US)/American)",
        "turn_prefix": "Speaker 1: ",
        "fallback": "Rachel (English (US)/American)"
    },
    "speaker2": {
        "voice": "Dexter (English (US)/American)",
        "turn_prefix": "Speaker 2: ",
        "fallback": "Patrick (English (US)/American)"
    }
}

class TTSService:
    """Service for converting text to speech using FAL.ai."""
    
    @staticmethod
    def _make_request(transcript: str, retry: int = 0) -> Optional[Dict[str, Any]]:
        """Make API request with retry logic."""
        try:
            return fal.subscribe(
                "fal-ai/playht/tts/ldm",
                {
                    "input": transcript,
                    "voices": [
                        {
                            "voice": voice_config["voice"],
                            "turn_prefix": voice_config["turn_prefix"]
                        }
                        for voice_config in VOICES.values()
                    ]
                }
            )
        except Exception as e:
            if retry < MAX_RETRIES:
                logger.warning(f"Attempt {retry + 1} failed, retrying in {RETRY_DELAY}s: {str(e)}")
                time.sleep(RETRY_DELAY)
                # Try fallback voices on subsequent retries
                if retry > 0:
                    for voice in VOICES.values():
                        voice["voice"], voice["fallback"] = voice["fallback"], voice["voice"]
                return TTSService._make_request(transcript, retry + 1)
            logger.error(f"Failed to generate audio after {MAX_RETRIES} attempts")
            return None
    
    @staticmethod
    def generate_audio(transcript: str) -> Optional[str]:
        """Convert transcript to audio and return the URL."""
        if not transcript.strip():
            logger.error("Transcript cannot be empty")
            return None
            
        result = TTSService._make_request(transcript)
        return result['audio']['url'] if result else None 
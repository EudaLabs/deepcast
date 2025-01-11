from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

class VoiceEmotion(str, Enum):
    """Voice emotion types."""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    EXCITED = "excited"
    SERIOUS = "serious"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    CALM = "calm"

class BackgroundMusicType(str, Enum):
    """Background music types."""
    NONE = "none"
    SOFT_PIANO = "soft_piano"
    AMBIENT = "ambient"
    JAZZ = "jazz"
    ELECTRONIC = "electronic"
    NATURE = "nature"
    CINEMATIC = "cinematic"

MUSIC_URLS = {
    BackgroundMusicType.SOFT_PIANO: "https://cdn.pixabay.com/download/audio/2022/02/22/audio_d1718ab41b.mp3",
    BackgroundMusicType.AMBIENT: "https://cdn.pixabay.com/download/audio/2022/03/15/audio_c8c8395646.mp3",
    BackgroundMusicType.JAZZ: "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3",
    BackgroundMusicType.ELECTRONIC: "https://cdn.pixabay.com/download/audio/2022/03/10/audio_c8695a1ecd.mp3",
    BackgroundMusicType.NATURE: "https://cdn.pixabay.com/download/audio/2021/11/25/audio_00fa5593f3.mp3",
    BackgroundMusicType.CINEMATIC: "https://cdn.pixabay.com/download/audio/2022/05/17/audio_69a61cd6d9.mp3"
}

EMOTION_MODIFIERS = {
    VoiceEmotion.NEUTRAL: {"stability": 0.5, "similarity_boost": 0.5},
    VoiceEmotion.HAPPY: {"stability": 0.7, "similarity_boost": 0.6},
    VoiceEmotion.EXCITED: {"stability": 0.8, "similarity_boost": 0.7},
    VoiceEmotion.SERIOUS: {"stability": 0.3, "similarity_boost": 0.4},
    VoiceEmotion.PROFESSIONAL: {"stability": 0.4, "similarity_boost": 0.5},
    VoiceEmotion.FRIENDLY: {"stability": 0.6, "similarity_boost": 0.6},
    VoiceEmotion.CALM: {"stability": 0.3, "similarity_boost": 0.3}
}

@dataclass
class SpeakerConfig:
    """Configuration for a single speaker."""
    voice: str
    emotion: VoiceEmotion = VoiceEmotion.NEUTRAL
    turn_prefix: str = ""
    fallback_voice: Optional[str] = None

@dataclass
class AudioConfig:
    """Configuration for audio generation."""
    speakers: Dict[str, SpeakerConfig]
    background_music: BackgroundMusicType = BackgroundMusicType.NONE
    music_volume: float = 0.1  # 0.0 to 1.0
    save_locally: bool = False
    output_format: str = "mp3"
    
    def __post_init__(self):
        """Validate configuration."""
        if not 0.0 <= self.music_volume <= 1.0:
            raise ValueError("Music volume must be between 0.0 and 1.0")
        if not self.speakers:
            raise ValueError("At least one speaker must be configured") 
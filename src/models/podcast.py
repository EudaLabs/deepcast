from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class Podcast:
    """A podcast with transcript and optional audio."""
    topic: str
    transcript: str
    audio_url: Optional[str] = None
    
    def save_transcript(self, file_path: str) -> None:
        """Save the transcript to a file."""
        Path(file_path).write_text(self.transcript, encoding='utf-8')
            
    @property
    def has_audio(self) -> bool:
        """Check if the podcast has an audio URL"""
        return self.audio_url is not None 
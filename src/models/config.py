from dataclasses import dataclass
from enum import Enum
from typing import Optional

class PodcastStyle(str, Enum):
    """Different styles of podcast conversations."""
    INTERVIEW = "interview"
    DEBATE = "debate"
    STORYTELLING = "storytelling"
    EDUCATIONAL = "educational"
    CASUAL = "casual"

class ComplexityLevel(str, Enum):
    """Complexity levels for content."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"

class Language(str, Enum):
    """Supported languages."""
    ENGLISH = "english"
    SPANISH = "spanish"
    FRENCH = "french"
    GERMAN = "german"
    ITALIAN = "italian"
    PORTUGUESE = "portuguese"
    
STYLE_DESCRIPTIONS = {
    PodcastStyle.INTERVIEW: "One host interviews an expert guest",
    PodcastStyle.DEBATE: "Two speakers discuss opposing viewpoints",
    PodcastStyle.STORYTELLING: "A narrative-driven conversation with story elements",
    PodcastStyle.EDUCATIONAL: "Focus on teaching and explaining concepts",
    PodcastStyle.CASUAL: "Informal, friendly conversation about the topic"
}

@dataclass
class PodcastConfig:
    """Configuration for podcast generation."""
    style: PodcastStyle = PodcastStyle.INTERVIEW
    complexity: ComplexityLevel = ComplexityLevel.INTERMEDIATE
    language: Language = Language.ENGLISH
    num_exchanges: int = 5
    
    def __post_init__(self):
        """Validate configuration."""
        if self.num_exchanges < 3:
            raise ValueError("Number of exchanges must be at least 3")
        if self.num_exchanges > 10:
            raise ValueError("Number of exchanges cannot exceed 10") 
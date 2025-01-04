import logging
import os
from typing import Optional

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from ..models.config import PodcastConfig, PodcastStyle, ComplexityLevel, Language, STYLE_DESCRIPTIONS

logger = logging.getLogger(__name__)

MAX_CONTENT_LENGTH = 4000

LANGUAGE_PROMPTS = {
    Language.ENGLISH: "Generate the conversation in English",
    Language.SPANISH: "Generate the conversation in Spanish (Genera la conversación en español)",
    Language.FRENCH: "Generate the conversation in French (Générez la conversation en français)",
    Language.GERMAN: "Generate the conversation in German (Generieren Sie das Gespräch auf Deutsch)",
    Language.ITALIAN: "Generate the conversation in Italian (Genera la conversazione in italiano)",
    Language.PORTUGUESE: "Generate the conversation in Portuguese (Gere a conversa em português)"
}

COMPLEXITY_PROMPTS = {
    ComplexityLevel.BEGINNER: """
    - Use simple, everyday language
    - Explain basic concepts clearly
    - Avoid technical jargon
    - Use relatable examples
    """,
    ComplexityLevel.INTERMEDIATE: """
    - Balance technical and accessible language
    - Build upon basic concepts
    - Introduce some field-specific terms
    - Use more detailed examples
    """,
    ComplexityLevel.EXPERT: """
    - Use technical language appropriately
    - Discuss advanced concepts
    - Reference specific studies or theories
    - Explore complex implications
    """
}

PODCAST_TEMPLATE = """
Create an engaging conversation between two speakers discussing the following topic or content: {topic}

Style: {style_description}
{language_prompt}

Requirements:
- Generate exactly {num_exchanges} back-and-forth exchanges
- Make it natural and conversational
- Include specific details from the topic/content
- Each line must start with either "Speaker 1:" or "Speaker 2:"
- Keep each speaker's response under 25 words
- Focus on the most important aspects if working with file content

Complexity Level:
{complexity_requirements}

The conversation should be:
- Well-structured with a clear flow
- Engaging and dynamic
- Appropriate for the chosen style and complexity
- Natural and authentic

Example format (but create new content):
Speaker 1: Welcome! Today we're exploring [topic]. What makes this so interesting?
Speaker 2: [Topic] is fascinating because [specific detail]. Let me explain why.
"""

class LLMService:
    """Service for generating podcast transcripts using language models."""
    
    def __init__(self) -> None:
        self.llm = ChatOpenAI(
            model="deepseek/deepseek-chat",
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1"
        )
        self.template = ChatPromptTemplate.from_template(PODCAST_TEMPLATE)
        
    def generate_transcript(self, topic: str, config: PodcastConfig) -> Optional[str]:
        """Generate a podcast transcript with the given configuration."""
        if not topic.strip():
            logger.error("Topic cannot be empty")
            return None
            
        # Truncate content if too long
        if len(topic) > MAX_CONTENT_LENGTH:
            logger.warning(f"Content too long ({len(topic)} chars), truncating to {MAX_CONTENT_LENGTH} chars")
            topic = topic[:MAX_CONTENT_LENGTH] + "..."
            
        try:
            # Prepare template variables
            variables = {
                "topic": topic,
                "style_description": STYLE_DESCRIPTIONS[config.style],
                "language_prompt": LANGUAGE_PROMPTS[config.language],
                "complexity_requirements": COMPLEXITY_PROMPTS[config.complexity],
                "num_exchanges": config.num_exchanges
            }
            
            chain = self.template | self.llm
            response = chain.invoke(variables)
            
            transcript = response.content.strip()
            if not transcript:
                logger.error("Generated transcript is empty")
                return None
                
            # Verify format
            if not all(line.startswith(("Speaker 1:", "Speaker 2:")) 
                      for line in transcript.split('\n') if line.strip()):
                logger.error("Generated transcript has invalid format")
                return None
                
            return transcript
            
        except Exception as e:
            logger.error(f"Failed to generate transcript: {str(e)}")
            return None 
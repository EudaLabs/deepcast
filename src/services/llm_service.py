import logging
import os
from typing import Optional

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

MAX_CONTENT_LENGTH = 4000  # Maximum content length to process

PODCAST_TEMPLATE = """
Create an engaging conversation between two speakers discussing the following topic or content: {topic}

Requirements:
- Generate exactly 5 back-and-forth exchanges
- Make it natural and conversational
- Include specific details from the topic/content
- Each line must start with either "Speaker 1:" or "Speaker 2:"
- Keep each speaker's response under 20 words
- Make Speaker 1 the host/interviewer and Speaker 2 the expert/guest
- Focus on the most important aspects if working with file content

The conversation should be:
- Insightful and educational
- Easy to understand for general audience
- Engaging and dynamic
- Well-structured with a clear flow

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
        
    def generate_transcript(self, topic: str) -> Optional[str]:
        """Generate a podcast transcript about a topic."""
        if not topic.strip():
            logger.error("Topic cannot be empty")
            return None
            
        # Truncate content if too long
        if len(topic) > MAX_CONTENT_LENGTH:
            logger.warning(f"Content too long ({len(topic)} chars), truncating to {MAX_CONTENT_LENGTH} chars")
            topic = topic[:MAX_CONTENT_LENGTH] + "..."
            
        try:
            chain = self.template | self.llm
            response = chain.invoke({"topic": topic})
            
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
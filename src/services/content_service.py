import logging
from pathlib import Path
from typing import Optional, List
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import html2text
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

logger = logging.getLogger(__name__)

class ContentService:
    """Service for fetching content from various sources."""
    
    @staticmethod
    def extract_youtube_id(url: str) -> Optional[str]:
        """Extract YouTube video ID from URL."""
        try:
            parsed = urlparse(url)
            if 'youtu.be' in parsed.netloc:
                return parsed.path[1:]
            elif 'youtube.com' in parsed.netloc:
                for param in parsed.query.split('&'):
                    if param.startswith('v='):
                        return param[2:]
            return None
        except Exception:
            return None
    
    @staticmethod
    def fetch_youtube_transcript(url: str) -> Optional[str]:
        """Fetch transcript from YouTube video."""
        try:
            video_id = ContentService.extract_youtube_id(url)
            if not video_id:
                logger.error("Invalid YouTube URL")
                return None
                
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            formatter = TextFormatter()
            return formatter.format_transcript(transcript)
            
        except Exception as e:
            logger.error(f"Failed to fetch YouTube transcript: {str(e)}")
            return None
    
    @staticmethod
    def fetch_web_content(url: str) -> Optional[str]:
        """Fetch and extract content from web URL."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Convert HTML to markdown-like text
            h = html2text.HTML2Text()
            h.ignore_links = True
            h.ignore_images = True
            h.ignore_emphasis = True
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
                
            # Get main content
            main_content = soup.find('main') or soup.find('article') or soup.find('body')
            if not main_content:
                return None
                
            return h.handle(str(main_content)).strip()
            
        except Exception as e:
            logger.error(f"Failed to fetch web content: {str(e)}")
            return None
    
    @staticmethod
    def combine_content(contents: List[str], max_length: int = 4000) -> str:
        """Combine multiple content pieces with smart truncation."""
        total_content = "\n\n---\n\n".join(contents)
        if len(total_content) > max_length:
            # Try to find a good breaking point
            truncated = total_content[:max_length]
            last_period = truncated.rfind('.')
            if last_period > max_length * 0.8:  # If we can find a good sentence break
                return truncated[:last_period + 1]
            return truncated + "..."
        return total_content 
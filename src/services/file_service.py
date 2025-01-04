import logging
from pathlib import Path
from typing import Optional, List
import re

import docx
from PyPDF2 import PdfReader
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import markdown

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_MB = 10
SUPPORTED_EXTENSIONS = {'.txt', '.pdf', '.docx', '.epub', '.md', '.html', '.htm'}

class FileService:
    """Service for reading content from different file types."""
    
    @staticmethod
    def read_file(file_paths: str | List[str]) -> Optional[str]:
        """Read content from one or more files."""
        if isinstance(file_paths, str):
            return FileService._read_single_file(file_paths)
            
        # Handle multiple files
        contents = []
        for file_path in file_paths:
            content = FileService._read_single_file(file_path)
            if content:
                contents.append(content)
                
        if not contents:
            return None
            
        # Combine contents with separators
        return "\n\n---\n\n".join(contents)
    
    @staticmethod
    def _read_single_file(file_path: str) -> Optional[str]:
        """Read content from a single file."""
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return None
            
        # Check file extension
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            logger.error(f"Unsupported file type: {path.suffix}. Supported types: {', '.join(SUPPORTED_EXTENSIONS)}")
            return None
            
        # Check file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            logger.error(f"File too large: {file_size_mb:.1f}MB. Maximum size: {MAX_FILE_SIZE_MB}MB")
            return None
            
        try:
            if path.suffix.lower() == '.txt':
                return path.read_text(encoding='utf-8').strip()
                
            elif path.suffix.lower() == '.pdf':
                reader = PdfReader(file_path)
                text = ' '.join(page.extract_text() for page in reader.pages)
                return text.strip() if text else None
                
            elif path.suffix.lower() == '.docx':
                doc = docx.Document(file_path)
                text = ' '.join(paragraph.text for paragraph in doc.paragraphs)
                return text.strip() if text else None
                
            elif path.suffix.lower() == '.epub':
                book = epub.read_epub(file_path)
                texts = []
                for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                    soup = BeautifulSoup(item.content, 'html.parser')
                    texts.append(soup.get_text())
                return ' '.join(texts).strip()
                
            elif path.suffix.lower() == '.md':
                content = path.read_text(encoding='utf-8')
                html = markdown.markdown(content)
                soup = BeautifulSoup(html, 'html.parser')
                return soup.get_text().strip()
                
            elif path.suffix.lower() in {'.html', '.htm'}:
                content = path.read_text(encoding='utf-8')
                soup = BeautifulSoup(content, 'html.parser')
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                return soup.get_text().strip()
                
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {str(e)}")
            return None 
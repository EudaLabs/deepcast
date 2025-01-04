import logging
from pathlib import Path
from typing import Optional

import docx
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_MB = 10
SUPPORTED_EXTENSIONS = {'.txt', '.pdf', '.docx'}

class FileService:
    """Service for reading content from different file types."""
    
    @staticmethod
    def read_file(file_path: str) -> Optional[str]:
        """Read content from a file based on its extension."""
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
                
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {str(e)}")
            return None 
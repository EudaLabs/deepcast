import logging
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

REQUIRED_ENV_VARS = ["OPENROUTER_API_KEY", "FAL_KEY"]

def load_environment() -> List[str]:
    """Load environment variables and return any missing ones."""
    if not Path(".env").exists():
        return ["No .env file found. Please create one from .env.example"]
        
    load_dotenv()
    return [var for var in REQUIRED_ENV_VARS if not os.getenv(var)] 
import logging
import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel

from .models.podcast import Podcast
from .services.llm_service import LLMService
from .services.tts_service import TTSService
from .services.file_service import FileService
from .utils import config

# Initialize logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("deepcast")

app = typer.Typer(
    help="DeepCast - AI Podcast Generator",
    add_completion=False,
)
console = Console()

def process_file(file_path: str) -> tuple[str, str]:
    """Process input file and return topic and content."""
    path = Path(file_path)
    if not path.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        raise typer.Exit(1)
        
    with console.status("[bold yellow]Reading file..."):
        content = FileService.read_file(file_path)
        if not content:
            raise typer.Exit(1)
    return f"Content from {path.name}", content

@app.command()
def generate(
    topic: str = typer.Argument(..., help="Topic for the podcast discussion"),
    file: Optional[str] = typer.Option(None, "--file", "-f", help="Generate podcast from a file (txt, pdf, docx)"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Save transcript to file"),
    audio_only: bool = typer.Option(False, "--audio-only", help="Only generate and show the audio URL"),
):
    """Generate a podcast-style conversation with audio."""
    try:
        # Check environment
        missing_vars = config.load_environment()
        if missing_vars:
            for var in missing_vars:
                console.print(f"[red]{var}[/red]")
            raise typer.Exit(1)

        # Process input
        content = None
        if file:
            topic, content = process_file(file)

        # Generate transcript
        with console.status("[bold green]Generating podcast transcript..."):
            llm_service = LLMService()
            transcript = llm_service.generate_transcript(content or topic)
            if not transcript:
                console.print("[red]Failed to generate transcript[/red]")
                raise typer.Exit(1)
                
            podcast = Podcast(topic=topic, transcript=transcript)

        if not audio_only:
            console.print("\n[bold]Generated Transcript:[/bold]")
            console.print(Panel(transcript, title=f"Podcast Transcript: {topic}", expand=False))

        # Generate audio
        with console.status("[bold green]Converting to audio..."):
            audio_url = TTSService.generate_audio(transcript)
            if audio_url:
                podcast.audio_url = audio_url

        if podcast.has_audio:
            console.print(f"\n[bold green]🎧 Audio generated successfully![/bold green]")
            console.print(f"[blue]Audio URL:[/blue] {audio_url}")
        else:
            console.print("\n[red]Failed to generate audio[/red]")

        if output_file and not audio_only:
            podcast.save_transcript(output_file)
            console.print(f"\n[green]Transcript saved to: {output_file}[/green]")
            
    except Exception as e:
        logger.exception("An error occurred")
        console.print(f"\n[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)

@app.command()
def version():
    """Show the version of DeepCast"""
    from . import __version__
    console.print(f"DeepCast version: [bold blue]{__version__}[/bold blue]") 
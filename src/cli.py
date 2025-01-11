import logging
import os
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table

from .models.podcast import Podcast
from .models.config import (
    PodcastConfig, PodcastStyle, ComplexityLevel, 
    Language, STYLE_DESCRIPTIONS
)
from .models.audio_config import (
    AudioConfig, SpeakerConfig, BackgroundMusicType,
    VoiceEmotion, MUSIC_URLS
)
from .services.llm_service import LLMService
from .services.audio_service import AudioService
from .services.file_service import FileService
from .services.content_service import ContentService
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

def show_styles():
    """Display available podcast styles."""
    table = Table(title="Available Podcast Styles")
    table.add_column("Style", style="cyan")
    table.add_column("Description", style="green")
    
    for style in PodcastStyle:
        table.add_row(style.value, STYLE_DESCRIPTIONS[style])
    
    console.print(table)

def show_music():
    """Display available background music types."""
    table = Table(title="Available Background Music")
    table.add_column("Type", style="cyan")
    table.add_column("Preview URL", style="blue")
    
    for music_type in BackgroundMusicType:
        if music_type != BackgroundMusicType.NONE:
            table.add_row(music_type.value, MUSIC_URLS[music_type])
    
    console.print(table)

def show_emotions():
    """Display available voice emotions."""
    table = Table(title="Available Voice Emotions")
    table.add_column("Emotion", style="cyan")
    
    for emotion in VoiceEmotion:
        table.add_row(emotion.value)
    
    console.print(table)

def process_input(
    topic: str,
    files: Optional[List[str]] = None,
    url: Optional[str] = None,
    youtube: Optional[str] = None,
) -> tuple[str, Optional[str]]:
    """Process all input sources and combine content."""
    contents = []
    
    # Process files if provided
    if files:
        with console.status("[bold yellow]Reading files..."):
            content = FileService.read_file(files)
            if content:
                contents.append(content)
    
    # Process URL if provided
    if url:
        with console.status("[bold yellow]Fetching web content..."):
            content = ContentService.fetch_web_content(url)
            if content:
                contents.append(content)
                
    # Process YouTube URL if provided
    if youtube:
        with console.status("[bold yellow]Fetching YouTube transcript..."):
            content = ContentService.fetch_youtube_transcript(youtube)
            if content:
                contents.append(content)
    
    # If no content was gathered, return topic only
    if not contents:
        return topic, None
        
    # Combine all content
    combined = ContentService.combine_content(contents)
    return topic, combined

@app.command()
def styles():
    """List available podcast styles and their descriptions."""
    show_styles()

@app.command()
def music():
    """List available background music types."""
    show_music()

@app.command()
def emotions():
    """List available voice emotions."""
    show_emotions()

@app.command()
def generate(
    topic: str = typer.Argument(..., help="Topic for the podcast discussion"),
    files: Optional[List[str]] = typer.Option(None, "--file", "-f", help="Generate podcast from files (txt, pdf, docx, epub, md, html)"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="Generate podcast from web article URL"),
    youtube: Optional[str] = typer.Option(None, "--youtube", "-y", help="Generate podcast from YouTube video transcript"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Save transcript to file"),
    audio_only: bool = typer.Option(False, "--audio-only", help="Only generate and show the audio URL"),
    style: PodcastStyle = typer.Option(PodcastStyle.INTERVIEW, "--style", "-s", help="Podcast style"),
    complexity: ComplexityLevel = typer.Option(ComplexityLevel.INTERMEDIATE, "--complexity", "-c", help="Content complexity"),
    language: Language = typer.Option(Language.ENGLISH, "--language", "-l", help="Conversation language"),
    exchanges: int = typer.Option(5, "--exchanges", "-e", help="Number of conversation exchanges (3-10)"),
    background_music: BackgroundMusicType = typer.Option(BackgroundMusicType.NONE, "--music", "-m", help="Background music type"),
    music_volume: float = typer.Option(0.1, "--volume", "-v", help="Background music volume (0.0-1.0)"),
    speaker1_emotion: VoiceEmotion = typer.Option(VoiceEmotion.PROFESSIONAL, "--speaker1-emotion", help="First speaker's emotion"),
    speaker2_emotion: VoiceEmotion = typer.Option(VoiceEmotion.FRIENDLY, "--speaker2-emotion", help="Second speaker's emotion"),
    save_audio: bool = typer.Option(False, "--save-audio", help="Save audio file locally"),
    audio_format: str = typer.Option("mp3", "--format", help="Audio output format (mp3, wav, ogg)"),
):
    """Generate a podcast-style conversation with audio."""
    try:
        # Check environment
        missing_vars = config.load_environment()
        if missing_vars:
            for var in missing_vars:
                console.print(f"[red]{var}[/red]")
            raise typer.Exit(1)

        # Create podcast config
        try:
            podcast_config = PodcastConfig(
                style=style,
                complexity=complexity,
                language=language,
                num_exchanges=exchanges
            )
        except ValueError as e:
            console.print(f"[red]Configuration error: {str(e)}[/red]")
            raise typer.Exit(1)

        # Create audio config
        audio_config = AudioConfig(
            speakers={
                "speaker1": SpeakerConfig(
                    voice="Jennifer (English (US)/American)",
                    emotion=speaker1_emotion,
                    turn_prefix="Speaker 1: ",
                    fallback_voice="Rachel (English (US)/American)"
                ),
                "speaker2": SpeakerConfig(
                    voice="Dexter (English (US)/American)",
                    emotion=speaker2_emotion,
                    turn_prefix="Speaker 2: ",
                    fallback_voice="Patrick (English (US)/American)"
                )
            },
            background_music=background_music,
            music_volume=music_volume,
            save_locally=save_audio,
            output_format=audio_format
        )

        # Process all inputs
        topic, content = process_input(topic, files, url, youtube)

        # Generate transcript
        with console.status("[bold green]Generating podcast transcript..."):
            llm_service = LLMService()
            transcript = llm_service.generate_transcript(content or topic, podcast_config)
            if not transcript:
                console.print("[red]Failed to generate transcript[/red]")
                raise typer.Exit(1)
                
            podcast = Podcast(topic=topic, transcript=transcript)

        if not audio_only:
            console.print("\n[bold]Generated Transcript:[/bold]")
            console.print(Panel(
                transcript, 
                title=f"Podcast Transcript: {topic}",
                subtitle=f"Style: {style.value} | Complexity: {complexity.value} | Language: {language.value}",
                expand=False
            ))

        # Generate audio
        with console.status("[bold green]Converting to audio..."):
            audio_url = AudioService.generate_audio(transcript, audio_config)
            if audio_url:
                podcast.audio_url = audio_url

        if podcast.has_audio:
            console.print(f"\n[bold green]🎧 Audio generated successfully![/bold green]")
            console.print(f"[blue]Audio URL:[/blue] {audio_url}")
            if save_audio:
                console.print("[green]Audio file saved in the output directory[/green]")
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
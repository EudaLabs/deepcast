# deepcast

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)

deepcast is an AI-powered CLI tool that generates engaging podcast-style conversations with realistic text-to-speech capabilities. Perfect for creating educational content, practice conversations, or exploring topics in a dialogue format.

## ✨ Features

- 🤖 **AI-Powered Conversations**: Uses Deepseek-V3 model for generating natural, educational dialogues
- 🎧 **Interactive Format**: Generates engaging podcast-style conversations between two speakers
- 📚 **Educational Content**: Creates deep, insightful discussions on any given topic
- 🗣️ **Text-to-Speech**: Integrates PlayHT for converting conversations into realistic audio
- 🚀 **Background Music**: Add ambient music with adjustable volume
- 😊 **Voice Emotions**: Control speaker emotions (happy, serious, excited, etc.)
- 📄 **Rich File Support**: Generate from TXT, PDF, DOCX, EPUB, Markdown, HTML files
- 🌐 **Web Content**: Generate from web articles, YouTube transcripts, and URLs
- 🔄 **Content Combination**: Combine multiple sources into one podcast
- 🌍 **Multiple Languages**: Support for English, Spanish, French, German, Italian, and Portuguese
- 🎭 **Podcast Styles**: Different conversation styles (interview, debate, storytelling, etc.)
- 📊 **Complexity Levels**: Adjust content for beginner, intermediate, or expert audiences
- 🚀 **Easy to Use**: Simple CLI interface with rich terminal output

## 🛠️ Installation

1. Clone the repository:

```bash
git clone https://github.com/byigitt/deepcast.git
cd deepcast
```

2. Install dependencies using uv:

```bash
uv venv
uv pip install -e .
```

3. Create a `.env` file from the example:

```bash
cp .env.example .env
```

4. Add your API keys to the `.env` file:

- Get an OpenRouter API key from [OpenRouter](https://openrouter.ai/keys)
- Get a FAL API key from [FAL.ai](https://fal.ai)

## 🚀 Usage

### View Available Options

List available podcast styles:

```bash
deepcast styles
```

List available background music:

```bash
deepcast music
```

List available voice emotions:

```bash
deepcast emotions
```

### Generate from a Topic

Create a podcast about any topic with custom settings:

```bash
# Basic usage
deepcast generate "Quantum Computing"

# With custom style
deepcast generate "Quantum Computing" --style debate

# With background music
deepcast generate "Quantum Computing" --music ambient --volume 0.2

# With voice emotions
deepcast generate "Quantum Computing" \
    --speaker1-emotion professional \
    --speaker2-emotion friendly

# Full customization
deepcast generate "Quantum Computing" \
    --style educational \
    --complexity expert \
    --language french \
    --exchanges 7 \
    --music soft_piano \
    --volume 0.15 \
    --speaker1-emotion serious \
    --speaker2-emotion excited \
    --save-audio \
    --format mp3
```

### Generate from Files

Create a podcast from various file types:

```bash
# From a single file with music
deepcast generate "Research Paper" \
    --file paper.pdf \
    --music ambient

# From multiple files with emotions
deepcast generate "Research Summary" \
    --file paper1.pdf \
    --file paper2.pdf \
    --speaker1-emotion professional \
    --speaker2-emotion friendly

# From different file types with full audio
deepcast generate "Documentation" \
    --file intro.md \
    --file chapter1.docx \
    --file appendix.pdf \
    --music soft_piano \
    --volume 0.2 \
    --save-audio
```

### Generate from Web Content

Create a podcast from web content:

```bash
# From a web article with music
deepcast generate "News Article" \
    --url "https://example.com/article" \
    --music cinematic

# From a YouTube video with emotions
deepcast generate "Video Summary" \
    --youtube "https://youtube.com/watch?v=..." \
    --speaker1-emotion excited \
    --speaker2-emotion professional

# Combine web and file content with full audio
deepcast generate "Research Review" \
    --file paper.pdf \
    --url "https://example.com/article" \
    --youtube "https://youtube.com/watch?v=..." \
    --music jazz \
    --volume 0.1 \
    --save-audio
```

### Output Options

Save the transcript to a file:

```bash
deepcast generate "Artificial Intelligence" --output transcript.txt
```

Only get the audio URL:

```bash
deepcast generate "Space Exploration" --audio-only
```

Save audio locally:

```bash
deepcast generate "Nature Documentary" \
    --music nature \
    --save-audio \
    --format mp3
```

### Full Example

Combine all features:

```bash
deepcast generate "Advanced Physics" \
    --file research.pdf \
    --file notes.md \
    --url "https://example.com/article" \
    --youtube "https://youtube.com/watch?v=..." \
    --style educational \
    --complexity expert \
    --language french \
    --exchanges 7 \
    --music cinematic \
    --volume 0.15 \
    --speaker1-emotion professional \
    --speaker2-emotion excited \
    --save-audio \
    --format mp3 \
    --output transcript.txt
```

## 🏗️ Project Structure

```
src/
├── models/         # Data models (Podcast, Config, Audio)
├── services/       # Core services (LLM, Audio, File, Content)
├── utils/          # Utility functions (Config)
└── cli.py          # CLI interface
```

## 🔧 Configuration

The following environment variables can be configured in `.env`:

- `OPENROUTER_API_KEY`: Your OpenRouter API key for accessing the Deepseek model
- `FAL_KEY`: Your FAL.ai API key for text-to-speech conversion
- `LOG_LEVEL`: Optional logging level (default: INFO)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenRouter](https://openrouter.ai) for providing access to the Deepseek model
- [FAL.ai](https://fal.ai) for the text-to-speech capabilities
- [PlayHT](https://play.ht) for voice synthesis
- [Pixabay](https://pixabay.com) for background music
- All our contributors and users

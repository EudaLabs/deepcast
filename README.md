# deepcast

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)

deepcast is an AI-powered CLI tool that generates engaging podcast-style conversations with realistic text-to-speech capabilities. Perfect for creating educational content, practice conversations, or exploring topics in a dialogue format.

## ✨ Features

- 🤖 **AI-Powered Conversations**: Uses Deepseek-V3 model for generating natural, educational dialogues
- 🎧 **Interactive Format**: Generates engaging podcast-style conversations between two speakers
- 📚 **Educational Content**: Creates deep, insightful discussions on any given topic
- 🗣️ **Text-to-Speech**: Integrates PlayHT for converting conversations into realistic audio
- 🚀 **File Support**: Generate podcasts from TXT, PDF, and DOCX files
- 🎯 **Multiple Outputs**: Save transcripts and get audio URLs
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

### Generate from a Topic

Create a podcast about any topic:

```bash
deepcast generate "Quantum Computing"
```

### Generate from Files

Create a podcast from various file types using the `--file` flag:

```bash
# From a text file
deepcast generate "Text File Content" --file article.txt

# From a PDF document
deepcast generate "PDF Content" --file research.pdf

# From a Word document
deepcast generate "Word Document" --file notes.docx
```

The topic argument will be used as a context hint for the AI, helping it better understand the content.

### Output Options

Save the transcript to a file:

```bash
deepcast generate "Artificial Intelligence" --output transcript.txt
```

Only get the audio URL:

```bash
deepcast generate "Space Exploration" --audio-only
```

Combine options:

```bash
# Generate from file and save transcript
deepcast generate "Research Paper" --file paper.pdf --output transcript.txt

# Generate from file and only get audio
deepcast generate "Meeting Notes" --file notes.docx --audio-only
```

### Other Commands

Check version:

```bash
deepcast version
```

## 🏗️ Project Structure

```
src/
├── models/         # Data models (Podcast)
├── services/       # Core services (LLM, TTS, File)
├── utils/         # Utility functions (Config)
└── cli.py         # CLI interface
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
- All our contributors and users

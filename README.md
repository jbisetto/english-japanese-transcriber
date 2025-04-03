# English-Japanese Transcriber

This project is a sophisticated transcription agent that leverages AWS Bedrock and Google Cloud services to transcribe audio files with high accuracy. It supports both English and Japanese, with advanced audio processing and intelligent language detection capabilities.

## Features

- Advanced audio processing with multiple segmentation strategies:
  - Silence-based segmentation
  - Fixed-length segmentation with overlap support
  - Energy-based segmentation using RMS values
- Intelligent language detection for English and Japanese
- High-quality transcription using AWS Bedrock
- Sophisticated text processing:
  - Language-specific formatting
  - Punctuation normalization
  - Number and unit handling
  - Contraction expansion (English)
  - Japanese text normalization
- Multiple output formats:
  - Plain text (TXT)
  - Structured JSON
  - Subtitles (SRT)
- Extensible configuration system supporting:
  - AWS Bedrock
  - Google Cloud
  - Custom audio processing parameters
  - Configurable output settings

## Requirements

- Python 3.8+
- AWS credentials configured for Bedrock access
- (Optional) Google Cloud credentials
- `requirements.txt` dependencies

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

1. Copy `.env.example` to `.env`
2. Configure your environment variables:
```env
# Cloud Provider Selection
CLOUD_PROVIDER=aws  # or google

# AWS Configuration
AWS_REGION_NAME=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET=your_bucket_name

# Google Cloud Configuration (if using)
GOOGLE_PROJECT_ID=your_project_id
GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json

# Audio Configuration
TARGET_SAMPLE_RATE=16000
TARGET_CHANNELS=1
MIN_SILENCE_LEN=700
SILENCE_THRESH=-16
KEEP_SILENCE=200

# Output Configuration
OUTPUT_DIR=output
```

## Usage

```python
from src.agent import TranscriptionAgent
from src.config import ConfigFactory

if __name__ == '__main__':
    # Get configuration based on environment
    config = ConfigFactory.get_config()
    
    # Initialize agent with configuration
    agent = TranscriptionAgent(config)
    
    # Process audio file
    audio_path = "examples/sample_audio/sample.mp3"
    filename = "transcription"
    
    # Save in different formats
    agent.process_and_save_transcript(audio_path, filename, format="txt")
    agent.process_and_save_transcript(audio_path, filename, format="json")
    agent.process_and_save_transcript(audio_path, filename, format="srt")
```

## Architecture

The project follows a modular architecture with the following components:

- `TranscriptionAgent`: Main orchestrator
- Audio Processing:
  - `AudioHandler`: Audio file processing and normalization
  - `AudioSegmenter`: Multiple segmentation strategies
- Language Services:
  - `LanguageDetector`: Intelligent language detection
  - `TextProcessor`: Language-specific text processing
- Transcription:
  - `TranscriptionService`: Cloud service integration
  - `BedrockClient`: AWS Bedrock integration
- Output:
  - `OutputManager`: Multiple format support
- Configuration:
  - `ConfigFactory`: Dynamic configuration management
  - Provider-specific configurations

## Documentation

For detailed documentation on architecture, configuration, and advanced usage, see the `docs/` directory.

## Testing

The project includes a comprehensive test suite:
```bash
python -m pytest -v  # Run all tests
python -m pytest tests/test_audio_handler.py -v  # Run specific test file
```

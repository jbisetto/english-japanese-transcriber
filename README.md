# English-Japanese Transcriber

This project is a transcription agent that uses AWS Bedrock to transcribe audio files and detect the language of the transcribed text. It supports both English and Japanese.

## Features

- Transcribe audio files to text.
- Detect the language of the transcribed text.
- Save the transcript to a file.
- Supports English and Japanese.

## Requirements

- Python 3.8+
- AWS credentials configured for Bedrock access.
- `requirements.txt` dependencies

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from src.agent import TranscriptionAgent

if __name__ == '__main__':
    # Example usage
    agent = TranscriptionAgent()
    audio_path = "examples/sample_audio/sample.mp3"  # Replace with your audio file
    filename = "simple_transcription"
    agent.process_and_save_transcript(audio_path, filename, format="txt")
```

## Configuration

The project uses a configuration file to store settings. You can modify the settings in the `src/config.py` file.

## Architecture

The project is structured as follows:

- `src/agent.py`: Contains the `TranscriptionAgent` class, which is the main entry point for the project.
- `src/config.py`: Contains the configuration classes.
- `src/audio/`: Contains the audio handling modules.
- `src/language/`: Contains the language detection modules.
- `src/output/`: Contains the output management modules.
- `src/transcription/`: Contains the transcription modules.

## Documentation

For more detailed documentation, see the `docs/` directory.

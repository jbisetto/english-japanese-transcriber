# English-Japanese Transcriber Integration Guide

## Overview
The English-Japanese Transcriber is a Python library that provides audio transcription capabilities with automatic language detection between English and Japanese. It supports both AWS and Google Cloud as backend providers for transcription services.

## API Documentation

### Main Entry Point: TranscriptionAgent

The `TranscriptionAgent` class serves as the main entry point for the library. It handles audio processing, language detection, transcription, and output management.

#### Initialization
```python
from src.agent import TranscriptionAgent
from src.config import AWSConfig, AudioConfig, TranscriptionConfig, LanguageDetectionConfig, OutputConfig

# Initialize with default configurations
agent = TranscriptionAgent()

# Or initialize with custom configurations
agent = TranscriptionAgent(
    aws_config=AWSConfig(),
    audio_config=AudioConfig(),
    transcription_config=TranscriptionConfig(),
    language_detection_config=LanguageDetectionConfig(),
    output_config=OutputConfig()
)
```

#### Main Methods

1. `transcribe_audio(audio_path: str) -> List[Dict[str, str]]`
   - Transcribes an audio file and returns a list of transcript entries
   - Each entry contains the detected language and transcribed text
   - Returns: `[{"language": "en", "text": "transcribed text"}, ...]`

2. `process_and_save_transcript(audio_path: str, filename: str, format: str = "txt") -> None`
   - Transcribes audio and saves the result to a file
   - Supported formats: "txt", "json", "srt"

## Dependencies

### Required Python Packages
```
boto3>=1.28.0
botocore>=1.31.0
pydub>=0.25.1
jaconv>=0.3.4
mojimoji>=0.0.12
nltk>=3.8.1
python-dotenv>=1.0.0
google-cloud-speech>=2.25.1
google-cloud-storage>=2.14.0
google-cloud-translate>=3.15.0
numpy>=1.24.0
scipy>=1.11.4
soundfile>=0.12.1
psutil>=5.9.0
amazon-transcribe>=0.6.0
```

### Environment Setup
1. Create a `.env` file with the following variables:
```
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=your_region
AWS_S3_BUCKET=your_bucket_name

# Google Cloud Configuration (if using Google Cloud)
GOOGLE_APPLICATION_CREDENTIALS=path_to_credentials.json
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_STORAGE_BUCKET=your_bucket_name

# Audio Processing Configuration
TARGET_SAMPLE_RATE=16000
TARGET_CHANNELS=1
MIN_SILENCE_LEN=700
SILENCE_THRESH=-16
SEGMENT_DURATION=10000

# Output Configuration
OUTPUT_DIR=output
```

## Data Flow

### Input Requirements
- Supported audio formats: MP3, WAV, FLAC
- Audio files are automatically processed to:
  - Target sample rate: 16kHz (configurable)
  - Mono channel (configurable)
  - Segmented based on silence detection

### Output Specifications
The transcriber produces output in three formats:
1. Text file (.txt): Plain text transcription
2. JSON file (.json): Structured format with language and text
3. SubRip file (.srt): Subtitle format with timestamps

## Integration Considerations

### Performance Characteristics
- CPU Usage: Moderate to high during audio processing and transcription
- Memory Usage: Depends on audio file size and segmentation
- Processing Time: Varies with audio length and complexity

### Threading and Async Support
- The library is synchronous by default
- For non-blocking operations, use Python's threading or asyncio
- Example of async usage:
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def transcribe_async(audio_path: str):
    with ThreadPoolExecutor() as executor:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            executor,
            agent.transcribe_audio,
            audio_path
        )
```

### Error Handling
The library uses standard Python exceptions:
- `ValueError`: Configuration errors
- `FileNotFoundError`: Audio file not found
- `Exception`: General transcription errors

### Best Practices
1. Resource Management:
```python
# Use context manager for cleanup
with TranscriptionAgent() as agent:
    agent.process_and_save_transcript("audio.mp3", "output")
```

2. Error Handling:
```python
try:
    transcript = agent.transcribe_audio("audio.mp3")
except Exception as e:
    print(f"Transcription failed: {e}")
    # Handle error appropriately
```

## Advanced Integration Examples

### Continuous Processing
```python
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class AudioHandler(FileSystemEventHandler):
    def __init__(self, agent):
        self.agent = agent

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(('.mp3', '.wav', '.flac')):
            self.agent.process_and_save_transcript(
                event.src_path,
                os.path.splitext(os.path.basename(event.src_path))[0]
            )

# Set up file watching
observer = Observer()
observer.schedule(AudioHandler(agent), path="input_directory", recursive=False)
observer.start()
```

### Minimalist Integration
```python
from src.agent import TranscriptionAgent

def transcribe_file(audio_path: str, output_format: str = "txt") -> None:
    agent = TranscriptionAgent()
    filename = os.path.splitext(os.path.basename(audio_path))[0]
    agent.process_and_save_transcript(audio_path, filename, output_format)
```

## Troubleshooting

Common issues and solutions:
1. AWS Credentials not found
   - Ensure AWS credentials are properly set in .env file
   - Check AWS region configuration

2. Audio processing errors
   - Verify audio file format is supported
   - Check audio file is not corrupted
   - Ensure sufficient system resources

3. Output directory issues
   - Create output directory if it doesn't exist
   - Check write permissions

For additional support, refer to the project's issue tracker or documentation. 
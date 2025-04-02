# English-Japanese Transcription Demo

A Gradio-based demo interface for the English-Japanese transcription system. This demo showcases the system's capabilities in a user-friendly web interface.

## Development Checklist

### Setup and Structure
- [x] Create project directory structure
- [x] Set up requirements.txt
- [x] Configure .gitignore
- [x] Create basic documentation

### Configuration System
- [x] Cloud service detection
- [x] Environment validation
- [x] Service status indicators
- [x] Demo-specific configuration
- [x] Configuration tests

### Audio Handling
- [x] Audio Input System
  - [x] Microphone detection
  - [x] Recording management
  - [x] File upload handling
  - [x] Audio format validation
  - [x] Recordings directory management
  - [x] Audio handler tests

### Debug and Logging
- [x] Debug System
  - [x] Custom logger setup
  - [x] Debug output formatting
  - [x] Error tracking
  - [x] Logging configuration

### Output Processing
- [x] Output Handlers
  - [x] Format processors (TXT, JSON, SRT)
  - [x] Pretty printing
  - [x] Language-specific formatting
  - [x] Output preview
  - [x] Output handler tests

### Resource Management
- [x] Resource Management
  - [x] Temporary file cleanup
  - [x] Recording cleanup
  - [x] Resource monitoring
  - [x] System health checks
- [x] Resource manager tests

### User Interface
- [x] Basic Interface
  - [x] Main application layout
  - [x] Core event handlers
  - [x] Error handling
  - [x] Component structure

- [x] Enhanced Features
  - [x] Audio playback controls
  - [x] Language selection
  - [x] Segmentation controls
  - [x] Format selection

### Error Handling
- [x] Error System
  - [x] Error Types
    - [x] Audio validation errors
    - [x] Processing errors
    - [x] Service errors
    - [x] Resource errors
    - [x] Output errors

  - [x] Error Handling
    - [x] Automatic retries
    - [x] Graceful degradation
    - [x] Resource cleanup
    - [x] User feedback

  - [x] Error Logging
    - [x] Error tracking
    - [x] Error history
    - [x] Error reporting
    - [x] Performance monitoring

### Testing and Documentation
- [x] Testing
  - [x] Component tests
  - [x] Integration tests
  - [x] Cleanup validation
  - [x] Test documentation

- [x] Final Documentation
  - [x] Update usage instructions
  - [x] Add configuration examples
  - [x] Create troubleshooting guide
  - [x] Remove this checklist

### Logging System
- [x] Log levels
- [x] Error tracking
- [x] Error history
- [x] Export functionality
- [x] Logger tests

### Demo Interface
- [x] Web UI components
- [x] Real-time transcription
- [x] Progress indicators
- [x] Error handling
- [x] Interface tests

### Documentation
- [x] API documentation
- [x] Usage examples
- [x] Configuration guide
- [x] Deployment guide

## Features

- Audio input via file upload or microphone recording
- Support for multiple audio formats (mp3, wav, m4a, flac)
- Language detection and forced language selection
- Multiple segmentation strategies
- Multiple output formats (TXT, JSON, SRT)
- Real-time service status indication
- Debug information and logging
- Resource management and cleanup

## Requirements

- Python 3.8+
- AWS or Google Cloud credentials configured
- Required Python packages (see requirements.txt)

## Installation

1. Install dependencies:
```bash
cd demo
pip install -r requirements.txt
```

2. Configure your environment variables in the root `.env` file:

```env
# Cloud Provider Selection (Required)
CLOUD_PROVIDER=aws  # or google

# AWS Configuration (Required if using AWS)
AWS_REGION=us-east-1  # Your AWS region
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Google Cloud Configuration (Required if using Google Cloud)
GOOGLE_PROJECT_ID=your_project_id
GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json

# Optional Configuration
DEBUG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
MAX_AUDIO_LENGTH=300  # Maximum audio length in seconds
CLEANUP_INTERVAL=3600  # Cleanup interval in seconds
```

## Usage

### Starting the Demo

1. Start the demo interface:
```bash
python app.py
```

2. Open your web browser to the displayed URL (typically http://127.0.0.1:7860)

### Using the Interface

1. **Audio Input**
   - Click "Record" to use your microphone
   - Click "Upload" to select an audio file
   - Supported formats: WAV, MP3, M4A, FLAC

2. **Language Settings**
   - Auto: Automatically detect language segments
   - English: Force English transcription
   - Japanese: Force Japanese transcription

3. **Output Format**
   - TXT: Plain text with proper spacing
   - JSON: Detailed transcription with timing
   - SRT: Subtitle format with timestamps

4. **Controls**
   - Transcribe: Start transcription
   - Clear: Reset the interface
   - Clear Output Files: Remove saved transcripts
   - Exit: Close the application

### Example Usage

1. **Recording Audio**
   ```python
   # 1. Click "Record"
   # 2. Speak: "Hello, world. こんにちは、世界。"
   # 3. Click "Stop"
   # 4. Select output format (e.g., "txt")
   # 5. Click "Transcribe"
   ```

2. **Uploading Audio**
   ```python
   # 1. Click "Upload"
   # 2. Select your audio file
   # 3. Choose language preference
   # 4. Select output format
   # 5. Click "Transcribe"
   ```

### Output Examples

1. **TXT Format**
```text
Hello, world. こんにちは、世界。
```

2. **JSON Format**
```json
{
  "results": {
    "transcripts": [{
      "transcript": "Hello, world. こんにちは、世界。"
    }],
    "segments": [
      {
        "start_time": "0.0",
        "end_time": "1.5",
        "text": "Hello, world.",
        "language": "en-US",
        "confidence": 0.98
      },
      {
        "start_time": "1.5",
        "end_time": "3.0",
        "text": "こんにちは、世界。",
        "language": "ja-JP",
        "confidence": 0.95
      }
    ]
  }
}
```

3. **SRT Format**
```srt
1
00:00:00,000 --> 00:00:01,500
Hello, world.

2
00:00:01,500 --> 00:00:03,000
こんにちは、世界。
```

## Configuration Examples

### AWS Configuration

1. **Basic Setup**
```env
CLOUD_PROVIDER=aws
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

2. **Advanced Setup**
```env
CLOUD_PROVIDER=aws
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
DEBUG_LEVEL=DEBUG
MAX_AUDIO_LENGTH=600
CLEANUP_INTERVAL=1800
```

### Google Cloud Configuration

1. **Basic Setup**
```env
CLOUD_PROVIDER=google
GOOGLE_PROJECT_ID=your_project_id
GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json
```

2. **Advanced Setup**
```env
CLOUD_PROVIDER=google
GOOGLE_PROJECT_ID=your_project_id
GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json
DEBUG_LEVEL=DEBUG
MAX_AUDIO_LENGTH=600
CLEANUP_INTERVAL=1800
```

## Troubleshooting

### Common Issues

1. **Microphone Not Working**
   - Check browser permissions
   - Verify system audio settings
   - Try refreshing the page

2. **Transcription Fails**
   - Check cloud credentials
   - Verify internet connection
   - Check debug logs
   - Ensure audio format is supported

3. **Output Files Missing**
   - Check write permissions
   - Verify cleanup settings
   - Check disk space

### Debug Mode

Enable debug mode by setting:
```env
DEBUG_LEVEL=DEBUG
```

Debug logs will show:
- Audio processing details
- Transcription API calls
- Language detection results
- Output formatting steps

## Testing

See [TESTING.md](TESTING.md) for detailed testing instructions.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
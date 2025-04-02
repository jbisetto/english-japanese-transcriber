# API Documentation

This document describes the key classes and methods available in the English-Japanese Transcription Demo.

## Core Components

### TranscriptionUI

Main web interface class that handles user interactions and transcription workflow.

```python
class TranscriptionUI:
    def __init__(
        self,
        audio_handler: AudioHandler,
        output_handler: OutputHandler,
        transcriber: Any,
        logger: Optional[DemoLogger] = None
    )
```

#### Methods

- `build_interface() -> gr.Blocks`: Creates and configures the Gradio interface
- `handle_transcription(audio_input: str, output_format: str) -> Tuple[str, str]`: Processes audio and returns transcription
- `handle_clear() -> Tuple[None, str, None, str]`: Resets the interface state
- `clear_files() -> Tuple[str, str]`: Cleans up output and recording files
- `cleanup_and_exit() -> bool`: Performs cleanup before application exit

### AudioHandler

Handles audio file processing and management.

```python
class AudioHandler:
    def __init__(self, recordings_dir: str = "recordings")
```

#### Methods

- `validate_format(file_path: str, mime_type: Optional[str] = None) -> bool`: Validates audio format
- `process_upload(upload_path: str) -> Dict[str, str]`: Processes uploaded audio files
- `save_recording(audio_data: np.ndarray, sample_rate: int) -> str`: Saves recorded audio
- `get_audio_info(file_path: str) -> Dict[str, Any]`: Retrieves audio file information
- `list_recordings() -> List[Dict[str, Any]]`: Lists available recordings

### OutputHandler

Manages transcription output formatting and file handling.

```python
class OutputHandler:
    def __init__(self, output_dir: str = "demo/output", logger=None)
```

#### Methods

- `format_output(transcription: Dict[str, Any], format: str = "txt") -> str`: Formats transcription output
- `save_output(transcription: Dict[str, Any], format: str = "txt") -> str`: Saves formatted output
- `generate_preview(transcription: Dict[str, Any], format: str, max_length: int = 500) -> str`: Generates output preview

### DemoLogger

Custom logger for the demo application.

```python
class DemoLogger:
    def __init__(self, name: str = "demo", level: str = "INFO")
```

#### Methods

- `debug(message: str)`: Logs debug messages
- `info(message: str)`: Logs info messages
- `warning(message: str)`: Logs warning messages
- `error(message: str)`: Logs error messages
- `export_error_history(filepath: str) -> bool`: Exports error history to file

### ResourceManager

Manages system resources and cleanup operations.

```python
class ResourceManager:
    def __init__(self, base_dir: str = "demo")
```

#### Methods

- `cleanup_resources() -> bool`: Performs resource cleanup
- `check_system_health() -> Dict[str, Any]`: Checks system resource usage
- `monitor_resources() -> None`: Monitors resource usage
- `emergency_cleanup() -> bool`: Performs emergency cleanup

## Error Types

```python
class AudioValidationError(Exception):
    """Raised when audio validation fails."""

class AudioProcessingError(Exception):
    """Raised when audio processing fails."""

class TranscriptionError(Exception):
    """Raised when transcription fails."""

class OutputFormatError(Exception):
    """Raised when output formatting fails."""

class ResourceError(Exception):
    """Raised when resource management fails."""
```

## Usage Examples

### Basic Transcription

```python
from demo.interface.web_ui import TranscriptionUI
from demo.handlers import AudioHandler, OutputHandler
from demo.utils.logger import DemoLogger

# Initialize handlers
audio_handler = AudioHandler()
output_handler = OutputHandler()
logger = DemoLogger()

# Create UI
ui = TranscriptionUI(audio_handler, output_handler, logger)

# Build and launch interface
interface = ui.build_interface()
interface.launch()
```

### Custom Configuration

```python
from demo.config import DemoConfig
from demo.utils.service_detector import ServiceDetector

# Load configuration
config = DemoConfig()

# Detect service provider
detector = ServiceDetector()
service = detector.detect_provider()

# Initialize with custom paths
audio_handler = AudioHandler(recordings_dir="custom/recordings")
output_handler = OutputHandler(output_dir="custom/output")
logger = DemoLogger(level="DEBUG")

# Create UI with custom configuration
ui = TranscriptionUI(
    audio_handler=audio_handler,
    output_handler=output_handler,
    logger=logger
)
```

### Direct API Usage

```python
# Process audio file
audio_path = "input.wav"
result = audio_handler.process_upload(audio_path)

# Format output
transcription = {
    "results": {
        "transcripts": [{
            "transcript": "Hello, world. こんにちは、世界。"
        }],
        "segments": [...]
    }
}

# Get different formats
txt_output = output_handler.format_output(transcription, "txt")
json_output = output_handler.format_output(transcription, "json")
srt_output = output_handler.format_output(transcription, "srt")

# Save output
output_path = output_handler.save_output(transcription, "txt")
``` 
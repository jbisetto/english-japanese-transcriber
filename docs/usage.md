# Usage

## Transcribing Audio Files

To transcribe an audio file, you can use the `TranscriptionAgent` class. Here's an example:

```python
from src.agent import TranscriptionAgent

if __name__ == '__main__':
    # Example usage
    agent = TranscriptionAgent()
    audio_path = "examples/sample_audio/sample.mp3"  # Replace with your audio file
    filename = "simple_transcription"
    agent.process_and_save_transcript(audio_path, filename, format="txt")
```

1.  Import the `TranscriptionAgent` class from `src/agent.py`.
2.  Create an instance of the `TranscriptionAgent` class.
3.  Specify the path to the audio file you want to transcribe.
4.  Specify the filename for the output transcript.
5.  Call the `process_and_save_transcript()` method to transcribe the audio file and save the transcript to a file.

## Configuration

The project uses configuration classes to store settings. You can modify the settings in the `src/config.py` file.

### AWS Configuration

To configure the AWS settings, you can modify the `AWSConfig` class in `src/config.py`. You need to set the `region_name` attribute to your AWS region.

```python
class AWSConfig(Config):
    def __init__(self, region_name: Optional[str] = None):
        self.region_name = region_name or os.environ.get("AWS_REGION_NAME", "us-east-1")
```

### Audio Configuration

To configure the audio settings, you can modify the `AudioConfig` class in `src/config.py`. You can set the `target_sample_rate` and `target_channels` attributes.

```python
class AudioConfig(Config):
    def __init__(self, target_sample_rate: int = 16000, target_channels: int = 1):
        self.target_sample_rate = target_sample_rate
        self.target_channels = target_channels
```

### Transcription Configuration

To configure the transcription settings, you can modify the `TranscriptionConfig` class in `src/config.py`. You can set the `english_model_id` and `japanese_model_id` attributes to the model IDs for English and Japanese transcription, respectively.

```python
class TranscriptionConfig(Config):
    def __init__(self, english_model_id: str = "anthropic.claude-v2", japanese_model_id: str = "anthropic.claude-v2"):
        self.english_model_id = english_model_id
        self.japanese_model_id = japanese_model_id
```

### Language Detection Configuration

To configure the language detection settings, you can modify the `LanguageDetectionConfig` class in `src/config.py`. You can set the `model_id` attribute to the model ID for language detection.

```python
class LanguageDetectionConfig(Config):
    def __init__(self, model_id: str = "amazon.comprehend"):
        self.model_id = model_id
```

### Output Configuration

To configure the output settings, you can modify the `OutputConfig` class in `src/config.py`. You can set the `output_dir` attribute to the directory where the transcripts will be saved.

```python
class OutputConfig(Config):
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir

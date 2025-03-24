import os
from typing import Optional

class Config:
    """
    Base configuration class.
    """
    def __init__(self):
        pass

class AWSConfig(Config):
    """
    Configuration class for AWS settings.
    """
    def __init__(self, region_name: Optional[str] = None):
        """
        Initializes the AWSConfig.

        Args:
            region_name (str, optional): The AWS region name. Defaults to None, which uses the default region.
        """
        super().__init__()
        self.region_name = region_name or os.environ.get("AWS_REGION_NAME")

class AudioConfig(Config):
    """
    Configuration class for audio processing settings.
    """
    def __init__(self, target_sample_rate: int = 16000, target_channels: int = 1):
        """
        Initializes the AudioConfig.

        Args:
            target_sample_rate (int, optional): The target sample rate in Hz. Defaults to 16000.
            target_channels (int, optional): The target number of channels. Defaults to 1.
        """
        super().__init__()
        self.target_sample_rate = target_sample_rate
        self.target_channels = target_channels

class TranscriptionConfig(Config):
    """
    Configuration class for transcription settings.
    """
    def __init__(self, english_model_id: str = "anthropic.claude-v2", japanese_model_id: str = "anthropic.claude-v2"):
        """
        Initializes the TranscriptionConfig.

        Args:
            english_model_id (str, optional): The model ID for English transcription.
            japanese_model_id (str, optional): The model ID for Japanese transcription.
        """
        super().__init__()
        self.english_model_id = english_model_id
        self.japanese_model_id = japanese_model_id

class LanguageDetectionConfig(Config):
    """
    Configuration class for language detection settings.
    """
    def __init__(self, model_id: str = "amazon.comprehend"):
        """
        Initializes the LanguageDetectionConfig.

        Args:
            model_id (str, optional): The model ID for language detection.
        """
        super().__init__()
        self.model_id = model_id

class OutputConfig(Config):
    """
    Configuration class for output settings.
    """
    def __init__(self, output_dir: str = "output"):
        """
        Initializes the OutputConfig.

        Args:
            output_dir (str, optional): The directory to save output files.
        """
        super().__init__()
        self.output_dir = output_dir

if __name__ == '__main__':
    # Example usage
    aws_config = AWSConfig(region_name="us-west-2")
    audio_config = AudioConfig(target_sample_rate=44100, target_channels=2)
    transcription_config = TranscriptionConfig(english_model_id="anthropic.claude-v2:1", japanese_model_id="anthropic.claude-v2:1")
    language_detection_config = LanguageDetectionConfig(model_id="amazon.comprehend:1")
    output_config = OutputConfig(output_dir="transcriptions")

    print(f"AWS Region: {aws_config.region_name}")
    print(f"Audio Sample Rate: {audio_config.target_sample_rate}")
    print(f"English Model ID: {transcription_config.english_model_id}")
    print(f"Language Detection Model ID: {language_detection_config.model_id}")
    print(f"Output Directory: {output_config.output_dir}")

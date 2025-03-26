import os
from typing import Optional, Dict, Type
from dotenv import load_dotenv
from enum import Enum
from abc import ABC, abstractmethod

# Load environment variables
load_dotenv()

class CloudProvider(Enum):
    """Enum for supported cloud providers."""
    AWS = "aws"
    GOOGLE = "google"

class BaseConfig(ABC):
    """Abstract base configuration class."""
    @abstractmethod
    def validate(self) -> None:
        """Validate the configuration."""
        pass

class CloudServiceConfig(BaseConfig):
    """Base class for cloud service configurations."""
    def __init__(self, provider: CloudProvider):
        self.provider = provider

    @abstractmethod
    def get_credentials(self) -> Dict[str, str]:
        """Get the credentials for the cloud service."""
        pass

class AWSConfig(CloudServiceConfig):
    """Configuration class for AWS settings."""
    def __init__(self):
        """Initialize AWS configuration from environment variables."""
        super().__init__(CloudProvider.AWS)
        self.access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region_name = os.getenv("AWS_REGION", "us-east-1")
        self.s3_bucket = os.getenv("AWS_S3_BUCKET")
        
        # Service-specific configurations
        self.bedrock = AWSBedrockConfig()
        self.s3 = AWSS3Config()

    def validate(self) -> None:
        """Validate AWS configuration."""
        missing = []
        if not self.access_key_id:
            missing.append("AWS_ACCESS_KEY_ID")
        if not self.secret_access_key:
            missing.append("AWS_SECRET_ACCESS_KEY")
        if not self.s3_bucket:
            missing.append("AWS_S3_BUCKET")
        
        if missing:
            raise ValueError(f"Missing required AWS configuration: {', '.join(missing)}")
        
        # Validate service-specific configs
        self.bedrock.validate()
        self.s3.validate()

    def get_credentials(self) -> Dict[str, str]:
        """Get AWS credentials."""
        return {
            "aws_access_key_id": self.access_key_id,
            "aws_secret_access_key": self.secret_access_key,
            "region_name": self.region_name
        }

class GoogleConfig(CloudServiceConfig):
    """Configuration class for Google Cloud settings."""
    def __init__(self):
        """Initialize Google Cloud configuration from environment variables."""
        super().__init__(CloudProvider.GOOGLE)
        self.credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        
        # Service-specific configurations
        self.storage = GoogleStorageConfig()
        self.speech = GoogleSpeechConfig()
        self.translate = GoogleTranslateConfig()

    def validate(self) -> None:
        """Validate Google Cloud configuration."""
        missing = []
        if not self.credentials_path:
            missing.append("GOOGLE_APPLICATION_CREDENTIALS")
        if not self.project_id:
            missing.append("GOOGLE_CLOUD_PROJECT")
            
        if missing:
            raise ValueError(f"Missing required Google Cloud configuration: {', '.join(missing)}")
        
        # Validate service-specific configs
        self.storage.validate()
        self.speech.validate()
        self.translate.validate()

    def get_credentials(self) -> Dict[str, str]:
        """Get Google Cloud credentials."""
        return {
            "credentials_path": self.credentials_path,
            "project_id": self.project_id
        }

# Service-specific configuration classes
class AWSBedrockConfig(BaseConfig):
    """Configuration for AWS Bedrock service."""
    def __init__(self):
        self.english_model_id = os.getenv("AWS_BEDROCK_ENGLISH_MODEL_ID", "anthropic.claude-v2")
        self.japanese_model_id = os.getenv("AWS_BEDROCK_JAPANESE_MODEL_ID", "anthropic.claude-v2")

    def validate(self) -> None:
        if not self.english_model_id or not self.japanese_model_id:
            raise ValueError("Missing required Bedrock model IDs")

class AWSS3Config(BaseConfig):
    """Configuration for AWS S3 service."""
    def __init__(self):
        self.bucket = os.getenv("AWS_S3_BUCKET")

    def validate(self) -> None:
        if not self.bucket:
            raise ValueError("Missing required S3 bucket configuration")

class GoogleStorageConfig(BaseConfig):
    """Configuration for Google Cloud Storage service."""
    def __init__(self):
        self.bucket = os.getenv("GOOGLE_STORAGE_BUCKET")

    def validate(self) -> None:
        if not self.bucket:
            raise ValueError("Missing required Google Storage bucket configuration")

class GoogleSpeechConfig(BaseConfig):
    """Configuration for Google Cloud Speech-to-Text service."""
    def __init__(self):
        self.model = os.getenv("GOOGLE_SPEECH_MODEL", "default")

    def validate(self) -> None:
        pass  # Using default model if not specified

class GoogleTranslateConfig(BaseConfig):
    """Configuration for Google Cloud Translate service."""
    def __init__(self):
        self.model = os.getenv("GOOGLE_TRANSLATION_MODEL", "nmt")

    def validate(self) -> None:
        pass  # Using default model if not specified

class AudioConfig(BaseConfig):
    """Configuration class for audio processing settings."""
    def __init__(self):
        """Initialize audio configuration from environment variables."""
        self.target_sample_rate = int(os.getenv("TARGET_SAMPLE_RATE", "16000"))
        self.target_channels = int(os.getenv("TARGET_CHANNELS", "1"))
        self.min_silence_len = int(os.getenv("MIN_SILENCE_LEN", "700"))
        self.silence_thresh = int(os.getenv("SILENCE_THRESH", "-16"))
        self.segment_duration = int(os.getenv("SEGMENT_DURATION", "10000"))

    def validate(self) -> None:
        """Validate audio configuration."""
        if self.target_sample_rate <= 0:
            raise ValueError("Sample rate must be positive")
        if self.target_channels <= 0:
            raise ValueError("Number of channels must be positive")

class OutputConfig(BaseConfig):
    """Configuration class for output settings."""
    def __init__(self):
        """Initialize output configuration from environment variables."""
        self.output_dir = os.getenv("OUTPUT_DIR", "output")

    def validate(self) -> None:
        """Validate output configuration."""
        if not self.output_dir:
            raise ValueError("Output directory must be specified")

class ConfigFactory:
    """Factory class for creating configurations."""
    _providers: Dict[CloudProvider, Type[CloudServiceConfig]] = {
        CloudProvider.AWS: AWSConfig,
        CloudProvider.GOOGLE: GoogleConfig
    }

    @classmethod
    def get_cloud_config(cls) -> CloudServiceConfig:
        """Get the appropriate cloud service configuration."""
        provider_name = os.getenv("CLOUD_PROVIDER", "aws").lower()
        try:
            provider = CloudProvider(provider_name)
        except ValueError:
            raise ValueError(f"Unsupported cloud provider: {provider_name}")

        config_class = cls._providers.get(provider)
        if not config_class:
            raise ValueError(f"No configuration class found for provider: {provider}")

        config = config_class()
        config.validate()
        return config

    @classmethod
    def register_provider(cls, provider: CloudProvider, config_class: Type[CloudServiceConfig]) -> None:
        """Register a new cloud provider configuration."""
        cls._providers[provider] = config_class

if __name__ == '__main__':
    # Example usage
    try:
        # Get configurations
        cloud_config = ConfigFactory.get_cloud_config()
        audio_config = AudioConfig()
        output_config = OutputConfig()

        # Validate all configurations
        audio_config.validate()
        output_config.validate()

        # Print configuration details
        if isinstance(cloud_config, AWSConfig):
            print("Using AWS Configuration:")
            print(f"Region: {cloud_config.region_name}")
            print(f"S3 Bucket: {cloud_config.s3.bucket}")
            print(f"English Model: {cloud_config.bedrock.english_model_id}")
        else:
            print("Using Google Cloud Configuration:")
            print(f"Project ID: {cloud_config.project_id}")
            print(f"Storage Bucket: {cloud_config.storage.bucket}")
            print(f"Speech Model: {cloud_config.speech.model}")

        print("\nAudio Configuration:")
        print(f"Sample Rate: {audio_config.target_sample_rate}")
        print(f"Channels: {audio_config.target_channels}")

        print("\nOutput Configuration:")
        print(f"Output Directory: {output_config.output_dir}")

    except ValueError as e:
        print(f"Configuration Error: {e}")

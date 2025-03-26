import os
import pytest
from unittest.mock import patch
from src.config import (
    CloudProvider,
    ConfigFactory,
    AWSConfig,
    GoogleConfig,
    AudioConfig,
    OutputConfig,
    AWSBedrockConfig,
    AWSS3Config,
    GoogleStorageConfig,
    GoogleSpeechConfig,
    GoogleTranslateConfig
)

@pytest.fixture
def aws_env_vars():
    """Fixture for AWS environment variables."""
    return {
        "CLOUD_PROVIDER": "aws",
        "AWS_ACCESS_KEY_ID": "test_access_key",
        "AWS_SECRET_ACCESS_KEY": "test_secret_key",
        "AWS_REGION": "us-west-2",
        "AWS_S3_BUCKET": "test-bucket",
        "AWS_BEDROCK_ENGLISH_MODEL_ID": "test-english-model",
        "AWS_BEDROCK_JAPANESE_MODEL_ID": "test-japanese-model"
    }

@pytest.fixture
def google_env_vars():
    """Fixture for Google Cloud environment variables."""
    return {
        "CLOUD_PROVIDER": "google",
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/credentials.json",
        "GOOGLE_CLOUD_PROJECT": "test-project",
        "GOOGLE_STORAGE_BUCKET": "test-bucket",
        "GOOGLE_SPEECH_MODEL": "test-model",
        "GOOGLE_TRANSLATION_MODEL": "test-translation"
    }

@pytest.fixture
def audio_env_vars():
    """Fixture for audio configuration environment variables."""
    return {
        "TARGET_SAMPLE_RATE": "44100",
        "TARGET_CHANNELS": "2",
        "MIN_SILENCE_LEN": "1000",
        "SILENCE_THRESH": "-20",
        "SEGMENT_DURATION": "15000"
    }

class TestCloudProvider:
    def test_valid_providers(self):
        """Test that valid cloud providers are correctly enumerated."""
        assert CloudProvider.AWS.value == "aws"
        assert CloudProvider.GOOGLE.value == "google"

    def test_invalid_provider(self):
        """Test that invalid provider names raise ValueError."""
        with pytest.raises(ValueError):
            CloudProvider("invalid")

class TestAWSConfig:
    def test_aws_config_valid(self, aws_env_vars):
        """Test AWS configuration with valid environment variables."""
        with patch.dict(os.environ, aws_env_vars):
            config = AWSConfig()
            config.validate()
            
            assert config.provider == CloudProvider.AWS
            assert config.access_key_id == "test_access_key"
            assert config.secret_access_key == "test_secret_key"
            assert config.region_name == "us-west-2"
            assert config.s3_bucket == "test-bucket"
            
            # Test credentials dictionary
            creds = config.get_credentials()
            assert creds["aws_access_key_id"] == "test_access_key"
            assert creds["aws_secret_access_key"] == "test_secret_key"
            assert creds["region_name"] == "us-west-2"

    def test_aws_config_missing_required(self):
        """Test AWS configuration with missing required variables."""
        with patch.dict(os.environ, {}, clear=True):
            config = AWSConfig()
            with pytest.raises(ValueError) as exc:
                config.validate()
            assert "Missing required AWS configuration" in str(exc.value)

    def test_aws_bedrock_config(self, aws_env_vars):
        """Test AWS Bedrock configuration."""
        with patch.dict(os.environ, aws_env_vars):
            config = AWSBedrockConfig()
            config.validate()
            assert config.english_model_id == "test-english-model"
            assert config.japanese_model_id == "test-japanese-model"

class TestGoogleConfig:
    def test_google_config_valid(self, google_env_vars):
        """Test Google Cloud configuration with valid environment variables."""
        with patch.dict(os.environ, google_env_vars):
            config = GoogleConfig()
            config.validate()
            
            assert config.provider == CloudProvider.GOOGLE
            assert config.credentials_path == "/path/to/credentials.json"
            assert config.project_id == "test-project"
            assert config.storage.bucket == "test-bucket"
            assert config.speech.model == "test-model"
            
            # Test credentials dictionary
            creds = config.get_credentials()
            assert creds["credentials_path"] == "/path/to/credentials.json"
            assert creds["project_id"] == "test-project"

    def test_google_config_missing_required(self):
        """Test Google Cloud configuration with missing required variables."""
        with patch.dict(os.environ, {}, clear=True):
            config = GoogleConfig()
            with pytest.raises(ValueError) as exc:
                config.validate()
            assert "Missing required Google Cloud configuration" in str(exc.value)

class TestAudioConfig:
    def test_audio_config_valid(self, audio_env_vars):
        """Test audio configuration with valid environment variables."""
        with patch.dict(os.environ, audio_env_vars):
            config = AudioConfig()
            config.validate()
            
            assert config.target_sample_rate == 44100
            assert config.target_channels == 2
            assert config.min_silence_len == 1000
            assert config.silence_thresh == -20
            assert config.segment_duration == 15000

    def test_audio_config_defaults(self):
        """Test audio configuration with default values."""
        with patch.dict(os.environ, {}, clear=True):
            config = AudioConfig()
            config.validate()
            
            assert config.target_sample_rate == 16000
            assert config.target_channels == 1
            assert config.min_silence_len == 700
            assert config.silence_thresh == -16
            assert config.segment_duration == 10000

    def test_audio_config_invalid_values(self):
        """Test audio configuration with invalid values."""
        with patch.dict(os.environ, {"TARGET_SAMPLE_RATE": "0", "TARGET_CHANNELS": "-1"}):
            config = AudioConfig()
            with pytest.raises(ValueError):
                config.validate()

class TestConfigFactory:
    def test_get_aws_config(self, aws_env_vars):
        """Test ConfigFactory returns correct AWS configuration."""
        with patch.dict(os.environ, aws_env_vars):
            config = ConfigFactory.get_cloud_config()
            assert isinstance(config, AWSConfig)
            assert config.provider == CloudProvider.AWS

    def test_get_google_config(self, google_env_vars):
        """Test ConfigFactory returns correct Google configuration."""
        with patch.dict(os.environ, google_env_vars):
            config = ConfigFactory.get_cloud_config()
            assert isinstance(config, GoogleConfig)
            assert config.provider == CloudProvider.GOOGLE

    def test_invalid_provider(self):
        """Test ConfigFactory handles invalid provider."""
        with patch.dict(os.environ, {"CLOUD_PROVIDER": "invalid"}):
            with pytest.raises(ValueError) as exc:
                ConfigFactory.get_cloud_config()
            assert "Unsupported cloud provider" in str(exc.value)

    def test_register_new_provider(self):
        """Test registering a new provider."""
        class MockConfig(GoogleConfig):
            pass

        # Register new provider
        mock_provider = CloudProvider("google")  # Using existing enum for test
        ConfigFactory.register_provider(mock_provider, MockConfig)
        
        # Verify registration
        assert ConfigFactory._providers[mock_provider] == MockConfig 
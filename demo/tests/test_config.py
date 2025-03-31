"""Tests for the demo configuration system."""

import os
import unittest
from unittest.mock import patch
from pathlib import Path

# Add demo directory to path
import sys
demo_path = Path(__file__).parent.parent
sys.path.append(str(demo_path))

from config import CloudProvider, ServiceDetector, DemoConfig

class TestCloudProvider(unittest.TestCase):
    """Tests for the CloudProvider enum."""
    
    def test_cloud_provider_values(self):
        """Test cloud provider enum values."""
        self.assertEqual(CloudProvider.AWS.value, "aws")
        self.assertEqual(CloudProvider.GOOGLE.value, "google")
        self.assertEqual(CloudProvider.UNKNOWN.value, "unknown")

class TestDemoConfig(unittest.TestCase):
    """Tests for the DemoConfig class."""
    
    def test_supported_formats(self):
        """Test supported audio formats."""
        config = DemoConfig()
        self.assertIn("mp3", config.supported_formats)
        self.assertIn("wav", config.supported_formats)
        self.assertIn("m4a", config.supported_formats)
        self.assertIn("flac", config.supported_formats)
    
    def test_language_options(self):
        """Test language options."""
        config = DemoConfig()
        self.assertIn("auto-detect", config.language_options)
        self.assertIn("force-english", config.language_options)
        self.assertIn("force-japanese", config.language_options)

class TestServiceDetector(unittest.TestCase):
    """Tests for the ServiceDetector class."""
    
    def setUp(self):
        """Set up test environment."""
        # Clear relevant environment variables
        for key in ["CLOUD_PROVIDER", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",
                   "AWS_REGION_NAME", "GOOGLE_PROJECT_ID", "GOOGLE_CREDENTIALS_PATH"]:
            if key in os.environ:
                del os.environ[key]
    
    def test_detect_provider_explicit_aws(self):
        """Test explicit AWS provider detection."""
        with patch.dict(os.environ, {"CLOUD_PROVIDER": "aws"}):
            provider = ServiceDetector.detect_provider()
            self.assertEqual(provider, CloudProvider.AWS)
    
    def test_detect_provider_explicit_google(self):
        """Test explicit Google provider detection."""
        with patch.dict(os.environ, {"CLOUD_PROVIDER": "google"}):
            provider = ServiceDetector.detect_provider()
            self.assertEqual(provider, CloudProvider.GOOGLE)
    
    def test_detect_provider_aws_credentials(self):
        """Test AWS provider detection from credentials."""
        aws_env = {
            "AWS_ACCESS_KEY_ID": "test_key",
            "AWS_SECRET_ACCESS_KEY": "test_secret",
            "AWS_REGION_NAME": "us-east-1"
        }
        with patch.dict(os.environ, aws_env):
            provider = ServiceDetector.detect_provider()
            self.assertEqual(provider, CloudProvider.AWS)
    
    def test_detect_provider_google_credentials(self):
        """Test Google provider detection from credentials."""
        google_env = {
            "GOOGLE_PROJECT_ID": "test_project",
            "GOOGLE_CREDENTIALS_PATH": "/path/to/credentials.json"
        }
        with patch.dict(os.environ, google_env):
            provider = ServiceDetector.detect_provider()
            self.assertEqual(provider, CloudProvider.GOOGLE)
    
    def test_detect_provider_unknown(self):
        """Test unknown provider detection."""
        provider = ServiceDetector.detect_provider()
        self.assertEqual(provider, CloudProvider.UNKNOWN)
    
    def test_get_service_status(self):
        """Test service status information."""
        status = ServiceDetector.get_service_status()
        self.assertIn("provider", status)
        self.assertIn("is_valid", status)
        self.assertIn("status_message", status)
        self.assertIn("debug_mode", status)

if __name__ == "__main__":
    unittest.main() 
"""
Configuration system for the English-Japanese Transcription Demo.

This module handles:
- Demo-specific configuration
- Cloud service detection
- Environment validation
- Service status indicators
"""

import os
from enum import Enum
from typing import Optional, List
from dataclasses import dataclass, field
from pathlib import Path

# Import the main project's configuration
import sys
sys.path.append(str(Path(__file__).parent.parent))
from src.config import ConfigFactory as ProjectConfigFactory

class CloudProvider(Enum):
    """Supported cloud providers."""
    AWS = "aws"
    GOOGLE = "google"
    UNKNOWN = "unknown"

@dataclass
class DemoConfig:
    """Configuration for the demo interface."""
    
    supported_formats: List[str] = field(default_factory=lambda: ["mp3", "wav", "m4a", "flac"])
    language_options: List[str] = field(default_factory=lambda: ["auto-detect", "force-english", "force-japanese"])
    
    # Thresholds for resource management
    disk_threshold: float = 90.0  # Percentage
    memory_threshold: float = 80.0  # Percentage
    min_free_space: float = 500.0  # MB
    
    # Audio settings
    MAX_DURATION_SECONDS: int = 300  # 5 minutes max for JLPT N5 level content
    TEMP_RECORDING_PATH: str = str(Path(__file__).parent / "recordings" / "temp_recording.wav")
    
    # UI settings
    SEGMENTATION_OPTIONS: tuple = ("silence-based", "fixed-length", "energy-based")
    OUTPUT_FORMATS: tuple = ("txt", "json", "srt")
    
    # Debug settings
    DEBUG_MODE: bool = False
    LOG_FILE: str = str(Path(__file__).parent / "demo_debug.log")

class ServiceDetector:
    """Detects and validates cloud service configuration."""
    
    @staticmethod
    def detect_provider() -> CloudProvider:
        """
        Detects which cloud provider is configured based on environment variables.
        
        Returns:
            CloudProvider: The detected cloud provider.
        """
        # Check explicit provider setting
        provider = os.getenv("CLOUD_PROVIDER", "").lower()
        if provider in [CloudProvider.AWS.value, CloudProvider.GOOGLE.value]:
            return CloudProvider(provider)
            
        # Check AWS credentials
        if all(os.getenv(key) for key in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION_NAME"]):
            return CloudProvider.AWS
            
        # Check Google credentials
        if all(os.getenv(key) for key in ["GOOGLE_PROJECT_ID", "GOOGLE_CREDENTIALS_PATH"]):
            return CloudProvider.GOOGLE
            
        return CloudProvider.UNKNOWN

    @staticmethod
    def validate_configuration() -> tuple[bool, str]:
        """
        Validates the current configuration.
        
        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        provider = ServiceDetector.detect_provider()
        
        if provider == CloudProvider.UNKNOWN:
            return False, "No valid cloud provider configuration detected"
            
        try:
            # Try to get configuration from main project
            ProjectConfigFactory.get_config()
            return True, f"Using {provider.value} configuration"
        except Exception as e:
            return False, f"Configuration error: {str(e)}"

    @staticmethod
    def get_service_status() -> dict:
        """
        Gets the current service status.
        
        Returns:
            dict: Service status information
        """
        is_valid, message = ServiceDetector.validate_configuration()
        provider = ServiceDetector.detect_provider()
        
        return {
            "provider": provider.value,
            "is_valid": is_valid,
            "status_message": message,
            "debug_mode": DemoConfig.DEBUG_MODE
        }

if __name__ == "__main__":
    # Example usage
    status = ServiceDetector.get_service_status()
    print(f"Cloud Provider: {status['provider']}")
    print(f"Valid Config: {status['is_valid']}")
    print(f"Status: {status['status_message']}") 
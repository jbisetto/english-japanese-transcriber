"""Error types for the demo application.

This module defines all custom exceptions used throughout the demo interface,
providing a centralized location for error handling and classification.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ErrorContext:
    """Context information for errors."""
    timestamp: datetime
    component: str
    operation: str
    details: Dict[str, Any]

class DemoError(Exception):
    """Base exception for all demo-related errors."""
    
    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        super().__init__(message)
        self.context = context
        self.timestamp = datetime.now()
        
    @property
    def user_message(self) -> str:
        """Returns a user-friendly error message."""
        return str(self)

class TranscriptionError(DemoError):
    """Raised when transcription fails."""
    
    @property
    def user_message(self) -> str:
        return "Failed to transcribe audio. Please ensure the audio is clear and try again."

class LanguageDetectionError(DemoError):
    """Raised when language detection fails."""
    
    @property
    def user_message(self) -> str:
        return "Could not detect the language. Please try selecting a specific language."

class ServiceUnavailableError(DemoError):
    """Raised when a required service is unavailable."""
    
    @property
    def user_message(self) -> str:
        return "Service temporarily unavailable. Please try again in a few minutes."

class RetryableError(DemoError):
    """Base class for errors that can be automatically retried."""
    
    def __init__(self, message: str, context: Optional[ErrorContext] = None, max_retries: int = 3):
        super().__init__(message, context)
        self.max_retries = max_retries

class NetworkError(RetryableError):
    """Raised when network operations fail."""
    
    @property
    def user_message(self) -> str:
        return "Network connection issue. Retrying automatically..."

class RateLimitError(RetryableError):
    """Raised when API rate limits are exceeded."""
    
    @property
    def user_message(self) -> str:
        return "Service is busy. Waiting to retry..."

# Update existing error types to inherit from DemoError
class AudioValidationError(DemoError):
    """Raised when audio validation fails."""
    
    @property
    def user_message(self) -> str:
        return f"Invalid audio file: {str(self)}. Please check the supported formats."

class AudioProcessingError(DemoError):
    """Raised when audio processing fails."""
    
    @property
    def user_message(self) -> str:
        return f"Could not process audio: {str(self)}. Please try a different file."

class OutputFormatError(DemoError):
    """Raised when output formatting fails."""
    
    @property
    def user_message(self) -> str:
        return f"Output formatting failed: {str(self)}. Please try a different format."

class ResourceError(DemoError):
    """Raised when resource management fails."""
    
    @property
    def user_message(self) -> str:
        return "System resource issue. Please try again or contact support." 
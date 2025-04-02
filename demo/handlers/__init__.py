"""Audio and output handling package for the demo interface."""

from ..utils.errors import (
    DemoError,
    AudioValidationError,
    AudioProcessingError,
    OutputFormatError,
    TranscriptionError,
    LanguageDetectionError,
    ServiceUnavailableError,
    ResourceError
)

from .audio_handler import AudioHandler
from .output_handler import OutputHandler

__all__ = [
    'AudioHandler',
    'OutputHandler',
    'DemoError',
    'AudioValidationError',
    'AudioProcessingError',
    'OutputFormatError',
    'TranscriptionError',
    'LanguageDetectionError',
    'ServiceUnavailableError',
    'ResourceError'
]

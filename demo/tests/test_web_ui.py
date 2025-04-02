"""Tests for the web interface components."""

import pytest
import gradio as gr
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from demo.interface.web_ui import TranscriptionUI
from demo.handlers import AudioHandler, OutputHandler
from demo.utils.logger import DemoLogger
from demo.utils.errors import AudioValidationError, TranscriptionError

@pytest.fixture
def audio_handler():
    """Create a mock audio handler."""
    handler = Mock(spec=AudioHandler)
    handler.process_upload.return_value = {
        'transcription': 'test_transcription.wav',
        'playback': 'test_playback.wav'
    }
    handler.get_audio_info.return_value = {'duration': 10.0, 'format': 'wav'}
    return handler

@pytest.fixture
def output_handler():
    """Create a mock output handler."""
    handler = Mock(spec=OutputHandler)
    handler.format_output.return_value = "Test transcription output"
    handler.save_output.return_value = "test_output.txt"
    return handler

@pytest.fixture
def transcriber():
    """Create a mock transcriber."""
    transcriber = AsyncMock()
    transcriber.transcribe.return_value = {
        "results": {
            "transcripts": [{"transcript": "Test transcription"}],
            "segments": [
                {
                    "start_time": "0.0",
                    "end_time": "2.0",
                    "text": "Test transcription",
                    "confidence": 0.95,
                    "language": "en-US"
                }
            ]
        }
    }
    return transcriber

@pytest.fixture
def logger():
    """Create a mock logger."""
    return Mock(spec=DemoLogger)

@pytest.fixture
def ui(audio_handler, output_handler, transcriber, logger):
    """Create a TranscriptionUI instance for testing."""
    return TranscriptionUI(audio_handler, output_handler, transcriber, logger)

def test_init(ui):
    """Test initialization of TranscriptionUI."""
    assert ui.audio_handler is not None
    assert ui.output_handler is not None
    assert ui.transcriber is not None
    assert ui.logger is not None
    assert ui.current_operation is None
    assert ui.operation_start_time is None

def test_build_interface(ui):
    """Test building the Gradio interface."""
    interface = ui.build_interface()
    assert isinstance(interface, gr.Blocks)
    assert ui.error_box is not None
    assert ui.status_box is not None
    assert ui.progress_bar is not None

@pytest.mark.asyncio
async def test_handle_transcription_no_audio(ui):
    """Test transcription handling with no audio."""
    output, error = await ui.handle_transcription(None, "txt")
    assert output == ""
    assert "Please provide an audio file" in error

@pytest.mark.asyncio
async def test_handle_transcription_with_audio(ui, audio_handler, output_handler, transcriber):
    """Test transcription handling with audio."""
    # Test successful transcription
    output, error = await ui.handle_transcription("test.wav", "txt")
    assert output == "Test transcription output"
    assert error == ""
    
    # Verify calls
    audio_handler.process_upload.assert_called_once_with("test.wav")
    transcriber.transcribe.assert_any_call(
        audio_path="test_transcription.wav",
        language_code="en-US"
    )
    transcriber.transcribe.assert_any_call(
        audio_path="test_transcription.wav",
        language_code="ja-JP"
    )
    output_handler.format_output.assert_called_once()
    output_handler.save_output.assert_called_once()

@pytest.mark.asyncio
async def test_handle_transcription_with_errors(ui, audio_handler):
    """Test transcription handling with various errors."""
    audio_path = "test.wav"
    
    # Test audio validation error
    audio_handler.process_upload.side_effect = AudioValidationError("Invalid audio")
    output, error = await ui.handle_transcription(audio_path, "txt")
    assert output == ""
    assert "Invalid audio" in error
    
    # Test transcription error
    audio_handler.process_upload.side_effect = None
    ui.transcriber.transcribe.side_effect = TranscriptionError("Failed to transcribe")
    output, error = await ui.handle_transcription(audio_path, "txt")
    assert output == ""
    assert "Failed to transcribe" in error

def test_handle_clear(ui):
    """Test clearing the interface."""
    result = ui.handle_clear()
    assert result == (None, "", None, "")
    assert ui.current_operation is None
    assert ui.operation_start_time is None

def test_update_status(ui, audio_handler):
    """Test status updates."""
    # Test with no audio
    status = ui.update_status(None)
    assert "Waiting for audio input" in status
    
    # Test with valid audio
    status = ui.update_status("test.wav")
    assert "Audio loaded" in status
    
    # Test with invalid audio
    audio_handler.get_audio_info.side_effect = Exception("Invalid audio")
    status = ui.update_status("invalid.wav")
    assert "Invalid audio file" in status

def test_progress_updates(ui):
    """Test progress bar updates."""
    # Setup mock progress bar
    ui.progress_bar = Mock()
    ui.status_box = Mock()
    
    # Test progress updates
    ui.progress(0.5, "Testing progress")
    ui.progress_bar.assert_called_once_with(0.5, desc="Testing progress")
    ui.status_box.update.assert_called_once_with(value="Testing progress")

def test_clear_files(ui):
    """Test clearing output files."""
    status, error = ui.clear_files()
    assert "All output and recording files cleared" in status
    assert error == ""

@pytest.mark.asyncio
async def test_cleanup_and_exit(ui):
    """Test cleanup and exit."""
    cleanup_gen = ui.cleanup_and_exit()
    
    # First yield should hide the button
    assert next(cleanup_gen) is False
    
    # Second yield should show the button again
    assert next(cleanup_gen) is True 
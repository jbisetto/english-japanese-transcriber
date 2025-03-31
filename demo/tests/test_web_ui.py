"""Tests for the web interface components."""

import pytest
import gradio as gr
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

from demo.interface.web_ui import TranscriptionUI
from demo.handlers import AudioHandler, OutputHandler
from demo.utils.logger import DemoLogger
from demo.utils.errors import AudioValidationError, TranscriptionError

@pytest.fixture
def audio_handler():
    """Create a mock audio handler."""
    handler = Mock(spec=AudioHandler)
    handler.process_upload.return_value = {'duration': 10.0, 'format': 'wav'}
    handler.get_audio_info.return_value = {'duration': 10.0, 'format': 'wav'}
    return handler

@pytest.fixture
def output_handler():
    """Create a mock output handler."""
    handler = Mock(spec=OutputHandler)
    handler.format_output.return_value = "Test transcription output"
    return handler

@pytest.fixture
def logger():
    """Create a mock logger."""
    return Mock(spec=DemoLogger)

@pytest.fixture
def ui(audio_handler, output_handler, logger):
    """Create a TranscriptionUI instance for testing."""
    return TranscriptionUI(audio_handler, output_handler, logger)

def test_init(ui):
    """Test initialization of TranscriptionUI."""
    assert ui.audio_handler is not None
    assert ui.output_handler is not None
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

def test_handle_transcription_no_audio(ui):
    """Test transcription handling with no audio."""
    output, error = ui.handle_transcription(None, "auto-detect", "txt")
    assert output == ""
    assert "Please provide an audio file" in error

def test_handle_transcription_with_audio(ui, audio_handler, output_handler):
    """Test transcription handling with audio."""
    # Setup mock returns
    audio_path = "test.wav"
    transcription = {
        "text": "Test transcription",
        "segments": [{"start": 0, "end": 2, "text": "Test transcription"}]
    }
    ui._simulate_transcription = Mock(return_value=transcription)
    
    # Test successful transcription
    output, error = ui.handle_transcription(audio_path, "auto-detect", "txt")
    assert output == "Test transcription output"
    assert error == ""
    
    # Verify calls
    audio_handler.process_upload.assert_called_once_with(audio_path)
    output_handler.format_output.assert_called_once()
    output_handler.save_output.assert_called_once()

def test_handle_transcription_with_errors(ui, audio_handler):
    """Test transcription handling with various errors."""
    audio_path = "test.wav"
    
    # Test audio validation error
    audio_handler.process_upload.side_effect = AudioValidationError("Invalid audio")
    output, error = ui.handle_transcription(audio_path, "auto-detect", "txt")
    assert output == ""
    assert "Invalid audio" in error
    
    # Test transcription error
    audio_handler.process_upload.side_effect = None
    ui._simulate_transcription = Mock(side_effect=TranscriptionError("Failed to transcribe"))
    output, error = ui.handle_transcription(audio_path, "auto-detect", "txt")
    assert output == ""
    assert "Failed to transcribe" in error

def test_handle_clear(ui):
    """Test clearing the interface."""
    result = ui.handle_clear()
    assert result == (None, "", "")
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
"""Tests for the web interface components."""

import pytest
import gradio as gr
from pathlib import Path
import tempfile
import shutil
import os
import numpy as np
import scipy.io.wavfile as wavfile

from demo.interface.web_ui import TranscriptionUI
from demo.config import DemoConfig
from demo.utils.resource_manager import ResourceManager

@pytest.fixture
def config():
    """Create a demo configuration for testing."""
    return DemoConfig()

@pytest.fixture
def ui(config):
    """Create a TranscriptionUI instance for testing."""
    return TranscriptionUI(config)

@pytest.fixture
def test_audio():
    """Create a test audio file with actual audio content."""
    temp_dir = tempfile.mkdtemp()
    audio_path = Path(temp_dir) / "test.wav"
    
    # Generate 1 second of silence at 44.1kHz
    sample_rate = 44100
    duration = 1  # seconds
    samples = np.zeros(sample_rate * duration, dtype=np.int16)
    
    # Add a simple sine wave to make it non-silent
    t = np.linspace(0, duration, sample_rate * duration)
    frequency = 440  # Hz (A4 note)
    samples += (32767 * 0.5 * np.sin(2 * np.pi * frequency * t)).astype(np.int16)
    
    # Write WAV file
    wavfile.write(str(audio_path), sample_rate, samples)
    
    yield str(audio_path)
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_init(ui):
    """Test initialization of the web interface."""
    assert ui.config is not None
    assert ui.logger is not None
    assert ui.resource_manager is not None
    assert ui.audio_handler is not None
    assert ui.output_handler is not None
    assert ui.interface is None
    assert isinstance(ui.progress, gr.Progress)
    assert isinstance(ui.error_box, gr.Textbox)
    assert not ui.error_box.visible

def test_build_interface(ui):
    """Test building the Gradio interface."""
    with gr.Blocks() as _:  # Create a Gradio context
        interface = ui.build_interface()
    
    assert isinstance(interface, gr.Blocks)
    assert ui.interface is not None
    assert ui.status is not None
    assert isinstance(ui.error_box, gr.Textbox)

def test_handle_transcription_no_audio(ui):
    """Test transcription handling with no audio."""
    output, error = ui.handle_transcription(None, "auto-detect", "txt")
    assert output == ""
    assert "provide an audio file" in error

def test_handle_transcription_with_audio(ui, test_audio):
    """Test transcription handling with audio file."""
    output, error = ui.handle_transcription(test_audio, "auto-detect", "txt")
    assert output == "Hello, how are you? こんにちは、お元気ですか？"
    assert error == ""

def test_handle_clear(ui):
    """Test clearing the interface."""
    audio, output, error = ui.handle_clear()
    assert audio is None
    assert output == ""
    assert error == ""

def test_get_service_status(ui):
    """Test service status retrieval."""
    status = ui._get_service_status()
    assert isinstance(status, str)
    assert any(indicator in status for indicator in ["✅", "❌"])
    assert any(provider in status.lower() for provider in ["aws", "google", "unknown"])

def test_simulate_transcription(ui):
    """Test transcription simulation."""
    result = ui._simulate_transcription()
    
    assert isinstance(result, dict)
    assert "text" in result
    assert "segments" in result
    assert "language" in result
    assert len(result["segments"]) == 2
    assert all(key in result["segments"][0] for key in ["start", "end", "text"])

def test_launch(ui):
    """Test interface launch preparation."""
    with gr.Blocks() as _:  # Create a Gradio context
        ui.launch(prevent_thread_lock=True)
    assert ui.interface is not None 
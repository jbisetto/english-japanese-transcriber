"""Tests for the AudioHandler class."""

import os
import pytest
import numpy as np
import soundfile as sf
from pathlib import Path
from datetime import datetime, timedelta
from demo.handlers.audio_handler import AudioHandler, AudioValidationError

@pytest.fixture
def temp_recordings_dir(tmp_path):
    """Create a temporary recordings directory."""
    recordings_dir = tmp_path / "test_recordings"
    recordings_dir.mkdir()
    return str(recordings_dir)

@pytest.fixture
def audio_handler(temp_recordings_dir):
    """Create an AudioHandler instance with a temporary directory."""
    return AudioHandler(recordings_dir=temp_recordings_dir)

@pytest.fixture
def sample_audio_data():
    """Generate a simple sine wave for testing."""
    sample_rate = 44100
    duration = 1.0  # seconds
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
    return audio_data, sample_rate

@pytest.fixture
def sample_audio_file(temp_recordings_dir, sample_audio_data):
    """Create a sample WAV file for testing."""
    audio_data, sample_rate = sample_audio_data
    filepath = os.path.join(temp_recordings_dir, "test.wav")
    sf.write(filepath, audio_data, sample_rate)
    return filepath

def test_init_creates_directory(temp_recordings_dir):
    """Test that initialization creates the recordings directory."""
    handler = AudioHandler(recordings_dir=temp_recordings_dir)
    assert Path(temp_recordings_dir).exists()
    assert Path(temp_recordings_dir).is_dir()

def test_validate_format_valid(audio_handler, sample_audio_file):
    """Test format validation with valid audio file."""
    assert audio_handler.validate_format(sample_audio_file) is True
    assert audio_handler.validate_format(sample_audio_file, mime_type="audio/wav") is True

def test_validate_format_invalid(audio_handler):
    """Test format validation with invalid audio file."""
    with pytest.raises(AudioValidationError):
        audio_handler.validate_format("invalid.xyz")
    
    with pytest.raises(AudioValidationError):
        audio_handler.validate_format("test.wav", mime_type="invalid/type")

def test_save_recording(audio_handler, sample_audio_data):
    """Test saving audio recording."""
    audio_data, sample_rate = sample_audio_data
    filepath = audio_handler.save_recording(audio_data, sample_rate)
    
    assert Path(filepath).exists()
    assert Path(filepath).suffix == ".wav"
    
    # Verify the saved audio
    saved_data, saved_rate = sf.read(filepath)
    assert saved_rate == sample_rate
    np.testing.assert_allclose(saved_data, audio_data, rtol=1e-4, atol=1e-4)

def test_process_upload(audio_handler, sample_audio_file):
    """Test processing uploaded audio file."""
    result = audio_handler.process_upload(sample_audio_file)
    
    assert isinstance(result, dict)
    assert 'playback' in result
    assert 'transcription' in result
    
    # Check both files exist and are wav files
    assert Path(result['playback']).exists()
    assert Path(result['playback']).suffix == ".wav"
    assert "playback_" in Path(result['playback']).name
    
    assert Path(result['transcription']).exists()
    assert Path(result['transcription']).suffix == ".wav"
    assert "transcription_" in Path(result['transcription']).name

def test_get_audio_info(audio_handler, sample_audio_file):
    """Test getting audio file information."""
    info = audio_handler.get_audio_info(sample_audio_file)
    
    assert isinstance(info, dict)
    assert 'duration' in info
    assert 'sample_rate' in info
    assert 'channels' in info
    assert 'format' in info
    assert 'size_bytes' in info
    
    assert info['format'] == 'wav'
    assert info['channels'] == 1
    assert info['sample_rate'] == 44100

def test_cleanup_old_recordings(audio_handler, sample_audio_file):
    """Test cleaning up old recordings."""
    # Create an old file
    old_file = Path(audio_handler.recordings_dir) / "old.wav"
    old_file.write_bytes(Path(sample_audio_file).read_bytes())
    
    # Modify its timestamp to be older
    old_time = datetime.now() - timedelta(hours=25)
    os.utime(str(old_file), (old_time.timestamp(), old_time.timestamp()))
    
    # Run cleanup
    audio_handler._cleanup_old_recordings(max_age_hours=24)
    
    assert not old_file.exists()
    assert Path(sample_audio_file).exists()

def test_list_recordings(audio_handler, sample_audio_file):
    """Test listing recordings."""
    recordings = audio_handler.list_recordings()
    
    assert isinstance(recordings, list)
    assert len(recordings) == 1
    
    recording = recordings[0]
    assert 'path' in recording
    assert 'created' in recording
    assert 'duration' in recording
    assert 'sample_rate' in recording
    assert recording['format'] == 'wav' 
import pytest
from pydub import AudioSegment
from src.audio.handler import AudioHandler, AudioProcessingError
import os
import tempfile
import numpy as np

@pytest.fixture
def audio_handler():
    return AudioHandler()

@pytest.fixture
def sample_audio_segment():
    # Create a 1-second audio segment with actual audio data
    sample_rate = 44100
    duration_ms = 1000
    t = np.linspace(0, duration_ms/1000, int(sample_rate * duration_ms/1000))
    audio_data = np.sin(2 * np.pi * 440 * t) * 32767  # 440 Hz sine wave
    audio_data = audio_data.astype(np.int16)
    
    return AudioSegment(
        audio_data.tobytes(),
        frame_rate=sample_rate,
        sample_width=2,
        channels=1
    )

@pytest.fixture
def temp_audio_file(sample_audio_segment):
    # Create a temporary audio file for testing
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        sample_audio_segment.export(temp_file.name, format='wav')
        temp_path = temp_file.name
    
    yield temp_path
    
    # Cleanup after test
    try:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    except OSError:
        pass  # Ignore cleanup errors

def test_init_valid_parameters():
    handler = AudioHandler(target_sample_rate=44100, target_channels=2)
    assert handler.target_sample_rate == 44100
    assert handler.target_channels == 2

def test_init_invalid_sample_rate():
    with pytest.raises(ValueError, match="Sample rate must be positive"):
        AudioHandler(target_sample_rate=-1)

def test_init_invalid_channels():
    with pytest.raises(ValueError, match=r"Channels must be either 1 \(mono\) or 2 \(stereo\)"):
        AudioHandler(target_channels=3)

def test_validate_audio_file_nonexistent(audio_handler):
    is_valid, error = audio_handler.validate_audio_file("nonexistent.mp3")
    assert not is_valid
    assert "Audio file not found" in error

def test_validate_audio_file_unsupported_format(temp_audio_file, audio_handler):
    # Rename temp file to unsupported extension
    unsupported_file = temp_audio_file + ".xyz"
    try:
        os.rename(temp_audio_file, unsupported_file)
        is_valid, error = audio_handler.validate_audio_file(unsupported_file)
        assert not is_valid
        assert "Unsupported audio format" in error
    finally:
        if os.path.exists(unsupported_file):
            os.unlink(unsupported_file)

def test_validate_audio_file_valid(temp_audio_file, audio_handler):
    is_valid, error = audio_handler.validate_audio_file(temp_audio_file)
    assert is_valid
    assert error == ""

def test_load_audio_nonexistent_file(audio_handler):
    with pytest.raises(AudioProcessingError, match="Audio file not found"):
        audio_handler.load_audio("nonexistent.mp3")

def test_load_audio_valid_file(temp_audio_file, audio_handler):
    audio_segment = audio_handler.load_audio(temp_audio_file)
    assert isinstance(audio_segment, AudioSegment)
    assert len(audio_segment) == 1000  # 1 second

def test_convert_to_standard_format(audio_handler, sample_audio_segment):
    # Create audio with different parameters
    audio = sample_audio_segment.set_frame_rate(44100).set_channels(2)
    
    # Convert to standard format
    converted = audio_handler.convert_to_standard_format(audio)
    
    assert converted.frame_rate == audio_handler.target_sample_rate
    assert converted.channels == audio_handler.target_channels

def test_normalize_audio_level_invalid_target(audio_handler, sample_audio_segment):
    with pytest.raises(ValueError, match="target_dbfs must be negative"):
        audio_handler.normalize_audio_level(sample_audio_segment, target_dbfs=1.0)

def test_normalize_audio_level_valid(audio_handler, sample_audio_segment):
    target_dbfs = -20.0
    normalized = audio_handler.normalize_audio_level(sample_audio_segment, target_dbfs)
    
    # Allow for small floating point differences
    assert abs(normalized.dBFS - target_dbfs) < 1.0

def test_remove_silence_invalid_threshold(audio_handler, sample_audio_segment):
    with pytest.raises(ValueError, match="silence_thresh must be negative"):
        audio_handler.remove_silence(sample_audio_segment, silence_thresh=1.0)

def test_remove_silence_invalid_min_length(audio_handler, sample_audio_segment):
    with pytest.raises(ValueError, match="min_silence_len must be non-negative"):
        audio_handler.remove_silence(sample_audio_segment, min_silence_len=-1)

def test_remove_silence_valid(audio_handler, sample_audio_segment):
    # Create audio with alternating silence and sound
    silence = AudioSegment.silent(duration=500)
    sound = sample_audio_segment[:500].apply_gain(20)
    
    # Create a sequence: silence -> sound -> silence
    audio = silence + sound + silence
    original_length = len(audio)
    
    processed = audio_handler.remove_silence(audio, silence_thresh=-30)
    
    # Should be shorter than original due to silence removal
    assert len(processed) < original_length
    # Should retain some audio (the sound segment plus small silence buffers)
    assert len(processed) > 0

def test_process_audio_complete_pipeline(temp_audio_file, audio_handler):
    processed = audio_handler.process_audio(temp_audio_file)
    assert isinstance(processed, AudioSegment)
    assert processed.frame_rate == audio_handler.target_sample_rate
    assert processed.channels == audio_handler.target_channels

def test_process_audio_without_silence_removal(temp_audio_file, audio_handler):
    processed = audio_handler.process_audio(temp_audio_file, remove_silence=False)
    assert isinstance(processed, AudioSegment)
    assert len(processed) == 1000  # Original duration preserved

def test_process_audio_invalid_file(audio_handler):
    with pytest.raises(AudioProcessingError, match="Audio file not found"):
        audio_handler.process_audio("nonexistent.mp3") 
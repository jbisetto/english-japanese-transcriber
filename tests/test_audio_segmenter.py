import pytest
import numpy as np
from pydub import AudioSegment
from src.audio.segmenter import AudioSegmenter, SegmentationConfig, AudioSegmentationError

@pytest.fixture
def audio_segmenter():
    """Default audio segmenter with standard configuration."""
    return AudioSegmenter()

@pytest.fixture
def custom_config():
    """Custom segmentation configuration for testing."""
    return SegmentationConfig(
        min_silence_len=500,
        silence_thresh=-20,
        keep_silence=100,
        segment_duration=5000,
        min_segment_length=1000,
        max_segment_length=10000,
        overlap=200
    )

@pytest.fixture
def custom_segmenter(custom_config):
    """Audio segmenter with custom configuration."""
    return AudioSegmenter(custom_config)

@pytest.fixture
def sample_audio():
    """Creates a sample audio segment for testing."""
    # Create a 3-second audio with alternating sound and silence
    sample_rate = 44100
    duration_ms = 3000
    t = np.linspace(0, duration_ms/1000, int(sample_rate * duration_ms/1000))
    
    # Generate a 440 Hz sine wave
    audio_data = np.sin(2 * np.pi * 440 * t) * 32767
    
    # Add silence in the middle (1 second)
    silence_start = len(audio_data) // 3
    silence_end = 2 * len(audio_data) // 3
    audio_data[silence_start:silence_end] = 0
    
    # Convert to int16
    audio_data = audio_data.astype(np.int16)
    
    return AudioSegment(
        audio_data.tobytes(),
        frame_rate=sample_rate,
        sample_width=2,
        channels=1
    )

@pytest.fixture
def long_sample_audio():
    """Creates a longer sample audio segment for testing overlapping segments."""
    # Create a 10-second audio
    sample_rate = 44100
    duration_ms = 10000
    t = np.linspace(0, duration_ms/1000, int(sample_rate * duration_ms/1000))
    
    # Generate a 440 Hz sine wave
    audio_data = np.sin(2 * np.pi * 440 * t) * 32767
    
    # Convert to int16
    audio_data = audio_data.astype(np.int16)
    
    return AudioSegment(
        audio_data.tobytes(),
        frame_rate=sample_rate,
        sample_width=2,
        channels=1
    )

def test_init_default_config():
    """Test initialization with default configuration."""
    segmenter = AudioSegmenter()
    assert segmenter.config is not None
    assert segmenter.config.min_silence_len == 700
    assert segmenter.config.silence_thresh == -16

def test_init_custom_config(custom_config):
    """Test initialization with custom configuration."""
    segmenter = AudioSegmenter(custom_config)
    assert segmenter.config.min_silence_len == 500
    assert segmenter.config.silence_thresh == -20
    assert segmenter.config.segment_duration == 5000

def test_validate_config_invalid_silence_len():
    """Test configuration validation with invalid silence length."""
    config = SegmentationConfig(min_silence_len=-1)
    with pytest.raises(ValueError, match="min_silence_len must be positive"):
        AudioSegmenter(config)

def test_validate_config_invalid_segment_duration():
    """Test configuration validation with invalid segment duration."""
    config = SegmentationConfig(segment_duration=0)
    with pytest.raises(ValueError, match="segment_duration must be positive"):
        AudioSegmenter(config)

def test_validate_config_invalid_segment_lengths():
    """Test configuration validation with invalid min/max segment lengths."""
    config = SegmentationConfig(min_segment_length=2000, max_segment_length=1000)
    with pytest.raises(ValueError, match="max_segment_length must be greater than min_segment_length"):
        AudioSegmenter(config)

def test_validate_config_invalid_overlap():
    """Test configuration validation with invalid overlap."""
    config = SegmentationConfig(segment_duration=1000, overlap=1000)
    with pytest.raises(ValueError, match="overlap must be less than segment_duration"):
        AudioSegmenter(config)

def test_get_audio_stats(audio_segmenter, sample_audio):
    """Test audio statistics calculation."""
    stats = audio_segmenter._get_audio_stats(sample_audio)
    assert 'duration' in stats
    assert 'dBFS' in stats
    assert 'max_dBFS' in stats
    assert 'rms' in stats
    assert stats['duration'] == pytest.approx(3.0)  # 3 seconds

def test_split_on_silence(audio_segmenter, sample_audio):
    """Test silence-based segmentation."""
    segments = audio_segmenter.split_on_silence(sample_audio)
    assert len(segments) > 1  # Should detect the silence and split
    assert all(isinstance(seg, AudioSegment) for seg in segments)

def test_split_on_silence_no_silence(audio_segmenter):
    """Test silence-based segmentation with no silence."""
    # Create continuous audio with no silence
    duration_ms = 2000
    sample_rate = 44100
    t = np.linspace(0, duration_ms/1000, int(sample_rate * duration_ms/1000))
    audio_data = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
    audio = AudioSegment(
        audio_data.tobytes(),
        frame_rate=sample_rate,
        sample_width=2,
        channels=1
    )
    
    segments = audio_segmenter.split_on_silence(audio)
    assert len(segments) == 1  # Should return the original audio

def test_split_into_fixed_length_segments(custom_segmenter, sample_audio):
    """Test fixed-length segmentation."""
    segments = custom_segmenter.split_into_fixed_length_segments(sample_audio)
    assert len(segments) > 0
    
    # Check segment lengths
    for segment in segments:
        assert len(segment) >= custom_segmenter.config.min_segment_length
        assert len(segment) <= custom_segmenter.config.segment_duration

def test_split_into_fixed_length_segments_with_overlap(custom_segmenter, long_sample_audio):
    """Test fixed-length segmentation with overlap."""
    segments = custom_segmenter.split_into_fixed_length_segments(long_sample_audio)
    
    # Should have multiple segments
    assert len(segments) > 1
    
    # Each segment should be at most segment_duration in length
    for segment in segments:
        assert len(segment) <= custom_segmenter.config.segment_duration
    
    # Check that segments overlap
    segment_duration = custom_segmenter.config.segment_duration
    overlap = custom_segmenter.config.overlap
    expected_segments = (len(long_sample_audio) - overlap) // (segment_duration - overlap)
    assert len(segments) >= expected_segments

def test_segment_by_energy(audio_segmenter, sample_audio):
    """Test energy-based segmentation."""
    segments = audio_segmenter.segment_by_energy(sample_audio)
    assert len(segments) > 0
    assert all(isinstance(seg, AudioSegment) for seg in segments)

def test_segment_by_energy_invalid_threshold(audio_segmenter, sample_audio):
    """Test energy-based segmentation with invalid threshold."""
    with pytest.raises((ValueError, AudioSegmentationError), match="energy_threshold must be between 0 and 1"):
        audio_segmenter.segment_by_energy(sample_audio, energy_threshold=1.5)

def test_segment_audio_silence_method(audio_segmenter, sample_audio):
    """Test audio segmentation using silence method."""
    segments = audio_segmenter.segment_audio(sample_audio, method="silence")
    assert len(segments) > 0
    assert all(isinstance(seg, AudioSegment) for seg in segments)

def test_segment_audio_fixed_method(audio_segmenter, sample_audio):
    """Test audio segmentation using fixed-length method."""
    segments = audio_segmenter.segment_audio(sample_audio, method="fixed")
    assert len(segments) > 0
    assert all(isinstance(seg, AudioSegment) for seg in segments)

def test_segment_audio_energy_method(audio_segmenter, sample_audio):
    """Test audio segmentation using energy-based method."""
    segments = audio_segmenter.segment_audio(sample_audio, method="energy")
    assert len(segments) > 0
    assert all(isinstance(seg, AudioSegment) for seg in segments)

def test_segment_audio_invalid_method(audio_segmenter, sample_audio):
    """Test audio segmentation with invalid method."""
    with pytest.raises(ValueError, match="Invalid segmentation method"):
        audio_segmenter.segment_audio(sample_audio, method="invalid") 
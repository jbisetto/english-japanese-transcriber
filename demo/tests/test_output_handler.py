"""Tests for the OutputHandler class."""

import os
import json
import pytest
from pathlib import Path
from datetime import datetime
from demo.handlers.output_handler import OutputHandler, OutputFormatError

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir()
    return str(output_dir)

@pytest.fixture
def output_handler(temp_output_dir):
    """Create an OutputHandler instance with a temporary directory."""
    return OutputHandler(output_dir=temp_output_dir)

@pytest.fixture
def sample_transcription():
    """Create a sample transcription dictionary."""
    return {
        'text': 'Hello, this is a test.',
        'language': 'en',
        'duration': 5.0,
        'segments': [
            {'text': 'Hello,', 'start': 0.0, 'end': 1.0},
            {'text': 'this is', 'start': 1.0, 'end': 2.5},
            {'text': 'a test.', 'start': 2.5, 'end': 5.0}
        ]
    }

@pytest.fixture
def sample_japanese_transcription():
    """Create a sample Japanese transcription dictionary."""
    return {
        'text': 'こんにちは 。 元気 ですか ？',
        'language': 'ja',
        'duration': 5.0,
        'segments': [
            {'text': 'こんにちは。', 'start': 0.0, 'end': 2.0},
            {'text': '元気ですか？', 'start': 2.0, 'end': 5.0}
        ]
    }

def test_init_creates_directory(temp_output_dir):
    """Test that initialization creates the output directory."""
    handler = OutputHandler(output_dir=temp_output_dir)
    assert Path(temp_output_dir).exists()
    assert Path(temp_output_dir).is_dir()

def test_format_japanese_text(output_handler):
    """Test Japanese text formatting."""
    input_text = "こんにちは 。 元気 ですか ？"
    expected = "こんにちは。元気ですか？"
    assert output_handler.format_japanese_text(input_text) == expected

def test_create_srt_timestamps(output_handler):
    """Test SRT timestamp creation."""
    duration = 5.0
    segments = [
        {'start': 0.0, 'end': 2.0},
        {'start': 2.0, 'end': 5.0}
    ]
    
    timestamps = output_handler.create_srt_timestamps(duration, segments)
    assert len(timestamps) == 2
    assert timestamps[0] == "0:00:00,000 --> 0:00:02,000"
    assert timestamps[1] == "0:00:02,000 --> 0:00:05,000"

def test_format_as_txt_english(output_handler, sample_transcription):
    """Test TXT formatting for English text."""
    result = output_handler.format_as_txt(sample_transcription)
    assert result == "Hello, this is a test."

def test_format_as_txt_japanese(output_handler, sample_japanese_transcription):
    """Test TXT formatting for Japanese text."""
    result = output_handler.format_as_txt(sample_japanese_transcription)
    assert result == "こんにちは。元気ですか？"

def test_format_as_json(output_handler, sample_transcription):
    """Test JSON formatting."""
    # Test pretty print
    pretty_result = output_handler.format_as_json(sample_transcription, pretty=True)
    assert isinstance(pretty_result, str)
    assert '\n' in pretty_result
    
    # Test compact
    compact_result = output_handler.format_as_json(sample_transcription, pretty=False)
    assert isinstance(compact_result, str)
    assert '\n' not in compact_result
    
    # Verify content
    data = json.loads(compact_result)
    assert data['text'] == "Hello, this is a test."
    assert len(data['segments']) == 3

def test_format_as_srt(output_handler, sample_transcription):
    """Test SRT formatting."""
    result = output_handler.format_as_srt(sample_transcription)
    lines = result.split('\n')
    
    assert lines[0] == "1"  # First subtitle number
    assert "0:00:00" in lines[1]  # First timestamp
    assert lines[2] == "Hello,"  # First subtitle text
    assert lines[3] == ""  # Empty line between entries

def test_save_output(output_handler, sample_transcription):
    """Test saving output in different formats."""
    # Test all formats
    for format in ['txt', 'json', 'srt']:
        filepath = output_handler.save_output(sample_transcription, format)
        assert Path(filepath).exists()
        assert Path(filepath).suffix == f".{format}"
        
        # Verify content is readable
        content = Path(filepath).read_text(encoding='utf-8')
        assert len(content) > 0

def test_save_output_invalid_format(output_handler, sample_transcription):
    """Test saving output with invalid format."""
    with pytest.raises(OutputFormatError):
        output_handler.save_output(sample_transcription, "invalid")

def test_generate_preview(output_handler, sample_transcription):
    """Test preview generation."""
    # Test with small max_length
    preview = output_handler.generate_preview(sample_transcription, 'txt', max_length=10)
    assert len(preview) <= 13  # 10 chars + "..."
    assert preview.endswith("...")
    
    # Test with large max_length
    preview = output_handler.generate_preview(sample_transcription, 'txt', max_length=1000)
    assert not preview.endswith("...")
    assert preview == "Hello, this is a test."

def test_generate_preview_invalid_format(output_handler, sample_transcription):
    """Test preview generation with invalid format."""
    with pytest.raises(OutputFormatError):
        output_handler.generate_preview(sample_transcription, "invalid") 
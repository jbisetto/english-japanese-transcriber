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
    transcripts_dir = output_dir / "transcripts"
    transcripts_dir.mkdir()
    return str(output_dir)

@pytest.fixture
def output_handler(temp_output_dir):
    """Create an OutputHandler instance with a temporary directory."""
    return OutputHandler(output_dir=temp_output_dir)

@pytest.fixture
def sample_transcription():
    """Create a sample transcription dictionary."""
    return {
        "results": {
            "transcripts": [{
                "transcript": "Hello, this is a test."
            }],
            "segments": [
                {
                    "start_time": "0.0",
                    "end_time": "1.0",
                    "text": "Hello,",
                    "language": "en-US",
                    "confidence": 0.95
                },
                {
                    "start_time": "1.0",
                    "end_time": "2.5",
                    "text": "this is",
                    "language": "en-US",
                    "confidence": 0.98
                },
                {
                    "start_time": "2.5",
                    "end_time": "5.0",
                    "text": "a test.",
                    "language": "en-US",
                    "confidence": 0.97
                }
            ]
        }
    }

@pytest.fixture
def sample_japanese_transcription():
    """Create a sample Japanese transcription dictionary."""
    return {
        "results": {
            "transcripts": [{
                "transcript": "こんにちは。元気ですか？"
            }],
            "segments": [
                {
                    "start_time": "0.0",
                    "end_time": "2.0",
                    "text": "こんにちは。",
                    "language": "ja-JP",
                    "confidence": 0.95
                },
                {
                    "start_time": "2.0",
                    "end_time": "5.0",
                    "text": "元気ですか？",
                    "language": "ja-JP",
                    "confidence": 0.98
                }
            ]
        }
    }

def test_init_creates_directory(temp_output_dir):
    """Test that initialization creates the output directory."""
    handler = OutputHandler(output_dir=temp_output_dir)
    assert Path(temp_output_dir).exists()
    assert Path(temp_output_dir).is_dir()
    assert (Path(temp_output_dir) / "transcripts").exists()
    assert (Path(temp_output_dir) / "transcripts").is_dir()

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
    result = output_handler.format_output(sample_transcription, "txt")
    assert result == "Hello, this is a test."

def test_format_as_txt_japanese(output_handler, sample_japanese_transcription):
    """Test TXT formatting for Japanese text."""
    result = output_handler.format_output(sample_japanese_transcription, "txt")
    assert result == "こんにちは。元気ですか？"

def test_format_as_json(output_handler, sample_transcription):
    """Test JSON formatting."""
    result = output_handler.format_output(sample_transcription, "json")
    assert isinstance(result, str)
    assert '\n' in result
    
    # Verify content
    data = json.loads(result)
    assert "results" in data
    assert "transcripts" in data["results"]
    assert data["results"]["transcripts"][0]["transcript"] == "Hello, this is a test."
    assert len(data["results"]["segments"]) == 3

def test_format_as_srt(output_handler, sample_transcription):
    """Test SRT formatting."""
    result = output_handler.format_output(sample_transcription, "srt")
    lines = result.split('\n')
    
    assert lines[0] == "1"  # First subtitle number
    assert "-->" in lines[1]  # First timestamp
    assert "Hello," in lines[2]  # First subtitle text
    assert lines[3] == ""  # Empty line between entries

def test_save_output(output_handler, sample_transcription):
    """Test saving output in different formats."""
    # Test all formats
    for format in ['txt', 'json', 'srt']:
        filepath = output_handler.save_output(sample_transcription, format)
        assert filepath is not None
        assert Path(filepath).exists()
        assert Path(filepath).suffix == f".{format}"
        
        # Verify content is readable
        content = Path(filepath).read_text(encoding='utf-8')
        assert len(content) > 0
        
        # Verify format-specific content
        if format == 'txt':
            assert "Hello, this is a test." in content
        elif format == 'json':
            data = json.loads(content)
            assert "results" in data
            assert "transcripts" in data["results"]
            assert "segments" in data["results"]
        elif format == 'srt':
            assert "1" in content  # First subtitle number
            assert "-->" in content  # Timestamp separator
            assert "Hello," in content  # First subtitle text

def test_save_output_invalid_format(output_handler, sample_transcription):
    """Test saving output with invalid format."""
    with pytest.raises(OutputFormatError):
        output_handler.save_output(sample_transcription, "invalid")

def test_save_output_empty_transcription(output_handler):
    """Test saving output with empty transcription."""
    result = output_handler.save_output(None, "txt")
    assert result is None
    
    result = output_handler.save_output({}, "txt")
    assert result is None

def test_generate_preview(output_handler, sample_transcription):
    """Test preview generation."""
    # Test with small max_length
    preview = output_handler.generate_preview(sample_transcription, 'txt', max_length=10)
    assert len(preview) <= 13  # 10 chars + "..."
    assert preview.endswith("...")
    
    # Test with large max_length
    preview = output_handler.generate_preview(sample_transcription, 'txt', max_length=1000)
    assert not preview.endswith("...")
    assert "Hello, this is a test." in preview

def test_generate_preview_invalid_format(output_handler, sample_transcription):
    """Test preview generation with invalid format."""
    with pytest.raises(OutputFormatError):
        output_handler.generate_preview(sample_transcription, "invalid")

def test_format_output_invalid_format(output_handler, sample_transcription):
    """Test format_output with invalid format."""
    with pytest.raises(OutputFormatError):
        output_handler.format_output(sample_transcription, "invalid")

def test_format_output_empty_transcription(output_handler):
    """Test format_output with empty transcription."""
    assert output_handler.format_output(None, "txt") == ""
    assert output_handler.format_output({}, "txt") == ""
    assert output_handler.format_output({"results": {}}, "txt") == "" 
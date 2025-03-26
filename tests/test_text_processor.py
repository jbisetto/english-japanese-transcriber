"""Tests for the TextProcessor class."""
import pytest
from src.transcription.processor import TextProcessor

def test_basic_japanese_formatting():
    """Test basic Japanese text formatting."""
    processor = TextProcessor()
    input_text = "これは  テスト   です。"  # Extra spaces
    expected = "これは　テスト　です。"  # Using full-width spaces
    assert processor.process_japanese_text(input_text) == expected

def test_japanese_punctuation():
    """Test Japanese punctuation handling."""
    processor = TextProcessor()
    input_text = "これは、テストです。！？"  # Mixed punctuation
    expected = "これは、テストです。！？"
    assert processor.process_japanese_text(input_text) == expected

def test_japanese_numbers():
    """Test Japanese number formatting."""
    processor = TextProcessor()
    input_text = "テスト1、テスト2。"  # Numbers in text
    expected = "テスト１、テスト２。"  # Convert to full-width
    assert processor.process_japanese_text(input_text) == expected

def test_japanese_mixed_scripts():
    """Test handling of mixed Japanese scripts."""
    processor = TextProcessor()
    input_text = "ひらがな カタカナ 漢字"
    expected = "ひらがな　カタカナ　漢字"  # Using full-width spaces
    assert processor.process_japanese_text(input_text) == expected

def test_japanese_line_breaks():
    """Test Japanese line break handling."""
    processor = TextProcessor()
    input_text = "これは\nテスト\nです。"
    expected = "これは　テスト　です。"  # Using full-width spaces
    assert processor.process_japanese_text(input_text) == expected

def test_japanese_full_width_ascii():
    """Test conversion of ASCII characters to full-width."""
    processor = TextProcessor()
    input_text = "テスト(test)123"
    expected = "テスト（ｔｅｓｔ）１２３"
    assert processor.process_japanese_text(input_text) == expected

def test_process_text_language_selection():
    """Test process_text language-specific processing."""
    processor = TextProcessor()
    japanese_text = "テスト123"
    english_text = "Test 123"
    
    assert processor.process_text(japanese_text, "ja") == "テスト１２３"
    assert processor.process_text(english_text, "en") == "Test 123" 
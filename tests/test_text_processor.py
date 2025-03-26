"""Tests for the TextProcessor class."""
import pytest
from src.transcription.processor import TextProcessor

class TestTextProcessor:
    @pytest.fixture
    def processor(self):
        return TextProcessor()

    # Japanese Text Processing Tests
    def test_basic_japanese_formatting(self, processor):
        """Test basic Japanese text formatting."""
        input_text = "これは  テスト   です。"  # Extra spaces
        expected = "これは　テスト　です。"  # Using full-width spaces
        assert processor.process_japanese_text(input_text) == expected

    def test_japanese_punctuation(self, processor):
        """Test Japanese punctuation handling."""
        input_text = "これは、テストです。！？"  # Mixed punctuation
        expected = "これは、テストです。！？"
        assert processor.process_japanese_text(input_text) == expected

    def test_japanese_numbers(self, processor):
        """Test Japanese number formatting."""
        input_text = "テスト1、テスト2。"  # Numbers in text
        expected = "テスト１、テスト２。"  # Convert to full-width
        assert processor.process_japanese_text(input_text) == expected

    def test_japanese_mixed_scripts(self, processor):
        """Test handling of mixed Japanese scripts."""
        input_text = "ひらがな カタカナ 漢字"
        expected = "ひらがな　カタカナ　漢字"  # Using full-width spaces
        assert processor.process_japanese_text(input_text) == expected

    def test_japanese_brackets(self, processor):
        """Test Japanese bracket conversion."""
        input_text = "これは(テスト)と[テスト]です。"
        expected = "これは（テスト）と［テスト］です。"
        assert processor.process_japanese_text(input_text) == expected

    def test_japanese_full_width_ascii(self, processor):
        """Test conversion of ASCII characters to full-width."""
        input_text = "テスト(test)123"
        expected = "テスト（ｔｅｓｔ）１２３"
        assert processor.process_japanese_text(input_text) == expected

    # English Text Processing Tests
    def test_basic_english_formatting(self, processor):
        """Test basic English text formatting."""
        input_text = "This   is  a    test."
        expected = "This is a test."
        assert processor.process_english_text(input_text) == expected

    def test_english_contractions(self, processor):
        """Test English contraction expansion."""
        input_text = "I can't do it. It's not possible."
        expected = "I cannot do it. It is not possible."
        assert processor.process_english_text(input_text) == expected

    def test_english_numbers_with_units(self, processor):
        """Test formatting of numbers with units."""
        input_text = "The temperature is 20C and speed is 60mph."
        expected = "The temperature is 20 C and speed is 60 mph."
        assert processor.process_english_text(input_text) == expected

    def test_english_multiple_periods(self, processor):
        """Test handling of multiple periods."""
        input_text = "Testing.... More text..."
        expected = "Testing... More text..."
        assert processor.process_english_text(input_text) == expected

    def test_english_sentence_spacing(self, processor):
        """Test sentence spacing."""
        input_text = "First sentence.Second sentence!Third sentence?"
        expected = "First sentence. Second sentence! Third sentence?"
        assert processor.process_english_text(input_text) == expected

    # General Text Processing Tests
    def test_process_text_empty_input(self, processor):
        """Test handling of empty input."""
        assert processor.process_text("", "en") == ""
        assert processor.process_text("", "ja") == ""

    def test_process_text_unsupported_language(self, processor):
        """Test handling of unsupported language codes."""
        input_text = "This is a test.  "
        expected = "This is a test."
        assert processor.process_text(input_text, "fr") == expected

    def test_process_text_language_selection(self, processor):
        """Test process_text language-specific processing."""
        japanese_text = "テスト123"
        english_text = "Test 123mph"
        
        assert processor.process_text(japanese_text, "ja") == "テスト１２３"
        assert processor.process_text(english_text, "en") == "Test 123 mph"

    def test_mixed_language_text(self, processor):
        """Test handling of mixed language text with their respective processors."""
        japanese_text = "これは test です。"
        english_text = "This is テスト."
        
        processed_ja = processor.process_text(japanese_text, "ja")
        processed_en = processor.process_text(english_text, "en")
        
        assert "ｔｅｓｔ" in processed_ja  # Full-width ASCII in Japanese
        assert "テスト" in processed_en  # Original Japanese in English 
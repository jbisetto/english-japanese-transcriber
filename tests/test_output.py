import unittest
import json
import os
import shutil
from src.output.adapters import (
    TranscriptAdapterFactory,
    TxtAdapter,
    JsonAdapter,
    SrtAdapter
)
from src.output.manager import OutputManager

class TestTranscriptAdapters(unittest.TestCase):
    def setUp(self):
        self.sample_transcript = [
            {"language": "en", "text": "Hello, this is a test."},
            {"language": "ja", "text": "こんにちは、テストです。"}
        ]

    def test_txt_adapter(self):
        adapter = TxtAdapter()
        result = adapter.format_transcript(self.sample_transcript)
        expected = "[EN] Hello, this is a test.\n\n[JA] こんにちは、テストです。"
        self.assertEqual(result, expected)

    def test_json_adapter(self):
        adapter = JsonAdapter()
        result = adapter.format_transcript(self.sample_transcript)
        # Parse both to compare the actual content
        result_dict = json.loads(result)
        expected_dict = {
            "version": "1.0",
            "transcript": self.sample_transcript
        }
        self.assertEqual(result_dict, expected_dict)

    def test_srt_adapter(self):
        adapter = SrtAdapter(words_per_subtitle=4, time_per_subtitle=2.0)
        result = adapter.format_transcript(self.sample_transcript)
        
        # Verify structure of SRT format
        lines = result.split('\n')
        
        # First subtitle
        self.assertEqual(lines[0], "1")  # Subtitle number
        self.assertEqual(lines[1], "00:00:00,000 --> 00:00:02,000")  # Timestamp
        self.assertEqual(lines[2], "Hello, this is a")  # Text
        
        # Second subtitle
        self.assertEqual(lines[4], "2")  # Subtitle number
        self.assertEqual(lines[5], "00:00:02,000 --> 00:00:04,000")  # Timestamp
        self.assertEqual(lines[6], "test.")  # Text
        
        # Third subtitle
        self.assertEqual(lines[8], "3")  # Subtitle number
        self.assertEqual(lines[9], "00:00:04,000 --> 00:00:06,000")  # Timestamp
        self.assertEqual(lines[10], "[JA] こんにちは、テストです。")  # Text with language tag

    def test_adapter_factory_valid_formats(self):
        for format_type in ["txt", "json", "srt"]:
            adapter = TranscriptAdapterFactory.get_adapter(format_type)
            self.assertTrue(hasattr(adapter, 'format_transcript'))

    def test_adapter_factory_invalid_format(self):
        with self.assertRaises(ValueError):
            TranscriptAdapterFactory.get_adapter("invalid")

class TestOutputManager(unittest.TestCase):
    def setUp(self):
        self.test_output_dir = "test_output"
        self.output_manager = OutputManager(output_dir=self.test_output_dir)
        self.sample_transcript = [
            {"language": "en", "text": "Hello, this is a test."},
            {"language": "ja", "text": "こんにちは、テストです。"}
        ]

    def tearDown(self):
        # Clean up test output directory
        if os.path.exists(self.test_output_dir):
            shutil.rmtree(self.test_output_dir)

    def test_save_transcript_txt(self):
        self.output_manager.save_transcript(self.sample_transcript, "test", "txt")
        output_path = os.path.join(self.test_output_dir, "test.txt")
        
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn("[EN] Hello, this is a test.", content)
        self.assertIn("[JA] こんにちは、テストです。", content)

    def test_save_transcript_json(self):
        self.output_manager.save_transcript(self.sample_transcript, "test", "json")
        output_path = os.path.join(self.test_output_dir, "test.json")
        
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        self.assertEqual(content["version"], "1.0")
        self.assertEqual(content["transcript"], self.sample_transcript)

    def test_save_transcript_srt(self):
        self.output_manager.save_transcript(self.sample_transcript, "test", "srt")
        output_path = os.path.join(self.test_output_dir, "test.srt")
        
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn("00:00:00,000 --> ", content)
        self.assertIn("Hello, this is a test.", content)
        self.assertIn("[JA] こんにちは、テストです。", content)

    def test_save_transcript_invalid_format(self):
        with self.assertRaises(ValueError):
            self.output_manager.save_transcript(self.sample_transcript, "test", "invalid")

    def test_output_directory_creation(self):
        # Create a new output manager with a nested directory path
        nested_dir = os.path.join(self.test_output_dir, "nested", "path")
        manager = OutputManager(output_dir=nested_dir)
        
        manager.save_transcript(self.sample_transcript, "test", "txt")
        self.assertTrue(os.path.exists(nested_dir))
        self.assertTrue(os.path.exists(os.path.join(nested_dir, "test.txt")))

if __name__ == '__main__':
    unittest.main()

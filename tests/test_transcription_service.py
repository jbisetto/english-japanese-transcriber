import unittest
import json
import asyncio
from unittest.mock import MagicMock, patch, ANY, AsyncMock
from pydub import AudioSegment
import io
from pathlib import Path
import pytest

# Mock necessary modules before they are imported by the service
# This prevents actual boto3 calls during module loading
mock_boto3 = MagicMock()
mock_transcribe_client = MagicMock()
mock_handlers = MagicMock()
mock_model = MagicMock()

modules = {
    'boto3': mock_boto3,
    'amazon_transcribe.client': MagicMock(TranscribeStreamingClient=MagicMock(return_value=mock_transcribe_client)),
    'amazon_transcribe.handlers': mock_handlers,
    'amazon_transcribe.model': mock_model,
    'src.aws.bedrock_client': MagicMock()
}

with patch.dict('sys.modules', modules):
    from src.transcription.service import TranscriptionService
    from src.aws.bedrock_client import BedrockClient # Now this imports the mock

# Mock configuration classes
class MockAWSConfig:
    def __init__(self):
        self.region_name = "us-east-1"
        self.s3_bucket = "test-bucket"

class MockTranscriptionConfig:
    def __init__(self):
        self.english_model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        self.japanese_model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

class TestTranscriptionService(unittest.TestCase):

    def setUp(self):
        # Reset mocks for each test
        self.mock_s3 = MagicMock()
        self.mock_transcribe = MagicMock()
        self.mock_bedrock_runtime = MagicMock()
        
        # Configure the mock boto3 client factory
        def get_client(service_name, region_name=None):
            if service_name == 's3':
                return self.mock_s3
            if service_name == 'transcribe':
                return self.mock_transcribe
            if service_name == 'bedrock-runtime':
                return self.mock_bedrock_runtime
            raise ValueError(f"Unexpected service requested from boto3.client: {service_name}")
            
        mock_boto3.client.side_effect = get_client
        
        # Mock streaming client
        self.mock_stream = AsyncMock()
        self.mock_stream.input_stream = AsyncMock()
        self.mock_stream.output_stream = AsyncMock()
        mock_transcribe_client.start_stream_transcription = AsyncMock(return_value=self.mock_stream)

        # Instantiate the service with mock configs
        self.service = TranscriptionService(
            aws_config=MockAWSConfig(),
            transcription_config=MockTranscriptionConfig()
        )
        
        # Mock AudioSegment methods needed for testing transcribe/upload
        self.mock_audio_segment = MagicMock(spec=AudioSegment)
        self.mock_audio_segment.export = MagicMock()
        self.mock_audio_segment.frame_rate = 44100
        buffer_mock = io.BytesIO(b"dummy audio data")
        self.mock_audio_segment.export.return_value = buffer_mock
        
        # Create a temporary output directory for testing
        self.test_output_dir = Path("test_output/transcripts")
        self.test_output_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        # Clean up test output directory
        import shutil
        shutil.rmtree("test_output", ignore_errors=True)

    def test_post_process_english_success(self):
        """Test successful English post-processing."""
        raw_text = "hello world this is a test"
        expected_processed_text = "Hello world. This is a test."
        
        mock_response_body = json.dumps({
            "type": "message",
            "content": [{"type": "text", "text": expected_processed_text}],
            "stop_reason": "end_turn"
        }).encode('utf-8')
        
        mock_stream = MagicMock()
        mock_stream.read.return_value = mock_response_body
        mock_response = {'body': mock_stream}
        self.mock_bedrock_runtime.invoke_model.return_value = mock_response

        processed_text = self.service.post_process_text(raw_text, "en")

        self.assertEqual(processed_text, expected_processed_text)
        self.mock_bedrock_runtime.invoke_model.assert_called_once()
        call_args = self.mock_bedrock_runtime.invoke_model.call_args[1]
        self.assertEqual(call_args['modelId'], self.service.transcription_config.english_model_id)
        body = json.loads(call_args['body'].decode())
        self.assertEqual(body['messages'][0]['content'], raw_text)
        self.assertIn("expert editor", body['system'])

    def test_post_process_japanese_success(self):
        """Test successful Japanese post-processing."""
        raw_text = "こんにちはせかい これはてすとです"
        expected_processed_text = "こんにちは、世界。これはテストです。"

        mock_response_body = json.dumps({
            "type": "message",
            "content": [{"type": "text", "text": expected_processed_text}],
            "stop_reason": "end_turn"
        }).encode('utf-8')

        mock_stream = MagicMock()
        mock_stream.read.return_value = mock_response_body
        mock_response = {'body': mock_stream}
        self.mock_bedrock_runtime.invoke_model.return_value = mock_response

        processed_text = self.service.post_process_text(raw_text, "ja")

        self.assertEqual(processed_text, expected_processed_text)
        self.mock_bedrock_runtime.invoke_model.assert_called_once()
        call_args = self.mock_bedrock_runtime.invoke_model.call_args[1]
        self.assertEqual(call_args['modelId'], self.service.transcription_config.japanese_model_id)
        body = json.loads(call_args['body'].decode())
        self.assertEqual(body['messages'][0]['content'], raw_text)
        self.assertIn("熟練した編集者", body['system'])

    def test_post_process_empty_text(self):
        """Test post-processing with empty input text."""
        processed_text = self.service.post_process_text("", "en")
        self.assertEqual(processed_text, "")
        self.mock_bedrock_runtime.invoke_model.assert_not_called()

    def test_post_process_unsupported_language(self):
        """Test post-processing with an unsupported language code."""
        raw_text = "Some text"
        processed_text = self.service.post_process_text(raw_text, "es")
        self.assertEqual(processed_text, raw_text)
        self.mock_bedrock_runtime.invoke_model.assert_not_called()

    def test_post_process_bedrock_api_error(self):
        """Test handling of Bedrock API errors during post-processing."""
        raw_text = "hello world"
        self.mock_bedrock_runtime.invoke_model.side_effect = Exception("AWS Bedrock Error")

        processed_text = self.service.post_process_text(raw_text, "en")

        self.assertEqual(processed_text, raw_text)
        self.mock_bedrock_runtime.invoke_model.assert_called_once()

    def test_post_process_bedrock_model_error_response(self):
        """Test handling of error responses from the Bedrock model itself."""
        raw_text = "some input"
        mock_error_response_body = json.dumps({
            "type": "error",
            "error": {"type": "overloaded_error", "message": "Model is overloaded"}
        }).encode('utf-8')

        mock_stream = MagicMock()
        mock_stream.read.return_value = mock_error_response_body
        mock_response = {'body': mock_stream}
        self.mock_bedrock_runtime.invoke_model.return_value = mock_response

        processed_text = self.service.post_process_text(raw_text, "en")

        self.assertEqual(processed_text, raw_text)
        self.mock_bedrock_runtime.invoke_model.assert_called_once()

    def test_post_process_unexpected_response_format(self):
        """Test handling of unexpected response formats from Bedrock."""
        raw_text = "another input"
        mock_bad_response_body = json.dumps({
            "type": "message",
            "content": [], # Empty content list
            "stop_reason": "end_turn"
        }).encode('utf-8')

        mock_stream = MagicMock()
        mock_stream.read.return_value = mock_bad_response_body
        mock_response = {'body': mock_stream}
        self.mock_bedrock_runtime.invoke_model.return_value = mock_response

        processed_text = self.service.post_process_text(raw_text, "en")

        self.assertEqual(processed_text, raw_text)
        self.mock_bedrock_runtime.invoke_model.assert_called_once()

    def test_post_process_non_text_content_block(self):
        """Test handling when the first content block is not text."""
        raw_text = "input leading to non-text response"
        mock_response_body = json.dumps({
            "type": "message",
            "content": [{"type": "tool_use", "id": "toolu_01A..."}], # Non-text block first
            "stop_reason": "tool_use"
        }).encode('utf-8')

        mock_stream = MagicMock()
        mock_stream.read.return_value = mock_response_body
        mock_response = {'body': mock_stream}
        self.mock_bedrock_runtime.invoke_model.return_value = mock_response

        processed_text = self.service.post_process_text(raw_text, "en")

        self.assertEqual(processed_text, raw_text)
        self.mock_bedrock_runtime.invoke_model.assert_called_once()

    @pytest.mark.asyncio
    @patch('pydub.AudioSegment.from_file')
    @patch('asyncio.get_event_loop')
    async def test_transcribe_success(self, mock_get_loop, mock_from_file):
        """Test successful transcription with streaming API."""
        # Mock audio file loading
        mock_from_file.return_value = self.mock_audio_segment

        # Mock event loop and coroutine
        mock_loop = MagicMock()
        mock_get_loop.return_value = mock_loop

        # Mock transcription results
        mock_results = {
            "results": {
                "transcripts": [{"transcript": "Hello, this is a test."}],
                "segments": [
                    {
                        "text": "Hello, this is a test.",
                        "start_time": 0.0,
                        "end_time": 2.0,
                        "confidence": 0.95
                    }
                ]
            }
        }

        # Mock the streaming client
        mock_stream = AsyncMock()
        mock_stream.input_stream = AsyncMock()
        self.mock_transcribe_client.start_stream_transcription.return_value = mock_stream
        mock_loop.run_until_complete.return_value = mock_results

        # Run transcription
        result = await self.service.transcribe("test.wav", "en-US")

        # Verify results
        self.assertEqual(result, mock_results)
        self.mock_transcribe_client.start_stream_transcription.assert_called_once_with(
            language_code="en-US",
            media_sample_rate_hz=44100,
            media_encoding="pcm"
        )

    @pytest.mark.asyncio
    async def test_transcribe_error_handling(self):
        """Test error handling in transcription."""
        with patch('pydub.AudioSegment.from_file') as mock_from_file:
            mock_from_file.side_effect = Exception("Audio file error")
    
            result = await self.service.transcribe("nonexistent.wav", "en-US")
    
            self.assertEqual(
                result,
                {"results": {"transcripts": [{"transcript": ""}], "segments": []}}
            )


if __name__ == '__main__':
    unittest.main() 
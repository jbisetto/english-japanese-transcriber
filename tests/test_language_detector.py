import unittest
from unittest.mock import MagicMock, patch
from pydub import AudioSegment
from botocore.exceptions import ClientError
from src.language.detector import LanguageDetector


class TestLanguageDetector(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('boto3.client')
        self.mock_boto3_client = self.patcher.start()
        self.mock_s3 = MagicMock()
        self.mock_transcribe = MagicMock()

        def mock_client(service, region_name=None):
            if service == 's3':
                return self.mock_s3
            elif service == 'transcribe':
                return self.mock_transcribe
            raise ValueError(f"Unknown service: {service}")

        self.mock_boto3_client.side_effect = mock_client

        # Initialize detector in test mode
        self.language_detector = LanguageDetector(test_mode=True)
        self.mock_audio_segment = MagicMock(spec=AudioSegment)
        self.test_bucket = "test-bucket"
        # Mock audio segment export
        self.mock_audio_segment.export = MagicMock()
        buffer = MagicMock()
        buffer.getvalue = MagicMock(return_value=b"test audio data")
        self.mock_audio_segment.export.return_value = buffer

    def tearDown(self):
        self.patcher.stop()

    def test_detect_language_english(self):
        # Mock S3 operations
        self.mock_s3.put_object = MagicMock(return_value={'ETag': 'test-etag'})
        self.mock_s3.get_object = MagicMock(return_value={
            'Body': MagicMock(
                read=MagicMock(
                    return_value=b'{"results": {"language_code": "en-US"}}'
                )
            )
        })
        self.mock_s3.delete_object = MagicMock(return_value={'DeleteMarker': True})

        # Mock Transcribe operations with immediate completion
        self.mock_transcribe.start_transcription_job = MagicMock(return_value={
            'TranscriptionJob': {
                'TranscriptionJobName': 'test-job',
                'TranscriptionJobStatus': 'IN_PROGRESS'
            }
        })
        self.mock_transcribe.get_transcription_job = MagicMock(return_value={
            "TranscriptionJob": {
                "TranscriptionJobStatus": "COMPLETED"
            }
        })

        result = self.language_detector.detect_language(self.mock_audio_segment, self.test_bucket)
        self.assertEqual(result, "en")

        # Verify S3 operations were called
        self.mock_s3.put_object.assert_called_once()
        self.mock_s3.get_object.assert_called_once()
        self.assertEqual(self.mock_s3.delete_object.call_count, 2)

    def test_detect_language_japanese(self):
        # Mock S3 operations
        self.mock_s3.put_object = MagicMock(return_value={'ETag': 'test-etag'})
        self.mock_s3.get_object = MagicMock(return_value={
            'Body': MagicMock(
                read=MagicMock(
                    return_value=b'{"results": {"language_code": "ja-JP"}}'
                )
            )
        })
        self.mock_s3.delete_object = MagicMock(return_value={'DeleteMarker': True})

        # Mock Transcribe operations with immediate completion
        self.mock_transcribe.start_transcription_job = MagicMock(return_value={
            'TranscriptionJob': {
                'TranscriptionJobName': 'test-job',
                'TranscriptionJobStatus': 'IN_PROGRESS'
            }
        })
        self.mock_transcribe.get_transcription_job = MagicMock(return_value={
            "TranscriptionJob": {
                "TranscriptionJobStatus": "COMPLETED"
            }
        })

        result = self.language_detector.detect_language(self.mock_audio_segment, self.test_bucket)
        self.assertEqual(result, "ja")

        # Verify S3 operations were called
        self.mock_s3.put_object.assert_called_once()
        self.mock_s3.get_object.assert_called_once()
        self.assertEqual(self.mock_s3.delete_object.call_count, 2)

    def test_detect_language_failure(self):
        # Mock S3 operations
        self.mock_s3.put_object = MagicMock(return_value={'ETag': 'test-etag'})
        self.mock_s3.delete_object = MagicMock(return_value={'DeleteMarker': True})

        # Mock Transcribe operations with immediate failure
        self.mock_transcribe.start_transcription_job = MagicMock(return_value={
            'TranscriptionJob': {
                'TranscriptionJobName': 'test-job',
                'TranscriptionJobStatus': 'IN_PROGRESS'
            }
        })
        self.mock_transcribe.get_transcription_job = MagicMock(return_value={
            "TranscriptionJob": {
                "TranscriptionJobStatus": "FAILED",
                "FailureReason": "Test failure"
            }
        })

        result = self.language_detector.detect_language(self.mock_audio_segment, self.test_bucket)
        self.assertEqual(result, "en")  # Should default to English on failure

        # Verify S3 operations were called
        self.mock_s3.put_object.assert_called_once()

    def test_detect_language_timeout(self):
        # Mock S3 operations
        self.mock_s3.put_object = MagicMock(return_value={'ETag': 'test-etag'})
        self.mock_s3.delete_object = MagicMock(return_value={'DeleteMarker': True})

        # Mock Transcribe operations to simulate timeout
        self.mock_transcribe.start_transcription_job = MagicMock(return_value={
            'TranscriptionJob': {
                'TranscriptionJobName': 'test-job',
                'TranscriptionJobStatus': 'IN_PROGRESS'
            }
        })
        # Always return IN_PROGRESS to trigger timeout
        self.mock_transcribe.get_transcription_job = MagicMock(return_value={
            "TranscriptionJob": {
                "TranscriptionJobStatus": "IN_PROGRESS"
            }
        })

        result = self.language_detector.detect_language(self.mock_audio_segment, self.test_bucket)
        self.assertEqual(result, "en")  # Should default to English on timeout

        # Verify S3 operations were called
        self.mock_s3.put_object.assert_called_once()


if __name__ == '__main__':
    unittest.main() 
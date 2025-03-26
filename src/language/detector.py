import io
import json
import time
import random
import boto3
from pydub import AudioSegment


class LanguageDetector:
    def __init__(self, region_name: str = "us-east-1", model_id: str = "amazon.comprehend", test_mode: bool = False):
        """
        Initializes the LanguageDetector with AWS clients.

        Args:
            region_name (str): AWS region name.
            model_id (str): The model ID for language detection (currently unused).
            test_mode (bool): If True, reduces wait times for testing.
        """
        self.transcribe_client = boto3.client('transcribe', region_name=region_name)
        self.s3_client = boto3.client('s3', region_name=region_name)
        self.test_mode = test_mode

    def _upload_audio_to_s3(self, audio_segment: AudioSegment, bucket: str) -> str:
        """
        Uploads an audio segment to S3 for language detection.

        Args:
            audio_segment (AudioSegment): The audio segment to upload.
            bucket (str): The S3 bucket name.

        Returns:
            str: The S3 URI of the uploaded file.
        """
        # Convert audio to WAV format
        buffer = io.BytesIO()
        audio_segment.export(buffer, format="wav")
        audio_data = buffer.getvalue()

        # Generate a unique key for the file
        key = f"language_detection/{int(time.time())}_{random.randint(1000, 9999)}.wav"
        
        # Upload to S3
        self.s3_client.put_object(Bucket=bucket, Key=key, Body=audio_data)
        return f"s3://{bucket}/{key}"

    def detect_language(self, audio_segment: AudioSegment, bucket: str) -> str:
        """
        Detects the language of the given audio segment using Amazon Transcribe.

        Args:
            audio_segment (AudioSegment): The audio segment to analyze.
            bucket (str): The S3 bucket to use for temporary file storage.

        Returns:
            str: The detected language code (e.g., "en" for English, "ja" for Japanese).
        """
        try:
            # Upload audio to S3
            s3_uri = self._upload_audio_to_s3(audio_segment, bucket)

            # Start language detection job
            job_name = f"language-detection-{int(time.time())}_{random.randint(1000, 9999)}"
            response = self.transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                IdentifyLanguage=True,  # Enable language detection
                MediaFormat="wav",
                Media={"MediaFileUri": s3_uri},
                OutputBucketName=bucket,
                OutputKey=f"language_detection_output/{job_name}/"
            )

            # Wait for job completion
            max_tries = 3 if self.test_mode else 60
            sleep_time = 0.1 if self.test_mode else 10
            
            while max_tries > 0:
                max_tries -= 1
                job = self.transcribe_client.get_transcription_job(
                    TranscriptionJobName=job_name
                )
                status = job["TranscriptionJob"]["TranscriptionJobStatus"]
                
                if status in ["COMPLETED", "FAILED"]:
                    if status == "FAILED":
                        raise Exception(f"Language detection job failed: {job.get('FailureReason', 'Unknown error')}")
                    break
                time.sleep(sleep_time)

            if max_tries <= 0:
                raise Exception("Language detection job timed out")

            # Get the language detection result
            output_key = f"language_detection_output/{job_name}/{job_name}.json"
            response = self.s3_client.get_object(Bucket=bucket, Key=output_key)
            result = json.loads(response['Body'].read())
            
            # Clean up S3 files
            self.s3_client.delete_object(Bucket=bucket, Key=output_key)
            input_key = s3_uri.split('/')[-1]
            self.s3_client.delete_object(Bucket=bucket, Key=f"language_detection/{input_key}")

            # Map Amazon Transcribe language codes to our format
            language_map = {
                "en-US": "en",
                "ja-JP": "ja",
                # Add more mappings as needed
            }
            detected_language = result.get("results", {}).get("language_code", "en-US")
            return language_map.get(detected_language, "en")

        except Exception as e:
            print(f"Error detecting language: {e}")
            return "en"  # Default to English on error


if __name__ == '__main__':
    # Example usage
    from src.audio.handler import AudioHandler

    language_detector = LanguageDetector()
    audio_handler = AudioHandler()
    
    # Replace with your actual audio file and S3 bucket
    audio_path = "examples/sample_audio/sample.mp3"
    bucket = "my-transcription-bucket"
    
    try:
        audio_segment = audio_handler.process_audio(audio_path)
        language = language_detector.detect_language(audio_segment, bucket)
        print(f"Detected language: {language}")
    except Exception as e:
        print(f"Failed to detect language: {e}")

import io
import json
import time
import random
import base64
import boto3
from pydub import AudioSegment
from typing import Dict, Any, Optional

class TranscriptionService:
    def __init__(self, 
                 region_name: str = "us-east-1",
                 english_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
                 japanese_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"):
        """
        Initializes the TranscriptionService with AWS clients and model IDs.

        Args:
            region_name (str): AWS region name.
            english_model_id (str): Bedrock model ID for English post-processing.
            japanese_model_id (str): Bedrock model ID for Japanese post-processing.
        """
        self.transcribe_client = boto3.client('transcribe', region_name=region_name)
        self.s3_client = boto3.client('s3', region_name=region_name)
        self.bedrock_client = boto3.client('bedrock-runtime', region_name=region_name)
        self.english_model_id = english_model_id
        self.japanese_model_id = japanese_model_id

    def _upload_audio_to_s3(self, audio_segment: AudioSegment, bucket: str) -> str:
        """
        Uploads an audio segment to S3 for transcription.

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
        key = f"transcribe_input/{int(time.time())}_{random.randint(1000, 9999)}.wav"
        
        # Upload to S3
        self.s3_client.put_object(Bucket=bucket, Key=key, Body=audio_data)
        return f"s3://{bucket}/{key}"

    def transcribe(self, audio_segment: AudioSegment, language_code: str, bucket: str) -> str:
        """
        Transcribes the given audio segment using Amazon Transcribe.

        Args:
            audio_segment (AudioSegment): The audio segment to transcribe.
            language_code (str): The language code (e.g., "en-US" for English, "ja-JP" for Japanese).
            bucket (str): The S3 bucket to use for temporary file storage.

        Returns:
            str: The transcribed text.
        """
        try:
            # Upload audio to S3
            s3_uri = self._upload_audio_to_s3(audio_segment, bucket)

            # Start transcription job
            job_name = f"transcription-{int(time.time())}_{random.randint(1000, 9999)}"
            response = self.transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                LanguageCode=language_code,
                MediaFormat="wav",
                Media={"MediaFileUri": s3_uri},
                OutputBucketName=bucket,
                OutputKey=f"transcribe_output/{job_name}/",
                Settings={
                    "ShowSpeakerLabels": False,  # Set to True if needed
                }
            )

            # Wait for job completion
            max_tries = 60
            while max_tries > 0:
                max_tries -= 1
                job = self.transcribe_client.get_transcription_job(
                    TranscriptionJobName=job_name
                )
                status = job["TranscriptionJob"]["TranscriptionJobStatus"]
                
                if status in ["COMPLETED", "FAILED"]:
                    if status == "FAILED":
                        raise Exception(f"Transcription job failed: {job.get('FailureReason', 'Unknown error')}")
                    break
                time.sleep(10)

            if max_tries <= 0:
                raise Exception("Transcription job timed out")

            # Get the transcription result
            output_key = f"transcribe_output/{job_name}/{job_name}.json"
            response = self.s3_client.get_object(Bucket=bucket, Key=output_key)
            transcription_result = json.loads(response['Body'].read())
            
            # Clean up S3 files
            self.s3_client.delete_object(Bucket=bucket, Key=output_key)
            input_key = s3_uri.split('/')[-1]
            self.s3_client.delete_object(Bucket=bucket, Key=f"transcribe_input/{input_key}")

            return transcription_result['results']['transcripts'][0]['transcript']

        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return ""

    def post_process_text(self, text: str, language_code: str) -> str:
        """
        Post-processes the transcribed text using Bedrock models.

        Args:
            text (str): The text to process.
            language_code (str): The language code of the text.

        Returns:
            str: The processed text.
        """
        try:
            # Select appropriate model based on language
            model_id = self.english_model_id if language_code.startswith("en") else self.japanese_model_id
            
            # Prepare the prompt based on language
            if language_code.startswith("en"):
                prompt = f"Please improve this English transcription while maintaining its original meaning: {text}"
            else:
                prompt = f"Please improve this Japanese transcription while maintaining its original meaning and using proper Japanese typography: {text}"

            # Call Bedrock model
            response = self.bedrock_client.invoke_model(
                modelId=model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 4096,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )

            # Parse and return the response
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']

        except Exception as e:
            print(f"Error post-processing text: {e}")
            return text  # Return original text if post-processing fails

if __name__ == '__main__':
    # Example usage (replace with your actual audio file path)
    from src.audio.handler import AudioHandler
    from src.language.detector import LanguageDetector

    bedrock_client = boto3.client('bedrock-runtime')  # Initialize Bedrock client
    transcription_service = TranscriptionService(bedrock_client)  # Initialize TranscriptionService
    language_detector = LanguageDetector(bedrock_client)

    audio_handler = AudioHandler()
    audio_path = "examples/sample_audio/sample.mp3"  # Replace with your audio file
    try:
        audio_segment = audio_handler.process_audio(audio_path)  # Process audio first
        language = language_detector.detect_language(audio_segment)
        transcribed_text = transcription_service.transcribe(audio_segment, language)
        print(f"Transcribed text: {transcribed_text}")
    except Exception as e:
        print(f"Failed to transcribe audio: {e}")

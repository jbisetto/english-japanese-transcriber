import io
import json
import time
import random
import base64
import boto3
from pydub import AudioSegment
from typing import Dict, Any, Optional

class TranscriptionService:
    def __init__(self, aws_config, transcription_config):
        """
        Initializes the TranscriptionService with AWS clients and model IDs.

        Args:
            aws_config: Configuration object with AWS settings (region_name, s3_bucket)
            transcription_config: Configuration object with model settings (english_model_id, japanese_model_id)
        """
        self.aws_config = aws_config
        self.transcription_config = transcription_config
        
        # Initialize AWS clients
        self.transcribe_client = boto3.client('transcribe', region_name=aws_config.region_name)
        self.s3_client = boto3.client('s3', region_name=aws_config.region_name)
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=aws_config.region_name)
        
        # Store model IDs
        self.english_model_id = transcription_config.english_model_id
        self.japanese_model_id = transcription_config.japanese_model_id
        
        # Store S3 bucket
        if not hasattr(aws_config, 's3_bucket') or not aws_config.s3_bucket:
            raise ValueError("S3 bucket must be configured in AWSConfig")
        self.s3_bucket = aws_config.s3_bucket

    def _upload_audio_to_s3(self, audio_segment: AudioSegment) -> str:
        """
        Uploads an audio segment to S3 for transcription.

        Args:
            audio_segment (AudioSegment): The audio segment to upload.

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
        self.s3_client.put_object(Bucket=self.s3_bucket, Key=key, Body=audio_data)
        return f"s3://{self.s3_bucket}/{key}"

    def transcribe(self, audio_segment: AudioSegment, language_code: str) -> str:
        """
        Transcribes the given audio segment using Amazon Transcribe.

        Args:
            audio_segment (AudioSegment): The audio segment to transcribe.
            language_code (str): The language code (e.g., "en-US" for English, "ja-JP" for Japanese).

        Returns:
            str: The transcribed text.
        """
        try:
            # Upload audio to S3
            s3_uri = self._upload_audio_to_s3(audio_segment)

            # Start transcription job
            job_name = f"transcription-{int(time.time())}_{random.randint(1000, 9999)}"
            response = self.transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                LanguageCode=language_code,
                MediaFormat="wav",
                Media={"MediaFileUri": s3_uri},
                OutputBucketName=self.s3_bucket,
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
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=output_key)
            transcription_result = json.loads(response['Body'].read())
            
            # Clean up S3 files
            self.s3_client.delete_object(Bucket=self.s3_bucket, Key=output_key)
            input_key = s3_uri.split('/')[-1]
            self.s3_client.delete_object(Bucket=self.s3_bucket, Key=f"transcribe_input/{input_key}")

            return transcription_result['results']['transcripts'][0]['transcript']

        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return ""

    def post_process_text(self, text: str, language_code: str) -> str:
        """
        Post-processes the transcribed text using Bedrock Claude 3 Sonnet.

        Args:
            text (str): The transcribed text.
            language_code (str): The language code ("en" or "ja").

        Returns:
            str: The post-processed text.
        """
        if not text:
            return ""

        model_id = self.english_model_id if language_code == "en" else self.japanese_model_id
        
        if "claude-3" not in model_id:
             print(f"Warning: Post-processing is optimized for Claude 3 models. Current model: {model_id}")
             return text

        if language_code == "en":
            system_prompt = "You are an expert editor. Review the following raw transcript text and improve its punctuation, capitalization, and formatting for readability. Ensure the meaning remains unchanged. Output only the corrected text."
        elif language_code == "ja":
            system_prompt = "あなたは熟練した編集者です。以下の書き起こしテキストを確認し、句読点や書式を修正して読みやすくしてください。意味は変えないでください。修正後のテキストのみを出力してください。"
        else:
            print(f"Warning: Unsupported language code for post-processing: {language_code}. Returning original text.")
            return text

        # Construct the request body for Claude 3 Messages API
        messages = [{"role": "user", "content": text}]
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": messages,
            "temperature": 0.1,
        })

        try:
            response = self.bedrock_runtime.invoke_model(
                modelId=model_id,
                body=body.encode(),
                accept='application/json',
                contentType='application/json'
            )
            response_body = json.loads(response['body'].read())

            # Check for errors in the response
            if response_body.get("type") == "error":
                print(f"Error from Bedrock model {model_id}: {response_body['error']}")
                return text

            # Extract the processed text - Claude 3 Messages API format
            if response_body.get("content") and len(response_body["content"]) > 0:
                 # Check if the first content block is text
                 if response_body["content"][0].get("type") == "text":
                     processed_text = response_body["content"][0].get("text", text)
                     return processed_text.strip()
                 else:
                    print(f"Warning: First content block is not text. Type: {response_body['content'][0].get('type')}. Returning original text.")
                    return text
            else:
                 print(f"Warning: Unexpected or empty content in response from Bedrock model {model_id}. Returning original text.")
                 return text

        except Exception as e:
            print(f"Error during Bedrock post-processing with model {model_id}: {e}")
            return text

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

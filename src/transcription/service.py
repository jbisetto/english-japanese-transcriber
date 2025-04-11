"""Transcription service using AWS Transcribe streaming API."""

import io
import json
import time
import asyncio
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

import boto3
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent
from pydub import AudioSegment

class TranscriptionResultHandler(TranscriptResultStreamHandler):
    """Handler for streaming transcription results."""
    
    def __init__(self, output_path: str, transcript_result_stream=None):
        """Initialize the handler with an output path."""
        self.output_path = output_path
        self.results: List[Dict[str, Any]] = []
        self.is_partial = True
        super().__init__(transcript_result_stream)
    
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        """Handle incoming transcription events."""
        results = transcript_event.transcript.results
        
        for result in results:
            if not result.is_partial:
                self.is_partial = False
                alternative = result.alternatives[0]
                transcript = {
                    "text": alternative.transcript,
                    "start_time": result.start_time,
                    "end_time": result.end_time,
                    "confidence": getattr(alternative, 'confidence', 1.0)  # Default to 1.0 if confidence not provided
                }
                self.results.append(transcript)
    
    def save_results(self):
        """Save the transcription results to a file."""
        if not self.results or self.output_path is None:
            return
            
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        
        # Save results
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump({
                "results": {
                    "transcripts": [{"transcript": "".join(r["text"] for r in self.results)}],
                    "segments": self.results
                }
            }, f, ensure_ascii=False, indent=2)

class TranscriptionService:
    """Handles audio transcription using AWS Transcribe streaming API."""
    
    def __init__(self, aws_config, transcription_config):
        """
        Initialize the TranscriptionService with AWS configuration.

        Args:
            aws_config: Configuration object with AWS settings (region_name)
            transcription_config: Configuration object with model settings
        """
        self.aws_config = aws_config
        self.transcription_config = transcription_config
        
        # Initialize AWS clients
        self.transcribe_client = TranscribeStreamingClient(region=aws_config.region_name)
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=aws_config.region_name)
        
        # Store model IDs for post-processing
        self.english_model_id = transcription_config.english_model_id
        self.japanese_model_id = transcription_config.japanese_model_id

    async def _stream_audio(self, stream, audio_segment: AudioSegment):
        """Stream audio data to AWS Transcribe."""
        # Convert audio to raw PCM data
        buffer = io.BytesIO()
        audio_segment.export(buffer, format='wav')
        buffer.seek(0)  # Reset buffer position
        
        # Read and send chunks
        chunk_size = 8 * 1024  # 8KB chunks
        while True:
            chunk = buffer.read(chunk_size)
            if not chunk:
                break
            await stream.input_stream.send_audio_event(audio_chunk=chunk)
        
        await stream.input_stream.end_stream()

    async def transcribe_streaming(
        self,
        audio_segment: AudioSegment,
        language_code: str,
        output_path: str,
        identify_language: bool = False,
        language_options: List[str] = None,
        preferred_language: str = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio using streaming API.

        Args:
            audio_segment: The audio to transcribe
            language_code: Language code (e.g., "en-US", "ja-JP")
            output_path: Where to save the transcription results
            identify_language: Whether to enable language identification
            language_options: List of language codes to identify between (not used in streaming mode)
            preferred_language: Preferred language for faster identification (not used in streaming mode)

        Returns:
            Dict containing the transcription results
        """
        # Start transcription stream
        stream_params = {
            "media_sample_rate_hz": audio_segment.frame_rate,
            "media_encoding": "pcm",
            "enable_partial_results_stabilization": True,
            "partial_results_stability": "high",
            "language_code": language_code if language_code != "auto" else "en-US"  # Default to en-US if auto
        }
        
        # Start transcription stream
        stream = await self.transcribe_client.start_stream_transcription(**stream_params)
        
        # Set up handler with the stream
        handler = TranscriptionResultHandler(output_path, stream.output_stream)
        
        # Process audio stream
        await asyncio.gather(
            self._stream_audio(stream, audio_segment),
            handler.handle_events()
        )
        
        # Save results
        handler.save_results()
        
        # Return results if any were generated
        if handler.results:
            return {
                "results": {
                    "transcripts": [{"transcript": "".join(r["text"] for r in handler.results)}],
                    "segments": handler.results
                }
            }
        else:
            return {"results": {"transcripts": [{"transcript": ""}], "segments": []}}

    async def transcribe(
        self,
        audio_path: str,
        language_code: str,
        identify_language: bool = False,
        language_options: List[str] = None,
        preferred_language: str = None
    ) -> Dict[str, Any]:
        """
        Transcribe an audio file using streaming API.

        Args:
            audio_path: Path to the audio file
            language_code: Language code (e.g., "en-US", "ja-JP")
            identify_language: Whether to enable language identification
            language_options: List of language codes to identify between
            preferred_language: Preferred language for faster identification

        Returns:
            Dict containing the transcription results
        """
        try:
            # Load audio
            audio_segment = AudioSegment.from_file(audio_path)
            
            # Prepare output path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("output/transcripts")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"transcript_{timestamp}.json")
            
            # Run async transcription
            results = await self.transcribe_streaming(
                audio_segment,
                language_code,
                output_path,
                identify_language=identify_language,
                language_options=language_options,
                preferred_language=preferred_language
            )
            print(f"Debug - Transcription results: {json.dumps(results, indent=2)}")  # Debug log
            return results

        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return {"results": {"transcripts": [{"transcript": ""}], "segments": []}}

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
        transcribed_text = transcription_service.transcribe(audio_path, language)
        print(f"Transcribed text: {transcribed_text}")
    except Exception as e:
        print(f"Failed to transcribe audio: {e}")

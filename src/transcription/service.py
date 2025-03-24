from src.aws.bedrock_client import BedrockClient
from pydub import AudioSegment
import io
import base64
from typing import Dict, Any

class TranscriptionService:
    def __init__(self, bedrock_client: BedrockClient, english_model_id: str = "anthropic.claude-v2", japanese_model_id: str = "anthropic.claude-v2"):  # Replace with actual model IDs
        """
        Initializes the TranscriptionService with a Bedrock client and model IDs for English and Japanese transcription.

        Args:
            bedrock_client (BedrockClient): The Bedrock client to use.
            english_model_id (str, optional): The ID of the Bedrock model for English transcription.
                                                Defaults to "anthropic.claude-v2" (placeholder).
            japanese_model_id (str, optional): The ID of the Bedrock model for Japanese transcription.
                                                 Defaults to "anthropic.claude-v2" (placeholder).
        """
        self.bedrock_client = bedrock_client
        self.english_model_id = english_model_id
        self.japanese_model_id = japanese_model_id

    def transcribe(self, audio_segment: AudioSegment, language_code: str) -> str:
        """
        Transcribes the given audio segment using Amazon Bedrock.

        Args:
            audio_segment (AudioSegment): The audio segment to transcribe.
            language_code (str): The language code of the audio segment (e.g., "en" for English, "ja" for Japanese).

        Returns:
            str: The transcribed text.
        """
        try:
            # Convert audio segment to a suitable format (e.g., WAV)
            buffer = io.BytesIO()
            audio_segment.export(buffer, format="wav")
            audio_data = buffer.getvalue()

            # Encode audio data to base64
            audio_base64 = base64.b64encode(audio_data).decode("utf-8")

            # Construct the request body for the Bedrock model
            body = {
                "audio": audio_base64,  # Assuming the model accepts base64 encoded audio
                "language": language_code
            }

            # Invoke the Bedrock model based on the language
            model_id = self.english_model_id if language_code == "en" else self.japanese_model_id
            response = self.bedrock_client.invoke_model(model_id, body)

            # Extract the transcribed text from the response
            transcribed_text = response.get("text", "")  # Adjust based on the actual response format

            return transcribed_text
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return ""

if __name__ == '__main__':
    # Example usage (replace with your actual audio file path)
    from src.audio.handler import AudioHandler
    from src.language.detector import LanguageDetector

    bedrock_client = BedrockClient()  # Initialize Bedrock client
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

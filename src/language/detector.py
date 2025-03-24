from src.aws.bedrock_client import BedrockClient
from pydub import AudioSegment
import io
import base64
from typing import Dict, Any

class LanguageDetector:
    def __init__(self, bedrock_client: BedrockClient, model_id: str = "amazon.comprehend"):  # Replace with actual model ID
        """
        Initializes the LanguageDetector with a Bedrock client and model ID.

        Args:
            bedrock_client (BedrockClient): The Bedrock client to use.
            model_id (str, optional): The ID of the Bedrock model for language detection.
                                        Defaults to "amazon.comprehend" (placeholder).
        """
        self.bedrock_client = bedrock_client
        self.model_id = model_id

    def detect_language(self, audio_segment: AudioSegment) -> str:
        """
        Detects the language of the given audio segment using Amazon Bedrock.

        Args:
            audio_segment (AudioSegment): The audio segment to analyze.

        Returns:
            str: The detected language code (e.g., "en" for English, "ja" for Japanese).
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
                "text": audio_base64  # Assuming the model accepts base64 encoded audio
            }

            # Invoke the Bedrock model
            response = self.bedrock_client.invoke_model(self.model_id, body)

            # Extract the detected language from the response
            language_code = response.get("language_code", "unknown")  # Adjust based on the actual response format

            return language_code
        except Exception as e:
            print(f"Error detecting language: {e}")
            return "unknown"

if __name__ == '__main__':
    # Example usage (replace with your actual audio file path)
    from src.audio.handler import AudioHandler

    bedrock_client = BedrockClient()  # Initialize Bedrock client
    language_detector = LanguageDetector(bedrock_client)  # Initialize LanguageDetector

    audio_handler = AudioHandler()
    audio_path = "examples/sample_audio/sample.mp3"  # Replace with your audio file
    try:
        audio_segment = audio_handler.process_audio(audio_path)  # Process audio first
        language = language_detector.detect_language(audio_segment)
        print(f"Detected language: {language}")
    except Exception as e:
        print(f"Failed to detect language: {e}")

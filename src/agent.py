from src.audio.handler import AudioHandler
from src.audio.segmenter import AudioSegmenter
from src.language.detector import LanguageDetector
from src.transcription.service import TranscriptionService
from src.transcription.processor import TextProcessor
from src.output.manager import OutputManager
from src.config import AWSConfig, AudioConfig, TranscriptionConfig, LanguageDetectionConfig, OutputConfig
from typing import List, Dict

class TranscriptionAgent:
    def __init__(self,
                 aws_config: AWSConfig = AWSConfig(),
                 audio_config: AudioConfig = AudioConfig(),
                 transcription_config: TranscriptionConfig = TranscriptionConfig(),
                 language_detection_config: LanguageDetectionConfig = LanguageDetectionConfig(),
                 output_config: OutputConfig = OutputConfig()):
        """
        Initializes the TranscriptionAgent with configuration objects.

        Args:
            aws_config (AWSConfig, optional): AWS configuration.
            audio_config (AudioConfig, optional): Audio processing configuration.
            transcription_config (TranscriptionConfig, optional): Transcription configuration.
            language_detection_config (LanguageDetectionConfig, optional): Language detection configuration.
            output_config (OutputConfig, optional): Output configuration.
        """
        self.audio_handler = AudioHandler(target_sample_rate=audio_config.target_sample_rate, target_channels=audio_config.target_channels)
        self.audio_segmenter = AudioSegmenter()
        self.bedrock_client = self._create_bedrock_client(aws_config)
        self.language_detector = LanguageDetector(self.bedrock_client, model_id=language_detection_config.model_id)
        self.transcription_service = TranscriptionService(self.bedrock_client, english_model_id=transcription_config.english_model_id, japanese_model_id=transcription_config.japanese_model_id)
        self.text_processor = TextProcessor()
        self.output_manager = OutputManager(output_dir=output_config.output_dir)

    def _create_bedrock_client(self, aws_config: AWSConfig):
        """
        Creates a Bedrock client using the AWS configuration.

        Args:
            aws_config (AWSConfig): The AWS configuration.

        Returns:
            BedrockClient: The Bedrock client.
        """
        from src.aws.bedrock_client import BedrockClient
        return BedrockClient(region=aws_config.region_name)

    def transcribe_audio(self, audio_path: str) -> List[Dict[str, str]]:
        """
        Transcribes the audio file at the given path.

        Args:
            audio_path (str): The path to the audio file.

        Returns:
            List[Dict[str, str]]: A list of transcript entries, where each entry contains the language and transcribed text.
        """
        try:
            audio_segment = self.audio_handler.process_audio(audio_path)
            segments = self.audio_segmenter.segment_audio(audio_segment)

            transcript: List[Dict[str, str]] = []
            for segment in segments:
                language = self.language_detector.detect_language(segment)
                text = self.transcription_service.transcribe(segment, language)
                processed_text = self.text_processor.process_text(text, language)
                transcript_entry = {"language": language, "text": processed_text}
                transcript.append(transcript_entry)

            return transcript
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return []

    def process_and_save_transcript(self, audio_path: str, filename: str, format: str = "txt") -> None:
        """
        Transcribes the audio file and saves the transcript to a file.

        Args:
            audio_path (str): The path to the audio file.
            filename (str): The name of the file to save the transcript to.
            format (str, optional): The format to save the transcript in (txt, json, srt). Defaults to "txt".
        """
        transcript = self.transcribe_audio(audio_path)
        self.output_manager.save_transcript(transcript, filename, format)

if __name__ == '__main__':
    # Example usage
    agent = TranscriptionAgent()
    audio_path = "examples/sample_audio/sample.mp3"  # Replace with your audio file
    filename = "transcription"
    agent.process_and_save_transcript(audio_path, filename, format="txt")
    agent.process_and_save_transcript(audio_path, filename, format="json")
    agent.process_and_save_transcript(audio_path, filename, format="srt")

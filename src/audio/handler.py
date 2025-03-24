from pydub import AudioSegment
from typing import Optional

class AudioHandler:
    def __init__(self, target_sample_rate: int = 16000, target_channels: int = 1):
        """
        Initializes the AudioHandler with target audio parameters.

        Args:
            target_sample_rate (int, optional): The target sample rate in Hz. Defaults to 16000.
            target_channels (int, optional): The target number of channels (1 for mono, 2 for stereo). Defaults to 1.
        """
        self.target_sample_rate = target_sample_rate
        self.target_channels = target_channels

    def load_audio(self, audio_path: str) -> AudioSegment:
        """
        Loads an audio file using pydub.

        Args:
            audio_path (str): The path to the audio file.

        Returns:
            AudioSegment: The loaded audio segment.
        """
        try:
            audio_segment = AudioSegment.from_file(audio_path)
            return audio_segment
        except Exception as e:
            print(f"Error loading audio file: {e}")
            raise

    def convert_to_standard_format(self, audio_segment: AudioSegment) -> AudioSegment:
        """
        Converts the audio segment to the standard format (sample rate and channels).

        Args:
            audio_segment (AudioSegment): The audio segment to convert.

        Returns:
            AudioSegment: The converted audio segment.
        """
        audio_segment = audio_segment.set_frame_rate(self.target_sample_rate)
        audio_segment = audio_segment.set_channels(self.target_channels)
        return audio_segment

    def normalize_audio_level(self, audio_segment: AudioSegment, target_dbfs: float = -20.0) -> AudioSegment:
        """
        Normalizes the audio level of the audio segment.

        Args:
            audio_segment (AudioSegment): The audio segment to normalize.
            target_dbfs (float, optional): The target dBFS (decibels relative to full scale). Defaults to -20.0.

        Returns:
            AudioSegment: The normalized audio segment.
        """
        change_in_dbfs = target_dbfs - audio_segment.dBFS
        normalized_audio_segment = audio_segment.apply_gain(change_in_dbfs)
        return normalized_audio_segment

    def process_audio(self, audio_path: str) -> AudioSegment:
        """
        Loads, converts, and normalizes an audio file.

        Args:
            audio_path (str): The path to the audio file.

        Returns:
            AudioSegment: The processed audio segment.
        """
        audio_segment = self.load_audio(audio_path)
        audio_segment = self.convert_to_standard_format(audio_segment)
        audio_segment = self.normalize_audio_level(audio_segment)
        return audio_segment

if __name__ == '__main__':
    # Example usage (replace with your actual audio file path)
    audio_handler = AudioHandler()
    audio_path = "examples/sample_audio/sample.mp3"  # Replace with your audio file
    try:
        audio_segment = audio_handler.process_audio(audio_path)
        print("Audio processed successfully.")
        # You can now save the processed audio_segment to a file if needed
        # audio_segment.export("processed_audio.wav", format="wav")
    except Exception as e:
        print(f"Failed to process audio: {e}")

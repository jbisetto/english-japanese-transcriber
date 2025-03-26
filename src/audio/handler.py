import os
from pydub import AudioSegment
from typing import Optional, Set, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioProcessingError(Exception):
    """Custom exception for audio processing errors."""
    pass

class AudioHandler:
    # Supported input formats (based on pydub capabilities)
    SUPPORTED_FORMATS: Set[str] = {'mp3', 'wav', 'ogg', 'm4a', 'flac'}
    
    def __init__(self, target_sample_rate: int = 16000, target_channels: int = 1):
        """
        Initializes the AudioHandler with target audio parameters.

        Args:
            target_sample_rate (int, optional): The target sample rate in Hz. Defaults to 16000.
            target_channels (int, optional): The target number of channels (1 for mono, 2 for stereo). Defaults to 1.

        Raises:
            ValueError: If sample rate or channels are invalid.
        """
        if target_sample_rate <= 0:
            raise ValueError("Sample rate must be positive")
        if target_channels not in [1, 2]:
            raise ValueError("Channels must be either 1 (mono) or 2 (stereo)")
            
        self.target_sample_rate = target_sample_rate
        self.target_channels = target_channels

    def validate_audio_file(self, audio_path: str) -> Tuple[bool, str]:
        """
        Validates the audio file exists and has a supported format.

        Args:
            audio_path (str): The path to the audio file.

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not os.path.exists(audio_path):
            return False, f"Audio file not found: {audio_path}"
            
        file_ext = os.path.splitext(audio_path)[1].lower().lstrip('.')
        if file_ext not in self.SUPPORTED_FORMATS:
            return False, f"Unsupported audio format: {file_ext}. Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            
        return True, ""

    def load_audio(self, audio_path: str) -> AudioSegment:
        """
        Loads an audio file using pydub with validation.

        Args:
            audio_path (str): The path to the audio file.

        Returns:
            AudioSegment: The loaded audio segment.

        Raises:
            AudioProcessingError: If the file is invalid or cannot be loaded.
        """
        # Validate file
        is_valid, error_message = self.validate_audio_file(audio_path)
        if not is_valid:
            raise AudioProcessingError(error_message)

        try:
            audio_segment = AudioSegment.from_file(audio_path)
            logger.info(f"Loaded audio file: {audio_path} (duration: {len(audio_segment)/1000:.2f}s)")
            return audio_segment
        except Exception as e:
            error_msg = f"Error loading audio file: {str(e)}"
            logger.error(error_msg)
            raise AudioProcessingError(error_msg) from e

    def convert_to_standard_format(self, audio_segment: AudioSegment) -> AudioSegment:
        """
        Converts the audio segment to the standard format (sample rate and channels).

        Args:
            audio_segment (AudioSegment): The audio segment to convert.

        Returns:
            AudioSegment: The converted audio segment.

        Raises:
            AudioProcessingError: If conversion fails.
        """
        try:
            # Log original format
            logger.info(f"Converting audio: {audio_segment.frame_rate}Hz, {audio_segment.channels} channels -> "
                       f"{self.target_sample_rate}Hz, {self.target_channels} channels")
            
            # Convert sample rate if needed
            if audio_segment.frame_rate != self.target_sample_rate:
                audio_segment = audio_segment.set_frame_rate(self.target_sample_rate)
            
            # Convert channels if needed
            if audio_segment.channels != self.target_channels:
                audio_segment = audio_segment.set_channels(self.target_channels)
            
            return audio_segment
        except Exception as e:
            error_msg = f"Error converting audio format: {str(e)}"
            logger.error(error_msg)
            raise AudioProcessingError(error_msg) from e

    def normalize_audio_level(self, audio_segment: AudioSegment, target_dbfs: float = -20.0) -> AudioSegment:
        """
        Normalizes the audio level of the audio segment.

        Args:
            audio_segment (AudioSegment): The audio segment to normalize.
            target_dbfs (float, optional): The target dBFS (decibels relative to full scale). Defaults to -20.0.

        Returns:
            AudioSegment: The normalized audio segment.

        Raises:
            AudioProcessingError: If normalization fails.
            ValueError: If target_dbfs is invalid.
        """
        if target_dbfs > 0:
            raise ValueError("target_dbfs must be negative")

        try:
            original_dbfs = audio_segment.dBFS
            change_in_dbfs = target_dbfs - original_dbfs
            
            logger.info(f"Normalizing audio level: {original_dbfs:.1f} dBFS -> {target_dbfs:.1f} dBFS")
            
            normalized_audio_segment = audio_segment.apply_gain(change_in_dbfs)
            return normalized_audio_segment
        except Exception as e:
            error_msg = f"Error normalizing audio level: {str(e)}"
            logger.error(error_msg)
            raise AudioProcessingError(error_msg) from e

    def remove_silence(self, audio_segment: AudioSegment, silence_thresh: float = -50.0, min_silence_len: int = 500) -> AudioSegment:
        """
        Removes silent sections from the audio.

        Args:
            audio_segment (AudioSegment): The audio segment to process.
            silence_thresh (float, optional): The silence threshold in dBFS. Defaults to -50.0.
            min_silence_len (int, optional): Minimum length of silence in ms. Defaults to 500.

        Returns:
            AudioSegment: The processed audio segment with silence removed.

        Raises:
            AudioProcessingError: If silence removal fails.
            ValueError: If parameters are invalid.
        """
        if silence_thresh > 0:
            raise ValueError("silence_thresh must be negative")
        if min_silence_len < 0:
            raise ValueError("min_silence_len must be non-negative")

        try:
            from pydub.silence import split_on_silence
            
            # Split on silence and concatenate
            audio_chunks = split_on_silence(
                audio_segment,
                min_silence_len=min_silence_len,
                silence_thresh=silence_thresh,
                keep_silence=100  # Keep 100ms of silence between chunks
            )
            
            if not audio_chunks:
                logger.warning("No non-silent chunks found in audio")
                return audio_segment
            
            processed_audio = sum(audio_chunks)
            
            reduction = (len(audio_segment) - len(processed_audio)) / 1000
            logger.info(f"Removed {reduction:.2f}s of silence from audio")
            
            return processed_audio
        except Exception as e:
            error_msg = f"Error removing silence: {str(e)}"
            logger.error(error_msg)
            raise AudioProcessingError(error_msg) from e

    def process_audio(self, audio_path: str, remove_silence: bool = True) -> AudioSegment:
        """
        Loads, converts, normalizes, and optionally removes silence from an audio file.

        Args:
            audio_path (str): The path to the audio file.
            remove_silence (bool, optional): Whether to remove silence. Defaults to True.

        Returns:
            AudioSegment: The processed audio segment.

        Raises:
            AudioProcessingError: If any processing step fails.
        """
        try:
            # Load audio
            audio_segment = self.load_audio(audio_path)
            
            # Convert to standard format
            audio_segment = self.convert_to_standard_format(audio_segment)
            
            # Remove silence if requested
            if remove_silence:
                audio_segment = self.remove_silence(audio_segment)
            
            # Normalize audio level
            audio_segment = self.normalize_audio_level(audio_segment)
            
            logger.info(f"Audio processing completed successfully: {audio_path}")
            return audio_segment
            
        except (AudioProcessingError, ValueError) as e:
            # Re-raise these exceptions as they're already properly formatted
            raise
        except Exception as e:
            error_msg = f"Unexpected error processing audio: {str(e)}"
            logger.error(error_msg)
            raise AudioProcessingError(error_msg) from e

if __name__ == '__main__':
    # Example usage
    audio_handler = AudioHandler()
    audio_path = "examples/sample_audio/sample.mp3"
    
    try:
        audio_segment = audio_handler.process_audio(audio_path)
        print(f"Audio processed successfully. Duration: {len(audio_segment)/1000:.2f}s")
        
        # Example of saving the processed audio
        output_path = "processed_audio.wav"
        audio_segment.export(output_path, format="wav")
        print(f"Saved processed audio to: {output_path}")
        
    except AudioProcessingError as e:
        print(f"Failed to process audio: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

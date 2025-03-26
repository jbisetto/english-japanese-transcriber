import logging
from pydub import AudioSegment
from pydub.silence import split_on_silence, detect_nonsilent
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioSegmentationError(Exception):
    """Custom exception for audio segmentation errors."""
    pass

@dataclass
class SegmentationConfig:
    """Configuration for audio segmentation."""
    min_silence_len: int = 700  # Minimum length of silence in ms
    silence_thresh: int = -16   # Silence threshold in dBFS
    keep_silence: int = 200     # Amount of silence to keep around segments
    segment_duration: int = 10000  # Fixed segment duration in ms
    min_segment_length: int = 1000  # Minimum segment length in ms
    max_segment_length: int = 30000  # Maximum segment length in ms
    overlap: int = 0  # Overlap between segments in ms

class AudioSegmenter:
    def __init__(self, config: Optional[SegmentationConfig] = None):
        """
        Initializes the AudioSegmenter with configurable parameters.

        Args:
            config (Optional[SegmentationConfig]): Configuration for segmentation parameters.
                                                If None, default values will be used.
        """
        self.config = config or SegmentationConfig()
        self._validate_config()

    def _validate_config(self) -> None:
        """Validates the segmentation configuration."""
        if self.config.min_silence_len <= 0:
            raise ValueError("min_silence_len must be positive")
        if self.config.segment_duration <= 0:
            raise ValueError("segment_duration must be positive")
        if self.config.min_segment_length <= 0:
            raise ValueError("min_segment_length must be positive")
        if self.config.max_segment_length <= self.config.min_segment_length:
            raise ValueError("max_segment_length must be greater than min_segment_length")
        if self.config.overlap < 0:
            raise ValueError("overlap must be non-negative")
        if self.config.overlap >= self.config.segment_duration:
            raise ValueError("overlap must be less than segment_duration")

    def _get_audio_stats(self, audio_segment: AudioSegment) -> Dict[str, float]:
        """
        Calculates basic statistics for the audio segment.

        Args:
            audio_segment (AudioSegment): The audio segment to analyze.

        Returns:
            Dict[str, float]: Dictionary containing audio statistics.
        """
        return {
            'duration': len(audio_segment) / 1000,  # in seconds
            'dBFS': audio_segment.dBFS,
            'max_dBFS': audio_segment.max_dBFS,
            'rms': audio_segment.rms,
        }

    def split_on_silence(self, audio_segment: AudioSegment) -> List[AudioSegment]:
        """
        Splits the audio segment into chunks based on silence with advanced handling.

        Args:
            audio_segment (AudioSegment): The audio segment to split.

        Returns:
            List[AudioSegment]: A list of audio segments.

        Raises:
            AudioSegmentationError: If segmentation fails.
        """
        try:
            logger.info(f"Splitting audio on silence (threshold: {self.config.silence_thresh} dBFS, "
                       f"min_silence: {self.config.min_silence_len}ms)")

            # Detect non-silent ranges
            nonsilent_ranges = detect_nonsilent(
                audio_segment,
                min_silence_len=self.config.min_silence_len,
                silence_thresh=self.config.silence_thresh
            )

            if not nonsilent_ranges:
                logger.warning("No non-silent ranges detected in audio")
                return [audio_segment]

            # Split on silence with keep_silence parameter
            segments = split_on_silence(
                audio_segment,
                min_silence_len=self.config.min_silence_len,
                silence_thresh=self.config.silence_thresh,
                keep_silence=self.config.keep_silence
            )

            # Post-process segments
            processed_segments = []
            for segment in segments:
                # Skip segments that are too short
                if len(segment) < self.config.min_segment_length:
                    logger.debug(f"Skipping segment shorter than {self.config.min_segment_length}ms")
                    continue

                # Split segments that are too long
                if len(segment) > self.config.max_segment_length:
                    subsegments = self.split_into_fixed_length_segments(segment)
                    processed_segments.extend(subsegments)
                else:
                    processed_segments.append(segment)

            logger.info(f"Split audio into {len(processed_segments)} segments")
            return processed_segments

        except Exception as e:
            error_msg = f"Error splitting audio on silence: {str(e)}"
            logger.error(error_msg)
            raise AudioSegmentationError(error_msg) from e

    def split_into_fixed_length_segments(self, audio_segment: AudioSegment) -> List[AudioSegment]:
        """
        Splits the audio segment into fixed-length segments with optional overlap.

        Args:
            audio_segment (AudioSegment): The audio segment to split.

        Returns:
            List[AudioSegment]: A list of audio segments.

        Raises:
            AudioSegmentationError: If segmentation fails.
        """
        try:
            total_duration = len(audio_segment)
            segment_duration = self.config.segment_duration
            overlap = self.config.overlap

            if total_duration <= segment_duration:
                return [audio_segment]

            segments = []
            start = 0

            # Calculate step size considering overlap
            step = segment_duration - overlap

            while start + segment_duration <= total_duration:
                # Extract segment
                segment = audio_segment[start:start + segment_duration]
                
                # Only add segments that meet the minimum length requirement
                if len(segment) >= self.config.min_segment_length:
                    segments.append(segment)
                
                # Move start position by step size
                start += step

            # Handle the last segment if there's enough audio left
            remaining_duration = total_duration - start
            if remaining_duration >= self.config.min_segment_length:
                last_segment = audio_segment[-segment_duration:] if remaining_duration >= segment_duration else audio_segment[start:]
                segments.append(last_segment)

            logger.info(f"Split audio into {len(segments)} fixed-length segments "
                       f"(duration: {segment_duration}ms, overlap: {overlap}ms)")
            return segments

        except Exception as e:
            error_msg = f"Error splitting audio into fixed-length segments: {str(e)}"
            logger.error(error_msg)
            raise AudioSegmentationError(error_msg) from e

    def segment_by_energy(self, audio_segment: AudioSegment, energy_threshold: float = 0.2) -> List[AudioSegment]:
        """
        Segments audio based on energy levels using RMS values.

        Args:
            audio_segment (AudioSegment): The audio segment to segment.
            energy_threshold (float): Threshold for energy-based segmentation (0.0 to 1.0).

        Returns:
            List[AudioSegment]: A list of audio segments.

        Raises:
            AudioSegmentationError: If segmentation fails.
        """
        try:
            if not 0 <= energy_threshold <= 1:
                raise ValueError("energy_threshold must be between 0 and 1")

            # Calculate RMS values for small windows
            window_size = 100  # ms
            rms_values = []
            for i in range(0, len(audio_segment), window_size):
                chunk = audio_segment[i:i + window_size]
                rms_values.append(chunk.rms)

            # Normalize RMS values
            rms_values = np.array(rms_values)
            if rms_values.max() > 0:
                rms_values = rms_values / rms_values.max()

            # Find segments based on energy threshold
            segments = []
            start = 0
            in_segment = False

            for i, energy in enumerate(rms_values):
                if energy > energy_threshold and not in_segment:
                    start = i * window_size
                    in_segment = True
                elif energy <= energy_threshold and in_segment:
                    end = i * window_size
                    if end - start >= self.config.min_segment_length:
                        segments.append(audio_segment[start:end])
                    in_segment = False

            # Handle the last segment
            if in_segment:
                end = len(audio_segment)
                if end - start >= self.config.min_segment_length:
                    segments.append(audio_segment[start:end])

            logger.info(f"Split audio into {len(segments)} segments based on energy levels")
            return segments

        except Exception as e:
            error_msg = f"Error segmenting audio by energy: {str(e)}"
            logger.error(error_msg)
            raise AudioSegmentationError(error_msg) from e

    def segment_audio(self, audio_segment: AudioSegment, method: str = "silence") -> List[AudioSegment]:
        """
        Segments the audio segment using the specified method.

        Args:
            audio_segment (AudioSegment): The audio segment to segment.
            method (str): Segmentation method to use:
                         - "silence": Split on silence
                         - "fixed": Fixed-length segments
                         - "energy": Energy-based segmentation

        Returns:
            List[AudioSegment]: A list of audio segments.

        Raises:
            AudioSegmentationError: If segmentation fails.
            ValueError: If an invalid method is specified.
        """
        # Log audio statistics
        stats = self._get_audio_stats(audio_segment)
        logger.info(f"Processing audio: duration={stats['duration']:.2f}s, "
                   f"dBFS={stats['dBFS']:.2f}, max_dBFS={stats['max_dBFS']:.2f}")

        try:
            if method == "silence":
                return self.split_on_silence(audio_segment)
            elif method == "fixed":
                return self.split_into_fixed_length_segments(audio_segment)
            elif method == "energy":
                return self.segment_by_energy(audio_segment)
            else:
                raise ValueError(f"Invalid segmentation method: {method}")

        except (AudioSegmentationError, ValueError) as e:
            # Re-raise these exceptions as they're already properly formatted
            raise
        except Exception as e:
            error_msg = f"Unexpected error during audio segmentation: {str(e)}"
            logger.error(error_msg)
            raise AudioSegmentationError(error_msg) from e

if __name__ == '__main__':
    # Example usage
    from src.audio.handler import AudioHandler

    # Create custom configuration
    config = SegmentationConfig(
        min_silence_len=500,
        silence_thresh=-20,
        keep_silence=100,
        segment_duration=15000,
        min_segment_length=1000,
        max_segment_length=20000,
        overlap=500
    )

    audio_handler = AudioHandler()
    audio_segmenter = AudioSegmenter(config)
    audio_path = "examples/sample_audio/sample.mp3"  # Replace with your audio file

    try:
        # Process audio
        audio_segment = audio_handler.process_audio(audio_path)
        
        # Try different segmentation methods
        silence_segments = audio_segmenter.segment_audio(audio_segment, method="silence")
        fixed_segments = audio_segmenter.segment_audio(audio_segment, method="fixed")
        energy_segments = audio_segmenter.segment_audio(audio_segment, method="energy")

        print(f"\nSegmentation results:")
        print(f"Silence-based: {len(silence_segments)} segments")
        print(f"Fixed-length: {len(fixed_segments)} segments")
        print(f"Energy-based: {len(energy_segments)} segments")

        # Example of saving segments
        # for i, segment in enumerate(silence_segments):
        #     segment.export(f"segment_silence_{i}.wav", format="wav")

    except AudioSegmentationError as e:
        print(f"Segmentation error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

from pydub import AudioSegment
from pydub.silence import split_on_silence
from typing import List

class AudioSegmenter:
    def __init__(self, min_silence_len: int = 700, silence_thresh: int = -16, segment_duration: int = 10000):
        """
        Initializes the AudioSegmenter with silence detection and segment duration parameters.

        Args:
            min_silence_len (int, optional): The minimum length of silence in milliseconds to be considered a silence. Defaults to 700.
            silence_thresh (int, optional): The silence threshold in dBFS. Defaults to -16.
            segment_duration (int, optional): The duration of each segment in milliseconds when using fixed-length segmentation. Defaults to 10000 (10 seconds).
        """
        self.min_silence_len = min_silence_len
        self.silence_thresh = silence_thresh
        self.segment_duration = segment_duration

    def split_on_silence(self, audio_segment: AudioSegment) -> List[AudioSegment]:
        """
        Splits the audio segment into chunks based on silence.

        Args:
            audio_segment (AudioSegment): The audio segment to split.

        Returns:
            List[AudioSegment]: A list of audio segments.
        """
        try:
            segments = split_on_silence(
                audio_segment,
                min_silence_len=self.min_silence_len,
                silence_thresh=self.silence_thresh,
                keep_silence=200,  # Keep some silence around the segments
            )
            return segments
        except Exception as e:
            print(f"Error splitting on silence: {e}")
            raise

    def split_into_fixed_length_segments(self, audio_segment: AudioSegment) -> List[AudioSegment]:
        """
        Splits the audio segment into fixed-length segments.

        Args:
            audio_segment (AudioSegment): The audio segment to split.

        Returns:
            List[AudioSegment]: A list of audio segments.
        """
        segments = []
        segment_length = self.segment_duration
        start = 0
        while start < len(audio_segment):
            end = start + segment_length
            segments.append(audio_segment[start:end])
            start = end
        return segments

    def segment_audio(self, audio_segment: AudioSegment, segment_by_silence: bool = True) -> List[AudioSegment]:
        """
        Segments the audio segment using either silence detection or fixed-length segmentation.

        Args:
            audio_segment (AudioSegment): The audio segment to segment.
            segment_by_silence (bool, optional): Whether to segment by silence. Defaults to True.

        Returns:
            List[AudioSegment]: A list of audio segments.
        """
        if segment_by_silence:
            return self.split_on_silence(audio_segment)
        else:
            return self.split_into_fixed_length_segments(audio_segment)

if __name__ == '__main__':
    # Example usage (replace with your actual audio file path)
    from src.audio.handler import AudioHandler  # Import AudioHandler for processing

    audio_handler = AudioHandler()
    audio_path = "examples/sample_audio/sample.mp3"  # Replace with your audio file
    try:
        audio_segment = audio_handler.process_audio(audio_path)  # Process audio first
        audio_segmenter = AudioSegmenter()
        segments = audio_segmenter.segment_audio(audio_segment, segment_by_silence=True)

        print(f"Audio segmented into {len(segments)} segments.")
        # You can now process each segment individually
        # for i, segment in enumerate(segments):
        #     segment.export(f"segment_{i}.wav", format="wav")
    except Exception as e:
        print(f"Failed to segment audio: {e}")

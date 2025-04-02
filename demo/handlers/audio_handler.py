"""
Audio handling module for the demo interface.

This module provides functionality for:
- Managing audio recordings
- Handling file uploads
- Validating audio formats
- Managing the recordings directory
"""

import os
import wave
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
import soundfile as sf
import numpy as np
from pydub import AudioSegment

class AudioValidationError(Exception):
    """Raised when audio validation fails."""
    pass

class AudioHandler:
    """Handles audio recording and file operations for the demo interface."""
    
    SUPPORTED_FORMATS = {
        'wav': ['audio/wav', 'audio/x-wav'],
        'mp3': ['audio/mpeg', 'audio/mp3'],
        'm4a': ['audio/mp4', 'audio/x-m4a'],
        'flac': ['audio/flac']
    }
    
    def __init__(self, recordings_dir: str = "recordings"):
        """
        Initialize the AudioHandler.
        
        Args:
            recordings_dir (str): Directory to store recordings
        """
        self.recordings_dir = Path(recordings_dir)
        self.recordings_dir.mkdir(parents=True, exist_ok=True)
        self._cleanup_old_recordings()
    
    def validate_format(self, file_path: str, mime_type: Optional[str] = None) -> bool:
        """
        Validate if the audio file format is supported.
        
        Args:
            file_path (str): Path to the audio file
            mime_type (str, optional): MIME type of the file
            
        Returns:
            bool: True if format is supported
            
        Raises:
            AudioValidationError: If format is not supported
        """
        ext = Path(file_path).suffix.lower()[1:]
        if ext not in self.SUPPORTED_FORMATS:
            raise AudioValidationError(f"Unsupported audio format: {ext}")
            
        if mime_type and not any(mime_type in types for types in self.SUPPORTED_FORMATS.values()):
            raise AudioValidationError(f"Unsupported MIME type: {mime_type}")
            
        return True
    
    def save_recording(self, audio_data: np.ndarray, sample_rate: int) -> str:
        """
        Save a recording from numpy array data.
        
        Args:
            audio_data (np.ndarray): Audio data
            sample_rate (int): Sample rate of the audio
            
        Returns:
            str: Path to the saved recording
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.wav"
        filepath = self.recordings_dir / filename
        
        sf.write(str(filepath), audio_data, sample_rate)
        return str(filepath)
    
    def process_upload(self, upload_path: str) -> Dict[str, str]:
        """
        Process an uploaded audio file.
        
        Args:
            upload_path (str): Path to the uploaded file
            
        Returns:
            Dict[str, str]: Paths to the processed files:
                - 'playback': High-quality version for playback
                - 'transcription': Optimized version for transcription
        """
        self.validate_format(upload_path)
        
        # Load audio and get original properties
        audio = AudioSegment.from_file(upload_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save playback version - preserve original properties
        playback_path = self.recordings_dir / f"playback_{timestamp}.wav"
        audio.export(str(playback_path), format='wav')
        
        # Create optimized version for transcription (16kHz mono)
        transcription_path = self.recordings_dir / f"transcription_{timestamp}.wav"
        transcription_audio = audio
        if audio.frame_rate != 16000:
            transcription_audio = transcription_audio.set_frame_rate(16000)
        if audio.channels != 1:
            transcription_audio = transcription_audio.set_channels(1)
        transcription_audio.export(str(transcription_path), format='wav')
        
        return {
            'playback': str(playback_path),
            'transcription': str(transcription_path)
        }
    
    def get_audio_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get information about an audio file.
        
        Args:
            file_path (str): Path to the audio file
            
        Returns:
            Dict[str, Any]: Audio file information
        """
        audio = AudioSegment.from_file(file_path)
        return {
            'duration': len(audio) / 1000.0,  # Convert to seconds
            'sample_rate': audio.frame_rate,
            'channels': audio.channels,
            'format': Path(file_path).suffix[1:],
            'size_bytes': os.path.getsize(file_path)
        }
    
    def _cleanup_old_recordings(self, max_age_hours: int = 24) -> None:
        """
        Clean up old recordings.
        
        Args:
            max_age_hours (int): Maximum age of recordings in hours
        """
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        for file in self.recordings_dir.glob("*.wav"):
            if file.stat().st_mtime < cutoff_time:
                file.unlink()
    
    def list_recordings(self) -> List[Dict[str, Any]]:
        """
        List all recordings with their information.
        
        Returns:
            List[Dict[str, Any]]: List of recording information
        """
        recordings = []
        for file in sorted(self.recordings_dir.glob("*.wav"), key=lambda x: x.stat().st_mtime, reverse=True):
            info = self.get_audio_info(str(file))
            recordings.append({
                'path': str(file),
                'created': datetime.fromtimestamp(file.stat().st_mtime),
                **info
            })
        return recordings 
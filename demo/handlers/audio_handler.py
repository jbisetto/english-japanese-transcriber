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
from typing import Optional, Tuple, List
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
    
    def process_upload(self, upload_path: str) -> str:
        """
        Process an uploaded audio file.
        
        Args:
            upload_path (str): Path to the uploaded file
            
        Returns:
            str: Path to the processed file in recordings directory
        """
        self.validate_format(upload_path)
        
        # Convert to WAV for consistent processing
        audio = AudioSegment.from_file(upload_path)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"upload_{timestamp}.wav"
        filepath = self.recordings_dir / filename
        
        audio.export(str(filepath), format='wav')
        return str(filepath)
    
    def get_audio_info(self, file_path: str) -> dict:
        """
        Get information about an audio file.
        
        Args:
            file_path (str): Path to the audio file
            
        Returns:
            dict: Audio file information
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
        Clean up recordings older than specified hours.
        
        Args:
            max_age_hours (int): Maximum age of recordings in hours
        """
        current_time = datetime.now().timestamp()
        for file in self.recordings_dir.glob("*"):
            if file.is_file():
                file_age = current_time - file.stat().st_mtime
                if file_age > (max_age_hours * 3600):
                    file.unlink()
    
    def list_recordings(self) -> List[dict]:
        """
        List all recordings with their information.
        
        Returns:
            List[dict]: List of recordings with their details
        """
        recordings = []
        for file in self.recordings_dir.glob("*"):
            if file.is_file():
                try:
                    info = self.get_audio_info(str(file))
                    info['path'] = str(file)
                    info['created'] = datetime.fromtimestamp(file.stat().st_mtime)
                    recordings.append(info)
                except Exception:
                    continue
        return recordings 
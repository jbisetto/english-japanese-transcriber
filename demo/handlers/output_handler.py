"""
Output handling module for the demo interface.

This module provides:
- Multiple output format support (TXT, JSON, SRT)
- Pretty printing capabilities
- Language-specific formatting
- Output preview generation
"""

import json
from pathlib import Path
from typing import Union, Dict, List, Any, Optional
from datetime import datetime, timedelta

class OutputFormatError(Exception):
    """Raised when output format validation fails."""
    pass

class OutputHandler:
    """Handles output processing and formatting for the demo interface."""
    
    SUPPORTED_FORMATS = ['txt', 'json', 'srt']
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the output handler.
        
        Args:
            output_dir (str): Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def format_japanese_text(self, text: str) -> str:
        """
        Format Japanese text with proper spacing and punctuation.
        
        Args:
            text (str): Japanese text to format
            
        Returns:
            str: Formatted Japanese text
        """
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Ensure proper spacing around Japanese punctuation
        punctuation = '。、！？'
        for p in punctuation:
            text = text.replace(f' {p}', p)
            text = text.replace(f'{p} ', f'{p}')
        
        # Remove spaces between Japanese characters
        parts = []
        current_part = ""
        
        for char in text:
            if ord(char) > 0x3000:  # Japanese character range
                if current_part and current_part[-1] == ' ':
                    current_part = current_part[:-1]
                current_part += char
            else:
                if char != ' ' or (current_part and ord(current_part[-1]) <= 0x3000):
                    current_part += char
        
        return current_part
    
    def create_srt_timestamps(self, duration: float, segments: List[Dict[str, Any]]) -> List[str]:
        """
        Create SRT format timestamps for segments.
        
        Args:
            duration (float): Total audio duration in seconds
            segments (List[Dict]): List of segment information
            
        Returns:
            List[str]: List of SRT format timestamps
        """
        def format_time(seconds: float) -> str:
            """Format seconds to SRT timestamp."""
            time = str(timedelta(seconds=seconds))
            if '.' not in time:
                time += '.000'
            return time.replace('.', ',')[:12]
        
        timestamps = []
        for i, segment in enumerate(segments):
            start = segment.get('start', 0)
            end = segment.get('end', start + duration/len(segments))
            timestamps.append(f"{format_time(start)} --> {format_time(end)}")
        
        return timestamps
    
    def format_as_txt(self, transcription: Dict[str, Any]) -> str:
        """
        Format transcription as plain text.
        
        Args:
            transcription (Dict): Transcription data
            
        Returns:
            str: Formatted text
        """
        text = transcription.get('text', '')
        language = transcription.get('language', 'en')
        
        if language == 'ja':
            text = self.format_japanese_text(text)
        
        return text
    
    def format_as_json(self, transcription: Dict[str, Any], pretty: bool = True) -> str:
        """
        Format transcription as JSON.
        
        Args:
            transcription (Dict): Transcription data
            pretty (bool): Whether to pretty print
            
        Returns:
            str: JSON string
        """
        if pretty:
            return json.dumps(transcription, indent=2, ensure_ascii=False)
        return json.dumps(transcription, ensure_ascii=False)
    
    def format_as_srt(self, transcription: Dict[str, Any]) -> str:
        """
        Format transcription as SRT subtitles.
        
        Args:
            transcription (Dict): Transcription data
            
        Returns:
            str: SRT formatted string
        """
        segments = transcription.get('segments', [])
        duration = transcription.get('duration', 0)
        language = transcription.get('language', 'en')
        
        timestamps = self.create_srt_timestamps(duration, segments)
        
        srt_parts = []
        for i, (segment, timestamp) in enumerate(zip(segments, timestamps), 1):
            text = segment.get('text', '')
            if language == 'ja':
                text = self.format_japanese_text(text)
            
            srt_parts.extend([
                str(i),
                timestamp,
                text,
                ''  # Empty line between entries
            ])
        
        return '\n'.join(srt_parts)
    
    def format_as_txt_english(self, transcription: Dict[str, Any]) -> str:
        """Format transcription as English text.
        
        Args:
            transcription: The transcription data
            
        Returns:
            str: Formatted English text
        """
        if not transcription:
            return ""
            
        text = transcription.get('text', '')
        if isinstance(text, list):
            return "\n".join(text)
        return str(text)
        
    def format_as_txt_japanese(self, transcription: Dict[str, Any]) -> str:
        """Format transcription as Japanese text.
        
        Args:
            transcription: The transcription data
            
        Returns:
            str: Formatted Japanese text
        """
        if not transcription:
            return ""
            
        text = transcription.get('text', '')
        if isinstance(text, list):
            return "。\n".join(text) + "。"
        return str(text)
    
    def save_output(
        self,
        transcription: Dict[str, Any],
        format: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Save transcription in specified format.
        
        Args:
            transcription (Dict): Transcription data
            format (str): Output format (txt, json, srt)
            filename (str, optional): Base filename without extension
            
        Returns:
            str: Path to saved file
            
        Raises:
            OutputFormatError: If format is not supported
        """
        format = format.lower()
        if format not in self.SUPPORTED_FORMATS:
            raise OutputFormatError(f"Unsupported output format: {format}")
        
        if filename is None:
            filename = f"transcription_{datetime.now():%Y%m%d_%H%M%S}"
        
        output_path = self.output_dir / f"{filename}.{format}"
        
        content = {
            'txt': lambda: self.format_as_txt(transcription),
            'json': lambda: self.format_as_json(transcription),
            'srt': lambda: self.format_as_srt(transcription)
        }[format]()
        
        output_path.write_text(content, encoding='utf-8')
        return str(output_path)
    
    def generate_preview(
        self,
        transcription: Dict[str, Any],
        format: str,
        max_length: int = 500
    ) -> str:
        """
        Generate a preview of the output.
        
        Args:
            transcription (Dict): Transcription data
            format (str): Output format
            max_length (int): Maximum preview length
            
        Returns:
            str: Preview text
            
        Raises:
            OutputFormatError: If format is not supported
        """
        format = format.lower()
        if format not in self.SUPPORTED_FORMATS:
            raise OutputFormatError(f"Unsupported output format: {format}")
        
        content = {
            'txt': lambda: self.format_as_txt(transcription),
            'json': lambda: self.format_as_json(transcription),
            'srt': lambda: self.format_as_srt(transcription)
        }[format]()
        
        if len(content) > max_length:
            return content[:max_length] + "..."
        return content
    
    def format_output(
        self,
        transcription: Dict[str, Any],
        format: str = "txt",
        language: str = "auto-detect"
    ) -> str:
        """Format the transcription output.
        
        Args:
            transcription: The transcription data
            format: Output format (txt, json, srt)
            language: Language option for formatting
            
        Returns:
            str: Formatted output
            
        Raises:
            OutputFormatError: If format is invalid
        """
        if format not in ["txt", "json", "srt"]:
            raise OutputFormatError(f"Invalid output format: {format}")
            
        if format == "txt":
            if language == "force-japanese":
                return self.format_as_txt_japanese(transcription)
            else:
                return self.format_as_txt_english(transcription)
                
        elif format == "json":
            return self.format_as_json(transcription)
            
        else:  # srt
            return self.format_as_srt(transcription) 
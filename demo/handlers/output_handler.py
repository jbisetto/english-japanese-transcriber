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
from ..utils.logger import DemoLogger

class OutputFormatError(Exception):
    """Raised when output format validation fails."""
    pass

class OutputHandler:
    """Handles output processing and formatting for the demo interface."""
    
    SUPPORTED_FORMATS = ['txt', 'json', 'srt']
    
    def __init__(self, output_dir: str = "demo/output", logger=None):
        """
        Initialize the output handler.
        
        Args:
            output_dir (str): Directory for output files
            logger: Logger instance
        """
        self.output_dir = Path(output_dir)
        self.transcripts_dir = self.output_dir / "transcripts"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger or DemoLogger()
    
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
    
    def format_output(self, transcription: Dict[str, Any], format: str = "txt") -> str:
        """Format transcription output in the specified format."""
        try:
            self.logger.debug(f"Selected format: {format}")
            
            if not transcription or "results" not in transcription:
                return ""
            
            # Check for empty results
            if not transcription["results"].get("transcripts"):
                return ""
            
            # Get the raw transcript text
            raw_text = transcription["results"]["transcripts"][0]["transcript"]
            self.logger.debug(f"Raw transcription text: {raw_text}")
            
            # Handle different output formats
            if format.lower() == "txt":
                self.logger.debug("Using TXT format: returning raw transcript text")
                # Ensure proper spacing between languages
                parts = []
                current_text = ""
                current_lang = None
                
                for segment in transcription["results"].get("segments", []):
                    text = segment.get("text", "").strip()
                    lang = segment.get("language")
                    
                    # If language changes, add current text to parts
                    if lang != current_lang and current_text:
                        parts.append(current_text.strip())
                        current_text = ""
                    
                    # Add space for English, no space for Japanese
                    if lang == "en-US":
                        if current_text and not current_text.endswith(" "):
                            current_text += " "
                        current_text += text
                        if not current_text.endswith(" "):
                            current_text += " "
                    else:  # Japanese
                        current_text += text
                    
                    current_lang = lang
                
                # Add any remaining text
                if current_text:
                    parts.append(current_text.strip())
                
                return " ".join(parts).strip()
            
            elif format.lower() == "json":
                self.logger.debug("Using JSON format")
                # Create a clean copy of the transcription
                clean_transcription = {
                    "results": {
                        "transcripts": transcription["results"]["transcripts"],
                        "segments": []
                    }
                }
                
                # Clean up segments
                for segment in transcription["results"].get("segments", []):
                    clean_segment = {
                        "start_time": segment.get("start_time", "0"),
                        "end_time": segment.get("end_time", "0"),
                        "text": segment.get("text", ""),
                        "language": segment.get("language", "unknown"),
                        "confidence": segment.get("confidence", 0)
                    }
                    clean_transcription["results"]["segments"].append(clean_segment)
                
                return json.dumps(clean_transcription, ensure_ascii=False, indent=2)
            
            elif format.lower() == "srt":
                self.logger.debug("Using SRT format")
                segments = transcription["results"].get("segments", [])
                if not segments:
                    return ""
                
                srt_parts = []
                for i, segment in enumerate(segments, 1):
                    start_time = float(segment.get("start_time", 0))
                    end_time = float(segment.get("end_time", 0))
                    text = segment.get("text", "").strip()
                    
                    if not text:
                        continue
                    
                    # Format times as SRT timestamps (HH:MM:SS,mmm)
                    start = str(timedelta(seconds=start_time)).replace(".", ",")[:11]
                    end = str(timedelta(seconds=end_time)).replace(".", ",")[:11]
                    
                    srt_parts.extend([
                        str(i),
                        f"{start} --> {end}",
                        text,
                        ""  # Empty line between entries
                    ])
                
                return "\n".join(srt_parts)
            
            else:
                raise OutputFormatError(f"Unsupported output format: {format}")
                
        except Exception as e:
            self.logger.error(f"Error formatting output: {str(e)}")
            raise OutputFormatError(f"Failed to format output: {str(e)}")
    
    def save_output(self, transcription: Dict[str, Any], format: str = "txt") -> None:
        """Save transcription output to a file."""
        if not transcription:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"transcript_{timestamp}.{format}"
        filepath = self.transcripts_dir / filename

        formatted_output = self.format_output(transcription, format)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(formatted_output)
            self.logger.info(f"Saved output to {filepath}")
            return str(filepath)
        except Exception as e:
            self.logger.error(f"Failed to save output: {e}")
            return None
    
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
        
        content = self.format_output(transcription, format)
        
        if len(content) > max_length:
            return content[:max_length] + "..."
        return content 
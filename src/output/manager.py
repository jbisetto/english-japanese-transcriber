import os
from typing import List, Dict
from .adapters import TranscriptAdapterFactory

class OutputManager:
    """Manages the output of transcripts in various formats."""
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the OutputManager.
        
        Args:
            output_dir (str): Directory where output files will be saved
        """
        self.output_dir = output_dir
        self._ensure_output_dir_exists()
    
    def _ensure_output_dir_exists(self) -> None:
        """Create the output directory if it doesn't exist."""
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _get_output_path(self, filename: str, format: str) -> str:
        """
        Get the full path for the output file.
        
        Args:
            filename (str): Base filename without extension
            format (str): Output format extension
            
        Returns:
            str: Full path to the output file
        """
        return os.path.join(self.output_dir, f"{filename}.{format}")
    
    def save_transcript(self, transcript: List[Dict[str, str]], filename: str, format: str = "txt") -> None:
        """
        Save the transcript in the specified format.
        
        Args:
            transcript (List[Dict[str, str]]): List of transcript entries
            filename (str): Name of the output file (without extension)
            format (str): Output format ("txt", "json", or "srt")
            
        Raises:
            ValueError: If the format is not supported
            IOError: If there's an error writing the file
        """
        try:
            # Get the appropriate adapter for the format
            adapter = TranscriptAdapterFactory.get_adapter(format)
            
            # Format the transcript
            formatted_content = adapter.format_transcript(transcript)
            
            # Write to file
            output_path = self._get_output_path(filename, format)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
                
        except ValueError as e:
            raise ValueError(f"Failed to save transcript: {str(e)}")
        except IOError as e:
            raise IOError(f"Failed to write transcript file: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error saving transcript: {str(e)}")

if __name__ == '__main__':
    # Example usage
    output_manager = OutputManager()
    
    # Sample transcript
    sample_transcript = [
        {"language": "en", "text": "Hello, this is a test transcript."},
        {"language": "ja", "text": "こんにちは、これはテスト用の文章です。"}
    ]
    
    # Save in different formats
    output_manager.save_transcript(sample_transcript, "example", "txt")
    output_manager.save_transcript(sample_transcript, "example", "json")
    output_manager.save_transcript(sample_transcript, "example", "srt")

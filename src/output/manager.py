import json
from typing import List, Dict

class OutputManager:
    def __init__(self, output_dir: str = "output"):
        """
        Initializes the OutputManager with an output directory.

        Args:
            output_dir (str, optional): The directory to save the output files. Defaults to "output".
        """
        self.output_dir = output_dir

    def format_as_txt(self, transcript: List[Dict[str, str]]) -> str:
        """
        Formats the transcript as a plain text string.

        Args:
            transcript (List[Dict[str, str]]): The transcript data.

        Returns:
            str: The formatted text.
        """
        text = ""
        for entry in transcript:
            text += f"{entry['language']}: {entry['text']}\n"
        return text

    def format_as_json(self, transcript: List[Dict[str, str]]) -> str:
        """
        Formats the transcript as a JSON string.

        Args:
            transcript (List[Dict[str, str]]): The transcript data.

        Returns:
            str: The formatted JSON string.
        """
        return json.dumps(transcript, indent=4, ensure_ascii=False)

    def format_as_srt(self, transcript: List[Dict[str, str]]) -> str:
        """
        Formats the transcript as an SRT (SubRip Subtitle) string.

        Args:
            transcript (List[Dict[str, str]]): The transcript data.

        Returns:
            str: The formatted SRT string.
        """
        srt_string = ""
        for i, entry in enumerate(transcript):
            srt_string += f"{i+1}\n"
            # Assuming each entry represents a segment with a start and end time
            srt_string += "00:00:00,000 --> 00:00:00,000\n"  # Placeholder timestamps
            srt_string += f"{entry['text']}\n\n"
        return srt_string

    def save_transcript(self, transcript: List[Dict[str, str]], filename: str, format: str = "txt") -> None:
        """
        Saves the transcript to a file in the specified format.

        Args:
            transcript (List[Dict[str, str]]): The transcript data.
            filename (str): The name of the file to save.
            format (str, optional): The format to save the transcript in (txt, json, srt). Defaults to "txt".
        """
        try:
            # Create the output directory if it doesn't exist
            import os
            os.makedirs(self.output_dir, exist_ok=True)

            filepath = os.path.join(self.output_dir, f"{filename}.{format}")

            if format == "txt":
                formatted_text = self.format_as_txt(transcript)
            elif format == "json":
                formatted_text = self.format_as_json(transcript)
            elif format == "srt":
                formatted_text = self.format_as_srt(transcript)
            else:
                raise ValueError(f"Unsupported format: {format}")

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(formatted_text)

            print(f"Transcript saved to {filepath}")

        except Exception as e:
            print(f"Error saving transcript: {e}")

if __name__ == '__main__':
    # Example usage
    output_manager = OutputManager()
    transcript = [
        {"language": "en", "text": "This is a test."},
        {"language": "ja", "text": "これはテストです。"}
    ]
    output_manager.save_transcript(transcript, "sample_transcript", format="txt")
    output_manager.save_transcript(transcript, "sample_transcript", format="json")
    output_manager.save_transcript(transcript, "sample_transcript", format="srt")

"""Web interface for the transcription demo.

This module provides the main web interface using Gradio, with enhanced
error handling and user feedback.
"""

import gradio as gr
from typing import Tuple, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import json

from demo.handlers.audio_handler import AudioHandler
from demo.handlers.output_handler import OutputHandler
from demo.utils.logger import DemoLogger
from ..utils.errors import (
    DemoError, AudioValidationError, AudioProcessingError,
    TranscriptionError, LanguageDetectionError, ServiceUnavailableError,
    OutputFormatError, ResourceError
)

class TranscriptionUI:
    """Main web interface for the transcription demo."""
    
    def __init__(
        self,
        audio_handler: AudioHandler,
        output_handler: OutputHandler,
        transcriber: Any,  # Can be AWS or Google transcription service
        logger: Optional[DemoLogger] = None
    ):
        """Initialize the web interface."""
        self.logger = logger or DemoLogger()
        self.audio_handler = audio_handler
        # Pass logger to output handler
        self.output_handler = output_handler
        if not hasattr(self.output_handler, 'logger'):
            self.output_handler.logger = self.logger
        self.transcriber = transcriber
        
        # Track operation state
        self.current_operation: Optional[str] = None
        self.operation_start_time: Optional[datetime] = None
        
        # Initialize interface components
        self.error_box = None
        self.status_box = None
        self.progress_bar = None
    
    def clear_files(self) -> Tuple[str, str]:
        """Clear all output and recording files except .gitkeep."""
        try:
            # Clear output files
            output_dir = Path("demo/output")
            transcripts_dir = output_dir / "transcripts"
            
            # Create directories if they don't exist
            output_dir.mkdir(parents=True, exist_ok=True)
            transcripts_dir.mkdir(parents=True, exist_ok=True)
            
            # Clear files in output directory
            for file in output_dir.glob("*"):
                if file.is_file() and file.name != ".gitkeep":
                    file.unlink()
            
            # Clear files in transcripts directory
            for file in transcripts_dir.glob("*"):
                if file.is_file() and file.name != ".gitkeep":
                    file.unlink()
            
            # Clear recording files from demo/recordings
            recordings_dir = Path("demo/recordings")
            recordings_dir.mkdir(parents=True, exist_ok=True)
            for file in recordings_dir.glob("*"):
                if file.is_file() and file.name != ".gitkeep":
                    file.unlink()
            
            return "All output and recording files cleared.", ""
        except Exception as e:
            error_msg = f"Error clearing files: {str(e)}"
            self.logger.error(error_msg)
            return "", error_msg
    
    def cleanup_and_exit(self) -> bool:
        """Perform cleanup and prepare for exit."""
        try:
            # Hide exit button during cleanup
            yield False
            
            # Perform cleanup
            status, error = self.clear_files()
            if error:
                self.logger.error(f"Error during cleanup: {error}")
            
            # Show exit button again
            yield True
        except Exception as e:
            self.logger.error(f"Exit error: {str(e)}")
            yield True
    
    def build_interface(self) -> gr.Blocks:
        """Build the Gradio interface with enhanced error handling."""
        with gr.Blocks(title="English-Japanese Transcriber") as interface:
            gr.Markdown("# English-Japanese Audio Transcriber")
            
            # Show which cloud service is being used
            provider = "AWS" if hasattr(self.transcriber, "aws_config") else "GOOGLE"
            gr.Markdown(f"Using {provider} services for transcription")
            
            # Status and error display
            with gr.Row():
                self.status_box = gr.Textbox(
                    label="System Status",
                    value="Ready",
                    interactive=False
                )
                self.error_box = gr.Textbox(
                    label="Error Messages",
                    value="",
                    interactive=False,
                    visible=False
                )
            
            # Progress tracking
            self.progress_bar = gr.Progress()
            
            # Input components
            with gr.Row():
                audio_input = gr.Audio(
                    label="Upload Audio or Record",
                    type="filepath",
                    sources=["microphone", "upload"],
                    format="wav"
                )
                
                with gr.Column():
                    format_select = gr.Dropdown(
                        choices=["txt", "json", "srt"],
                        value="txt",
                        label="Output Format"
                    )
            
            # Action buttons
            with gr.Row():
                transcribe_btn = gr.Button("Transcribe")
                clear_btn = gr.Button("Clear")
                clear_files_btn = gr.Button("Clear Output Files", variant="secondary")
            
            # Output display
            output_text = gr.Textbox(
                label="Transcription Output",
                lines=10,
                interactive=False
            )

            # Exit section at the bottom
            gr.Markdown("---")  # Horizontal line for separation
            with gr.Row():
                exit_btn = gr.Button("Exit Application", variant="stop")
            
            # Event handlers
            transcribe_btn.click(
                fn=self.handle_transcription,
                inputs=[audio_input, format_select],
                outputs=[output_text, self.error_box]
            )
            clear_btn.click(
                fn=self.handle_clear,
                inputs=[],
                outputs=[audio_input, output_text, self.error_box]
            )
            clear_files_btn.click(
                fn=self.clear_files,
                inputs=[],
                outputs=[self.status_box, self.error_box]
            )
            exit_btn.click(
                fn=self.cleanup_and_exit,
                inputs=[],
                outputs=[exit_btn],
                show_progress=True
            )
            
            # Update status on component changes
            audio_input.change(
                fn=self.update_status,
                inputs=[audio_input],
                outputs=[self.status_box]
            )
        
        return interface
    
    def update_status(self, audio_path: Optional[str]) -> str:
        """Update the status display based on system state."""
        if not audio_path:
            return "Ready - Waiting for audio input"
        
        try:
            info = self.audio_handler.get_audio_info(audio_path)
            return f"Ready - Audio loaded: {info['duration']:.1f}s, {info['format']}"
        except Exception as e:
            return f"Ready - Invalid audio file: {str(e)}"
    
    async def handle_transcription(
        self,
        audio_input: Optional[str],
        output_format: str = "txt"
    ) -> Tuple[str, str]:
        """
        Handle the transcription process with support for mixed language content.
        
        Args:
            audio_input: Audio input from Gradio (file or recording)
            output_format: Selected output format
            
        Returns:
            Tuple[str, str]: Tuple of (output text, error message)
        """
        processed_files = []
        try:
            if not audio_input:
                raise AudioValidationError("Please provide an audio file or recording")
            
            self.logger.info(f"Starting mixed language transcription with format: {output_format}")
            
            # Process the audio file
            audio_paths = self.audio_handler.process_upload(audio_input)
            processed_files = [audio_paths['transcription'], audio_paths['playback']]
            
            # Try both languages and merge results
            en_transcription = await self.transcriber.transcribe(
                audio_path=audio_paths['transcription'],
                language_code="en-US"
            )
            
            ja_transcription = await self.transcriber.transcribe(
                audio_path=audio_paths['transcription'],
                language_code="ja-JP"
            )
            
            # Debug log the raw transcriptions
            self.logger.debug(f"English transcription: {json.dumps(en_transcription, ensure_ascii=False)}")
            self.logger.debug(f"Japanese transcription: {json.dumps(ja_transcription, ensure_ascii=False)}")
            
            # Process all segments from both transcriptions
            all_segments = []
            
            # Process English segments
            en_segments = en_transcription.get("results", {}).get("segments", [])
            for segment in en_segments:
                if segment.get("confidence", 0) >= 0.3:  # Filter low confidence segments
                    # Clean up English text
                    text = segment.get("text", "").strip()
                    # Remove any trailing Japanese punctuation
                    if text and text[-1] in "。、！？":
                        text = text[:-1].strip()
                    if text:  # Only add if there's actual text
                        segment["text"] = text
                        segment["language"] = "en-US"
                        all_segments.append(segment)
            
            # Process Japanese segments
            ja_segments = ja_transcription.get("results", {}).get("segments", [])
            for segment in ja_segments:
                if segment.get("confidence", 0) >= 0.3:  # Filter low confidence segments
                    # Clean up Japanese text
                    text = segment.get("text", "").strip()
                    # Remove lone punctuation
                    if text in "。、！？":
                        continue
                    # Ensure proper Japanese punctuation
                    if text and text[-1] not in "。、！？":
                        text += "。"
                    if text:  # Only add if there's actual text
                        segment["text"] = text
                        segment["language"] = "ja-JP"
                        all_segments.append(segment)
            
            # Sort segments by start time
            all_segments.sort(key=lambda x: float(x.get("start_time", 0)))
            
            # Merge overlapping segments based on confidence and language
            merged_segments = []
            for segment in all_segments:
                # If we have a previous segment that overlaps
                if merged_segments and self._segments_overlap(merged_segments[-1], segment):
                    prev_segment = merged_segments[-1]
                    # If same language, keep higher confidence
                    if prev_segment["language"] == segment["language"]:
                        if segment.get("confidence", 0) > prev_segment.get("confidence", 0):
                            merged_segments[-1] = segment
                    # If different languages, keep both unless very close in time
                    elif abs(float(segment.get("start_time", 0)) - float(prev_segment.get("end_time", 0))) > 0.1:
                        merged_segments.append(segment)
                else:
                    merged_segments.append(segment)
            
            # Create merged transcription result with proper text handling
            transcript_text = " ".join(s["text"] for s in merged_segments)
            
            merged_transcription = {
                "results": {
                    "transcripts": [{
                        "transcript": transcript_text
                    }],
                    "segments": merged_segments
                }
            }
            
            # Debug log the merged transcription
            self.logger.debug(f"Merged transcription: {json.dumps(merged_transcription, ensure_ascii=False)}")
            
            # Format and save the output
            self.logger.info(f"Formatting mixed language output as {output_format}")
            output = self.output_handler.format_output(
                transcription=merged_transcription,
                format=output_format
            )
            
            self.output_handler.save_output(merged_transcription, format=output_format)
            
            return output, ""
            
        except Exception as e:
            self.logger.error(f"Transcription error with format {output_format}: {str(e)}")
            return "", str(e)
        finally:
            # Clean up processed audio files
            try:
                for file_path in processed_files:
                    if file_path and Path(file_path).exists():
                        Path(file_path).unlink()
            except Exception as cleanup_error:
                self.logger.error(f"Error cleaning up audio files: {cleanup_error}")
    
    def _segments_overlap(self, seg1: Dict[str, Any], seg2: Dict[str, Any]) -> bool:
        """Check if two segments overlap in time."""
        start1 = float(seg1.get("start_time", 0))
        end1 = float(seg1.get("end_time", 0))
        start2 = float(seg2.get("start_time", 0))
        end2 = float(seg2.get("end_time", 0))
        
        # Consider segments overlapping if they share any time period
        return not (end1 < start2 or start1 > end2)
    
    def handle_clear(self) -> Tuple[None, str, None, str]:
        """Clear the interface and reset state."""
        self.current_operation = None
        self.operation_start_time = None
        self.progress(0, "Ready")
        return None, "", None, ""
    
    def progress(self, value: float, desc: str = "") -> None:
        """Update progress bar and status."""
        if self.progress_bar:
            self.progress_bar(value, desc=desc)
        if self.status_box:
            self.status_box.update(value=desc)
            
    def _get_language_code(self, language_option: str) -> str:
        """
        Convert UI language option to AWS language code.
        
        Args:
            language_option (str): Language selected in UI ("auto", "english", "japanese")
            
        Returns:
            str: AWS language code ("en-US" or "ja-JP")
        """
        language_map = {
            "auto": "en-US",  # Default to English if auto
            "english": "en-US",
            "japanese": "ja-JP"
        }
        return language_map[language_option] 
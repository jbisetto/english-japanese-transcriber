"""Web interface for the transcription demo.

This module provides the main web interface using Gradio, with enhanced
error handling and user feedback.
"""

import gradio as gr
import time
from typing import Tuple, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from ..handlers import AudioHandler, OutputHandler
from ..utils.logger import DemoLogger
from ..utils.errors import (
    DemoError, AudioValidationError, AudioProcessingError,
    TranscriptionError, LanguageDetectionError, ServiceUnavailableError,
    OutputFormatError, ResourceError
)
from ..utils.retry_handler import retry

class TranscriptionUI:
    """Main web interface for the transcription demo."""
    
    def __init__(
        self,
        audio_handler: AudioHandler,
        output_handler: OutputHandler,
        logger: Optional[DemoLogger] = None
    ):
        """Initialize the web interface."""
        self.audio_handler = audio_handler
        self.output_handler = output_handler
        self.logger = logger or DemoLogger()
        
        # Track operation state
        self.current_operation: Optional[str] = None
        self.operation_start_time: Optional[datetime] = None
        
        # Initialize interface components
        self.error_box = None
        self.status_box = None
        self.progress_bar = None
    
    def build_interface(self) -> gr.Blocks:
        """Build the Gradio interface with enhanced error handling."""
        with gr.Blocks(title="English-Japanese Transcriber") as interface:
            gr.Markdown("# English-Japanese Audio Transcriber")
            
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
                    type="filepath"
                )
                
                with gr.Column():
                    language_select = gr.Dropdown(
                        choices=["auto-detect", "force-english", "force-japanese"],
                        value="auto-detect",
                        label="Language Mode"
                    )
                    format_select = gr.Dropdown(
                        choices=["txt", "json", "srt"],
                        value="txt",
                        label="Output Format"
                    )
            
            # Output display
            output_text = gr.Textbox(
                label="Transcription Output",
                lines=10,
                interactive=False
            )
            
            # Action buttons
            with gr.Row():
                transcribe_btn = gr.Button("Transcribe")
                clear_btn = gr.Button("Clear")
            
            # Event handlers
            transcribe_btn.click(
                fn=self.handle_transcription,
                inputs=[audio_input, language_select, format_select],
                outputs=[output_text, self.error_box]
            )
            clear_btn.click(
                fn=self.handle_clear,
                inputs=[],
                outputs=[audio_input, output_text, self.error_box]
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
    
    def progress(self, value: float, desc: str = "") -> None:
        """Update progress bar and status."""
        if self.progress_bar:
            self.progress_bar(value, desc=desc)
        if self.status_box:
            self.status_box.update(value=desc)
    
    @retry(max_retries=3)
    def handle_transcription(
        self,
        audio_path: Optional[str],
        language: str,
        output_format: str
    ) -> Tuple[str, str]:
        """
        Handle the transcription process with enhanced error handling.
        
        Args:
            audio_path: Path to the audio file
            language: Selected language mode
            output_format: Selected output format
            
        Returns:
            Tuple[str, str]: (output_text, error_message)
        """
        # Reset error state
        error_msg = ""
        self.operation_start_time = datetime.now()
        self.current_operation = "transcription"
        
        try:
            # Input validation
            if not audio_path:
                raise AudioValidationError("Please provide an audio file or recording")
            
            # Process audio
            self.progress(0.1, "Processing audio...")
            audio_info = self.audio_handler.process_upload(audio_path)
            
            # Language detection
            self.progress(0.3, "Detecting language...")
            if language == "auto-detect":
                try:
                    detected_language = self._detect_language(audio_path)
                    self.logger.info(f"Detected language: {detected_language}")
                except Exception as e:
                    raise LanguageDetectionError(f"Language detection failed: {str(e)}")
            
            # Transcription
            self.progress(0.5, "Transcribing...")
            try:
                transcription = self._simulate_transcription()
            except Exception as e:
                raise TranscriptionError(f"Transcription failed: {str(e)}")
            
            # Format output
            self.progress(0.8, "Formatting output...")
            try:
                output = self.output_handler.format_output(
                    transcription=transcription,
                    format=output_format,
                    language=language
                )
            except Exception as e:
                raise OutputFormatError(f"Output formatting failed: {str(e)}")
            
            # Save output
            self.progress(0.9, "Saving output...")
            self.output_handler.save_output(transcription, format=output_format)
            
            # Complete
            self.progress(1.0, "Complete!")
            self.current_operation = None
            return output, error_msg
            
        except DemoError as e:
            self.logger.error(str(e), exc_info=e)
            self.progress(1.0, "Error occurred")
            return "", e.user_message
            
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}", exc_info=e)
            self.progress(1.0, "Error occurred")
            return "", f"An unexpected error occurred: {str(e)}"
        
        finally:
            if self.error_box:
                self.error_box.update(visible=bool(error_msg))
    
    def handle_clear(self) -> Tuple[None, str, str]:
        """Clear the interface and reset state."""
        self.current_operation = None
        self.operation_start_time = None
        self.progress(0, "Ready")
        return None, "", ""
    
    def _detect_language(self, audio_path: str) -> str:
        """Simulate language detection."""
        time.sleep(1)  # Simulate processing
        return "en"
    
    def _simulate_transcription(self) -> Dict[str, Any]:
        """Simulate transcription for demo purposes."""
        time.sleep(2)  # Simulate processing
        return {
            "text": "Hello, how are you? こんにちは、元気ですか？",
            "segments": [
                {"start": 0, "end": 2, "text": "Hello, how are you?"},
                {"start": 2, "end": 4, "text": "こんにちは、元気ですか？"}
            ]
        } 
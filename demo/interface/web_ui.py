"""Web interface for the transcription demo.

This module provides the main web interface using Gradio, with enhanced
error handling and user feedback.
"""

import gradio as gr
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
        self.audio_handler = audio_handler
        self.output_handler = output_handler
        self.transcriber = transcriber
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
                    source="microphone",
                    format="wav",
                    sample_rate=None  # Let Gradio preserve original sample rate
                )
                
                with gr.Column():
                    language_select = gr.Dropdown(
                        choices=["auto", "english", "japanese"],
                        value="auto",
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
            
            # Playback audio
            output_audio = gr.Audio(
                label="Processed Audio",
                type="filepath",
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
                outputs=[output_text, output_audio, self.error_box]
            )
            clear_btn.click(
                fn=self.handle_clear,
                inputs=[],
                outputs=[audio_input, output_text, output_audio, self.error_box]
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
    
    def handle_transcription(
        self,
        audio_input: Optional[str],
        language_option: str = "auto",
        output_format: str = "txt"
    ) -> Tuple[str, str, str]:
        """
        Handle the transcription process.
        
        Args:
            audio_input: Audio input from Gradio (file or recording)
            language_option (str): Language option for transcription
            output_format: Selected output format
            
        Returns:
            Tuple[str, str, str]: Tuple of (output text, audio file path for playback, error message)
        """
        try:
            if not audio_input:
                raise AudioValidationError("Please provide an audio file or recording")
            
            # Process the audio file
            audio_paths = self.audio_handler.process_upload(audio_input)
            
            # Get transcription using the optimized audio
            transcription = self.transcriber.transcribe(
                audio_paths['transcription'],
                language=language_option if language_option != "auto" else None
            )
            
            # Format and save the output
            output = self.output_handler.format_output(
                transcription=transcription,
                format=output_format,
                language=language_option
            )
            self.output_handler.save_output(transcription, format=output_format)
            
            # Return the formatted output and playback audio path
            return output, audio_paths['playback'], ""
            
        except Exception as e:
            self.logger.error(f"Transcription error: {str(e)}")
            return "", None, str(e)
    
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
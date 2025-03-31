"""Web UI components for the English-Japanese transcription demo.

This module provides the Gradio-based web interface components for audio transcription,
including real-time feedback, progress indicators, and error handling.
"""

from typing import Dict, List, Optional, Tuple, Any
import gradio as gr
import logging
from pathlib import Path
from datetime import datetime

from ..utils.logger import DemoLogger
from ..utils.resource_manager import ResourceManager
from ..handlers.audio_handler import AudioHandler
from ..handlers.output_handler import OutputHandler, OutputFormatError
from ..config import DemoConfig, ServiceDetector

class TranscriptionUI:
    """Main web interface for the transcription demo."""
    
    def __init__(self, config: DemoConfig):
        """Initialize the web interface.
        
        Args:
            config: Configuration for the demo
        """
        self.config = config
        self.logger = DemoLogger()
        self.resource_manager = ResourceManager()
        self.audio_handler = AudioHandler()
        self.output_handler = OutputHandler()
        
        # Initialize interface components
        self.interface = None
        self.progress = gr.Progress()
        self.status = None
        self.error_box = gr.Textbox(
            label="Status",
            visible=False,
            interactive=False
        )
        
    def build_interface(self) -> gr.Blocks:
        """Build the Gradio interface.
        
        Returns:
            gr.Blocks: The constructed Gradio interface
        """
        with gr.Blocks(title="English-Japanese Transcriber") as interface:
            gr.Markdown("# English-Japanese Audio Transcriber")
            
            with gr.Row():
                # Service status indicators
                with gr.Column(scale=1):
                    gr.Markdown("### Service Status")
                    self.status = gr.Label(value=self._get_service_status())
                
                # System health
                with gr.Column(scale=1):
                    gr.Markdown("### System Health")
                    health_info = self.resource_manager.check_system_health()
                    health_status = "✅ Good" if not health_info['needs_cleanup'] else "⚠️ Needs Cleanup"
                    gr.Label(value=health_status)
            
            with gr.Row():
                # Input section
                with gr.Column(scale=2):
                    gr.Markdown("### Audio Input")
                    audio_input = gr.Audio(
                        type="filepath",
                        label="Record or upload audio",
                        sources=["microphone", "upload"]
                    )
                    
                    language_select = gr.Dropdown(
                        choices=self.config.language_options,
                        value="auto-detect",
                        label="Language Detection"
                    )
                    
                    format_select = gr.Dropdown(
                        choices=self.config.supported_formats,
                        value="txt",
                        label="Output Format"
                    )
                
                # Output section
                with gr.Column(scale=2):
                    gr.Markdown("### Transcription Output")
                    output_text = gr.TextArea(
                        label="Transcription",
                        placeholder="Transcription will appear here...",
                        lines=10
                    )
                    self.error_box = gr.Textbox(
                        label="Status",
                        visible=False,
                        interactive=False
                    )
            
            # Action buttons
            with gr.Row():
                transcribe_btn = gr.Button("Transcribe", variant="primary")
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
            
            # Periodic updates
            interface.load(
                fn=self._get_service_status,
                inputs=None,
                outputs=self.status,
                show_progress=False
            )
        
        self.interface = interface
        return interface
    
    def handle_transcription(
        self,
        audio_path: str,
        language: str,
        output_format: str
    ) -> Tuple[str, str]:
        """Handle the transcription process.
        
        Args:
            audio_path: Path to the audio file
            language: Selected language option
            output_format: Desired output format
            
        Returns:
            Tuple[str, str]: (transcription output, error message if any)
        """
        try:
            # Reset error state
            error_msg = ""
            
            # Validate inputs
            if not audio_path:
                error_msg = "Please provide an audio file or recording"
                return "", error_msg
            
            # Process audio
            self.progress(0, desc="Processing audio...")
            audio_info = self.audio_handler.process_upload(audio_path)
            
            # Simulate transcription (to be implemented)
            self.progress(0.5, desc="Transcribing...")
            transcription = self._simulate_transcription()
            
            # Format output
            self.progress(0.8, desc="Formatting output...")
            output = self.output_handler.format_output(
                transcription=transcription,
                format=output_format,
                language=language
            )
            
            # Save output
            self.progress(0.9, desc="Saving output...")
            self.output_handler.save_output(transcription, format=output_format)
            
            self.progress(1.0, desc="Complete!")
            return output, error_msg
            
        except Exception as e:
            self.logger.error(f"Transcription error: {str(e)}")
            return "", f"Error: {str(e)}"
    
    def handle_clear(self) -> Tuple[None, str, str]:
        """Clear the interface.
        
        Returns:
            Tuple[None, str, str]: (None for audio, empty string for output and error)
        """
        return None, "", ""
    
    def _get_service_status(self) -> str:
        """Get the current service status.
        
        Returns:
            str: Status message
        """
        detector = ServiceDetector()
        provider = detector.detect_provider()
        status = detector.get_service_status()
        
        if status.get('status', 'unavailable') == 'available':
            return f"✅ {provider.value} Connected"
        else:
            return f"❌ {provider.value} Unavailable"
    
    def _simulate_transcription(self) -> Dict[str, Any]:
        """Simulate a transcription result for testing.
        
        Returns:
            Dict[str, Any]: Simulated transcription data
        """
        return {
            'text': 'Hello, how are you? こんにちは、お元気ですか？',
            'segments': [
                {
                    'start': 0.0,
                    'end': 2.5,
                    'text': 'Hello, how are you?'
                },
                {
                    'start': 2.5,
                    'end': 5.0,
                    'text': 'こんにちは、お元気ですか？'
                }
            ],
            'language': 'mixed'
        }
    
    def launch(self, **kwargs) -> None:
        """Launch the web interface.
        
        Args:
            **kwargs: Additional arguments to pass to gr.launch()
        """
        if self.interface is None:
            self.build_interface()
        self.interface.launch(**kwargs) 
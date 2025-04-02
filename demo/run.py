"""Run script for the transcription demo."""

from demo.interface.web_ui import TranscriptionUI
from demo.handlers import AudioHandler, OutputHandler
from demo.utils.logger import DemoLogger

from src.config import ConfigFactory, AWSConfig
from src.transcription.service import TranscriptionService

def main():
    """Initialize and run the demo interface."""
    # Initialize components
    logger = DemoLogger()
    audio_handler = AudioHandler()
    output_handler = OutputHandler()
    
    # Initialize AWS configuration
    aws_config = ConfigFactory.get_cloud_config()
    aws_config.validate()
    
    # Initialize transcription service
    transcription_service = TranscriptionService(
        aws_config=aws_config,
        transcription_config=aws_config.bedrock
    )
    
    # Create UI
    ui = TranscriptionUI(
        audio_handler=audio_handler,
        output_handler=output_handler,
        transcriber=transcription_service,
        logger=logger
    )
    
    # Launch interface
    interface = ui.build_interface()
    interface.launch(
        share=True,  # Create public URL
        server_name="0.0.0.0",  # Listen on all interfaces
        server_port=7860  # Default Gradio port
    )

if __name__ == "__main__":
    main() 
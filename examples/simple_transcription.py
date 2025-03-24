from src.agent import TranscriptionAgent

if __name__ == '__main__':
    # Example usage
    agent = TranscriptionAgent()
    # audio_path = "examples/sample_audio/sample.mp3"  # Replace with your audio file
    filename = "simple_transcription"
    # agent.process_and_save_transcript(audio_path, filename, format="txt")

    # Create a dummy transcript for testing
    transcript = [
        {"language": "en", "text": "This is a test transcript."},
        {"language": "ja", "text": "これはテストのトランスクリプトです。"}
    ]
    agent.output_manager.save_transcript(transcript, filename, format="txt")

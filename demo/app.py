"""
English-Japanese Transcription Demo

A Gradio-based demo interface for the English-Japanese transcription system.
This is the main entry point for the demo application.
"""

import os
import gradio as gr
from pathlib import Path

# Ensure the recordings directory exists
RECORDINGS_DIR = Path(__file__).parent / "recordings"
RECORDINGS_DIR.mkdir(exist_ok=True)

if __name__ == "__main__":
    # Main application entry point
    pass 
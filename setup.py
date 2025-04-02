"""Setup configuration for the demo package."""

from setuptools import setup, find_packages

setup(
    name="demo",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "gradio>=4.0.0",
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "pydub>=0.25.1",
        "soundfile>=0.12.1",
        "psutil>=5.9.0",
        "boto3>=1.28.0",
        "pytest>=8.0.0",
    ],
    python_requires=">=3.10",
    author="Your Name",
    description="English-Japanese Audio Transcription Demo",
    keywords="transcription, audio, japanese, english",
)

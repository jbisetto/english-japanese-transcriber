# English-Japanese Transcription Demo

A Gradio-based demo interface for the English-Japanese transcription system. This demo showcases the system's capabilities in a user-friendly web interface.

## Features

- Audio input via file upload or microphone recording
- Support for multiple audio formats (mp3, wav, m4a, flac)
- Language detection and forced language selection
- Multiple segmentation strategies
- Multiple output formats (TXT, JSON, SRT)
- Real-time service status indication
- Debug information and logging
- Resource management and cleanup

## Requirements

- Python 3.8+
- AWS or Google Cloud credentials configured
- Required Python packages (see requirements.txt)

## Installation

1. Install dependencies:
```bash
cd demo
pip install -r requirements.txt
```

2. Ensure your environment variables are properly configured in the root `.env` file:
```env
# Cloud Provider Selection
CLOUD_PROVIDER=aws  # or google

# AWS Configuration (if using AWS)
AWS_REGION_NAME=your_region
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET=your_bucket

# Google Cloud Configuration (if using Google Cloud)
GOOGLE_PROJECT_ID=your_project_id
GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json
```

## Usage

1. Start the demo:
```bash
python app.py
```

2. Open your web browser to the URL shown in the console (typically http://127.0.0.1:7860)

3. Use the interface to:
   - Upload audio files or record from microphone
   - Select language preferences
   - Choose segmentation method
   - Select output format
   - View and download transcription results

## Notes

- The demo is optimized for short audio clips (ideal for JLPT N5 level content)
- Recorded audio files are automatically cleaned up
- Debug information can be accessed through the interface
- The service status indicator shows which cloud provider is being used

## Troubleshooting

1. If microphone recording is unavailable:
   - Check your browser's microphone permissions
   - Verify your system's audio input settings
   - The interface will automatically adjust to show only file upload option

2. If transcription fails:
   - Check your cloud service credentials
   - Verify your internet connection
   - Check the debug output for detailed error information

## Contributing

Please read the main project's contributing guidelines.

## License

See the main project's license file. 
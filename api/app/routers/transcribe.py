import os
import shutil
import sys
import traceback
import asyncio
from typing import List, Dict
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from datetime import datetime
import logging
from pathlib import Path
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from src.config import ConfigFactory
from src.audio.handler import AudioHandler
from src.transcription.service import TranscriptionService

router = APIRouter()

# Ensure upload directory exists
UPLOAD_DIR = "api/uploads"
RESULTS_DIR = "api/results"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

@router.post("/api/transcribe", status_code=status.HTTP_200_OK)
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Endpoint to upload and transcribe an audio file
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="No file provided"
        )
    
    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ['.mp3', '.wav', '.m4a', '.mp4', '.ogg']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Unsupported file format. Supported formats: mp3, wav, m4a, mp4, ogg"
        )
    
    # Generate unique filename with timestamp to avoid conflicts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File saved to {file_path}")
        
        # Initialize AWS configuration
        try:
            # Ensure AWS_REGION is set
            current_region = os.environ.get('AWS_REGION')
            if not current_region or current_region.strip() == '':
                logger.warning("AWS_REGION not set in environment, defaulting to us-east-1")
                os.environ['AWS_REGION'] = 'us-east-1'
                
            # Create AWS config
            aws_config = ConfigFactory.get_cloud_config()
            
            # Override the region if it's still empty
            if not aws_config.region_name or aws_config.region_name.strip() == '':
                logger.warning("Region name is empty in config, manually setting to us-east-1")
                aws_config.region_name = 'us-east-1'
                
            aws_config.validate()
            logger.info(f"AWS config initialized successfully with region: {aws_config.region_name}")
        except Exception as e:
            logger.error(f"Error initializing AWS config: {str(e)}")
            raise
        
        try:
            # Initialize components directly like the Gradio demo does
            audio_handler = AudioHandler(
                target_sample_rate=16000,  # Default sample rate
                target_channels=1  # Default to mono
            )
            
            # Initialize transcription service with bedrock config
            # This is the pattern used in the Gradio demo
            transcription_service = TranscriptionService(
                aws_config=aws_config,
                transcription_config=aws_config.bedrock  # Using bedrock config
            )
            logger.info("TranscriptionService initialized successfully")
            
            # Process the audio file
            logger.info(f"Processing audio file: {file_path}")
            audio_segment = audio_handler.process_audio(file_path)
            logger.info("Audio processed successfully")
            
            # Prepare output path for transcription result
            output_filename = f"{os.path.splitext(unique_filename)[0]}.json"
            output_path = os.path.join(RESULTS_DIR, output_filename)
            
            # Set language code - for proper mixed language detection, 
            # normally this would be determined by a language detector
            # For demonstration, we'll just try "en-US" since we have a simplified MVP
            language_code = "en-US"
            
            # Transcribe the audio - directly await the coroutine
            logger.info("Starting transcription with language code: " + language_code)
            
            transcription_result = await transcription_service.transcribe_streaming(
                audio_segment=audio_segment,
                language_code=language_code,
                output_path=output_path
            )
            logger.info(f"Transcription completed. Result has {len(transcription_result.get('results', {}).get('segments', []))} segments")
            
            # Extract transcript text
            transcripts = []
            if transcription_result and "results" in transcription_result:
                if "segments" in transcription_result["results"]:
                    for segment in transcription_result["results"]["segments"]:
                        # Detect language from segment (in a real implementation, this would 
                        # come from a proper language detector)
                        # For demo purposes, default to English
                        language = "en"
                        
                        # Post-process text if there's content
                        text = segment.get("text", "")
                        if text:
                            processed_text = transcription_service.post_process_text(text, language)
                            
                            # Add to transcripts
                            transcripts.append({
                                "language": language,
                                "text": processed_text or text
                            })
            
            # If no transcripts were generated, add an empty one
            if not transcripts:
                transcripts.append({
                    "language": "en", 
                    "text": "No transcription available"
                })
            
            # Return the actual transcription result
            return {
                "status": "success",
                "filename": unique_filename,
                "transcript": transcripts
            }
            
        except Exception as e:
            logger.error(f"Error in transcription process: {str(e)}")
            logger.error(traceback.format_exc())
            
            # For MVP, return a placeholder response if transcription fails
            return {
                "status": "partial_success",
                "message": "File uploaded but transcription failed. Using placeholder response.",
                "filename": unique_filename,
                "error": str(e),
                "transcript": [
                    {
                        "language": "en",
                        "text": "Placeholder text. Actual transcription failed due to an error."
                    }
                ]
            }
    
    except Exception as e:
        # Log the full error
        logger.error(f"Error processing file: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Make sure to clean up temporary files even if an error occurs
        if os.path.exists(file_path):
            os.remove(file_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        ) 
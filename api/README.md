# English-Japanese Transcriber API

A simple REST API for the English-Japanese Transcriber service.

## Endpoints

### Health Check

**GET /api/health**

Check if the API is running properly.

**Response:**
```json
{
  "status": "ok"
}
```

### Transcribe Audio

**POST /api/transcribe**

Upload an audio file for transcription.

**Parameters:**
- `file` (form-data): The audio file to transcribe (mp3, wav, m4a, mp4, ogg)

**Response:**
```json
{
  "status": "success",
  "message": "File uploaded successfully",
  "filename": "TIMESTAMP_filename.mp3",
  "file_path": "api/uploads/TIMESTAMP_filename.mp3",
  "transcript": [
    {
      "language": "en",
      "text": "Transcription text"
    }
  ]
}
```

## Error Responses

**400 Bad Request:**
```json
{
  "detail": "No file provided"
}
```

or

```json
{
  "detail": "Unsupported file format. Supported formats: mp3, wav, m4a, mp4, ogg"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Error processing file: ERROR_MESSAGE"
}
```

## Running Locally

```bash
# Run directly with Python
cd api
python run.py

# Run with Docker
docker compose up
``` 
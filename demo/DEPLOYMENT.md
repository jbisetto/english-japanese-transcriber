# Deployment Guide

This guide explains how to deploy the English-Japanese Transcription Demo in different environments.

## Local Deployment

### Prerequisites

- Python 3.8+
- pip package manager
- AWS or Google Cloud credentials
- Sufficient disk space for audio files
- Microphone access (for recording feature)

### Steps

1. Clone the repository:
```bash
git clone <repository-url>
cd english-japanese-transcriber/demo
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables in `.env`:
```env
CLOUD_PROVIDER=aws  # or google
# Add other required variables as specified in README.md
```

5. Run the application:
```bash
python app.py
```

## Docker Deployment

### Prerequisites

- Docker installed
- Docker Compose (optional)
- AWS or Google Cloud credentials

### Using Docker

1. Build the image:
```bash
docker build -t transcription-demo .
```

2. Run the container:
```bash
docker run -p 7860:7860 \
  -e CLOUD_PROVIDER=aws \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  -e AWS_REGION=us-east-1 \
  transcription-demo
```

### Using Docker Compose

1. Create `docker-compose.yml`:
```yaml
version: '3'
services:
  demo:
    build: .
    ports:
      - "7860:7860"
    env_file:
      - .env
    volumes:
      - ./recordings:/app/recordings
      - ./output:/app/output
```

2. Start the service:
```bash
docker-compose up -d
```

## Cloud Deployment

### Google Cloud Run

1. Build and push the container:
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/transcription-demo
```

2. Deploy to Cloud Run:
```bash
gcloud run deploy transcription-demo \
  --image gcr.io/PROJECT_ID/transcription-demo \
  --platform managed \
  --allow-unauthenticated
```

### AWS Elastic Beanstalk

1. Create an Elastic Beanstalk application:
```bash
eb init -p python-3.8 transcription-demo
```

2. Configure environment variables in `.ebextensions/environment.config`

3. Deploy:
```bash
eb create transcription-demo-env
```

### Heroku

1. Create a new Heroku app:
```bash
heroku create transcription-demo
```

2. Set environment variables:
```bash
heroku config:set CLOUD_PROVIDER=aws
heroku config:set AWS_ACCESS_KEY_ID=your_key
heroku config:set AWS_SECRET_ACCESS_KEY=your_secret
heroku config:set AWS_REGION=us-east-1
```

3. Deploy:
```bash
git push heroku main
```

## Security Considerations

1. **Environment Variables**
   - Never commit `.env` files
   - Use secure secret management in production
   - Rotate credentials regularly

2. **File Storage**
   - Configure proper file permissions
   - Implement file size limits
   - Set up regular cleanup

3. **Network Security**
   - Use HTTPS in production
   - Configure CORS appropriately
   - Implement rate limiting

4. **Resource Management**
   - Set memory limits
   - Configure disk quotas
   - Monitor resource usage

## Monitoring

1. **Application Logs**
   - Configure log aggregation
   - Set up error alerting
   - Monitor performance metrics

2. **System Health**
   - Monitor disk usage
   - Track memory consumption
   - Watch CPU utilization

3. **Usage Metrics**
   - Track transcription requests
   - Monitor success rates
   - Log error frequencies

## Troubleshooting

### Common Deployment Issues

1. **Port Conflicts**
   - Check if port 7860 is available
   - Configure alternative port if needed
   - Update firewall rules

2. **Memory Issues**
   - Increase container memory limits
   - Monitor memory leaks
   - Configure swap space

3. **Storage Problems**
   - Verify disk space
   - Check file permissions
   - Configure volume mounts

4. **Cloud Credentials**
   - Verify credential validity
   - Check permission scopes
   - Update expired credentials

## Maintenance

1. **Updates**
   - Keep dependencies updated
   - Apply security patches
   - Update cloud SDK versions

2. **Backup**
   - Configure regular backups
   - Test restore procedures
   - Document recovery steps

3. **Cleanup**
   - Schedule regular cleanup
   - Archive old recordings
   - Remove temporary files 
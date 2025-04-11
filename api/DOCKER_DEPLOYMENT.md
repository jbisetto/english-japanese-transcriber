# Docker Deployment

This document outlines how to deploy the English-Japanese Transcriber API using Docker.

## Prerequisites

- Docker installed on your machine
- Docker Compose installed on your machine

## Local Development Deployment

1. **Clone the repository:**

```bash
git clone https://github.com/yourusername/english-japanese-transcriber.git
cd english-japanese-transcriber
```

2. **Create environment file:**

Create a `.env` file in the project root with your AWS credentials:

```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=your_region
AWS_S3_BUCKET=your_bucket
```

3. **Build and start the Docker container:**

```bash
docker compose build
docker compose up
```

The API will be available at `http://localhost:8000`.

To run in the background:

```bash
docker compose up -d
```

4. **Stop the container:**

```bash
docker compose down
```

## Production Deployment Considerations

For production deployments, consider:

1. **Security:**
   - Use proper authentication mechanisms
   - Use HTTPS for API communication
   - Restrict network access as appropriate

2. **Environment Configuration:**
   - Use environment-specific configurations
   - Store secrets securely using environment variables or a secrets manager

3. **Resource Allocation:**
   - Adjust container resources based on expected load
   - Monitor container resource usage

4. **Container Orchestration:**
   - Consider using Kubernetes or other orchestration for larger deployments
   - Set up proper health checks and auto-scaling

5. **Logging and Monitoring:**
   - Set up proper logging mechanisms
   - Implement monitoring for the API service

## Troubleshooting

- If the container fails to start, check the logs:
  ```bash
  docker compose logs
  ```

- If you can't connect to the API, make sure the port is properly exposed and not blocked by a firewall.

- For build errors related to dependencies, make sure the Dockerfile has the necessary system packages installed. 
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies including C++ compiler and ffmpeg
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p api/uploads api/results

# Expose port
EXPOSE 8000

# Start application
CMD ["python", "api/run.py"] 
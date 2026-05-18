FROM python:3.11-slim

# Install system dependencies for C++ compilation and audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libsndfile1 \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend codebase
COPY . .

# Create models, data, and uploads directories if they don't exist
RUN mkdir -p models data uploads

# Expose port (Hugging Face Spaces requirement)
EXPOSE 7860

# Start backend
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]

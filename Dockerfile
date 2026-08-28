# Issue Whisperer — Production Dockerfile for Backend Deployment

FROM python:3.11-slim

WORKDIR /app

# Install build dependencies for FAISS / C-extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all code and data assets
COPY . .

# Set default production environment variables
ENV ENVIRONMENT=production
ENV EMBEDDING_DEVICE=cpu
ENV LOG_LEVEL=INFO
ENV PORT=8000

EXPOSE 8000

# Start FastAPI backend
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

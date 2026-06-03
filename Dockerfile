# Dockerfile for Store Intelligence Platform
# Multi-stage build for optimized image size

# Stage 1: Base image with system dependencies
FROM python:3.10-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required for OpenCV and other libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    # OpenCV dependencies
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    # Additional utilities
    wget \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash appuser

# Set working directory
WORKDIR /app

# Stage 2: Dependencies installation
FROM base as dependencies

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Application
FROM dependencies as application

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p /app/data /app/models /app/config /app/logs && \
    chown -R appuser:appuser /app/data /app/models /app/config /app/logs

# Make scripts executable
RUN chmod +x /app/init_db.py /app/docker-entrypoint.sh

# Download YOLOv8 model if not present (optional - can be done via volume mount)
# Uncomment the following lines to download model during build
# RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')" && \
#     mv yolov8n.pt /app/models/

# Switch to non-root user
USER appuser

# Set entrypoint to run initialization script
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command: Start API server
CMD ["python", "-m", "uvicorn", "src.api_server:app", "--host", "0.0.0.0", "--port", "8000"]

# Alternative commands (can be overridden in docker-compose or docker run):
# Video processing: CMD ["store-intelligence-process", "--video", "/videos/input.mp4"]
# API server with workers: CMD ["store-intelligence-api", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

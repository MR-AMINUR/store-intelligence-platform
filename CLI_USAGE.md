# CLI Usage Guide

This document provides instructions for using the Store Intelligence Platform command-line interfaces.

## Overview

The Store Intelligence Platform provides two CLI entry points:

1. **`store-intelligence-process`** - Process video files through the detection/tracking/event pipeline
2. **`store-intelligence-api`** - Start the FastAPI REST API server

## Installation

Install the package to make CLI commands available:

```bash
pip install -e .
```

Alternatively, you can run the CLI commands directly using Python:

```bash
# Video processing
python -c "import sys; sys.argv = ['store-intelligence-process', ...]; from src.cli import process_video; process_video()"

# API server
python -c "import sys; sys.argv = ['store-intelligence-api', ...]; from src.cli import start_api_server; start_api_server()"
```

## Video Processing CLI

### Command: `store-intelligence-process`

Process video files through the Store Intelligence Platform pipeline.

### Usage

```bash
store-intelligence-process --video <path> [options]
```

### Arguments

- `--video PATH` (required): Path to video file to process (MP4, AVI, MOV)
- `--config PATH` (optional): Path to configuration file (uses environment variables if not specified)
- `--log-level LEVEL` (optional): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: INFO

### Examples

```bash
# Process a video file with default configuration
store-intelligence-process --video store_footage.mp4

# Process with custom configuration file
store-intelligence-process --video store_footage.mp4 --config .env.production

# Enable debug logging
store-intelligence-process --video store_footage.mp4 --log-level DEBUG
```

### Output

The CLI will display a summary of the processing results:

```
======================================================================
VIDEO PROCESSING SUMMARY
======================================================================
Video File:       store_footage.mp4
Status:           ✓ SUCCESS
Total Frames:     1500
Failed Frames:    2
Events Generated: 150
Events Stored:    148
======================================================================
```

### Exit Codes

- `0`: Success
- `1`: Error (file not found, pipeline failure, etc.)
- `130`: Interrupted by user (CTRL+C)

## API Server CLI

### Command: `store-intelligence-api`

Start the Store Intelligence Platform REST API server.

### Usage

```bash
store-intelligence-api [options]
```

### Arguments

- `--config PATH` (optional): Path to configuration file (uses environment variables if not specified)
- `--host HOST` (optional): Server host address (default: from config or 0.0.0.0)
- `--port PORT` (optional): Server port (default: from config or 8000)
- `--log-level LEVEL` (optional): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: INFO
- `--reload` (optional): Enable auto-reload for development (not for production)
- `--workers N` (optional): Number of worker processes (default: 1)

### Examples

```bash
# Start API server with default settings (0.0.0.0:8000)
store-intelligence-api

# Start with custom host and port
store-intelligence-api --host 127.0.0.1 --port 5000

# Start with custom configuration file
store-intelligence-api --config .env.production

# Enable auto-reload for development
store-intelligence-api --reload

# Start with multiple workers (production)
store-intelligence-api --workers 4
```

### Output

The CLI will display server information:

```
======================================================================
STORE INTELLIGENCE PLATFORM API SERVER
======================================================================
Host:        0.0.0.0
Port:        8000
Log Level:   INFO
Reload:      Disabled
Workers:     1
Database:    data/events.db
======================================================================

API Documentation: http://localhost:8000/docs
Health Check:      http://localhost:8000/health

Press CTRL+C to stop the server
```

### Exit Codes

- `0`: Success (server shut down gracefully)
- `1`: Error (configuration error, server startup failure, etc.)

## Configuration

Both CLI commands support loading configuration from a file using the `--config` option. The configuration file should be in `.env` format:

```env
# Database
DB_PATH=data/events.db

# API Server
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO

# Detection
YOLO_MODEL_PATH=models/yolov8n.pt
CONFIDENCE_THRESHOLD=0.5

# Tracking
TRACKER_MAX_AGE=30

# Zones
ZONE_CONFIG_PATH=config/zones.json
```

If `--config` is not specified, the CLI will use environment variables.

## Help

View help for any CLI command:

```bash
store-intelligence-process --help
store-intelligence-api --help
```

## Requirements

See requirements.txt for all dependencies. Key requirements:

- Python >= 3.10
- FastAPI
- Uvicorn
- OpenCV
- Ultralytics (YOLOv8)
- SQLAlchemy
- python-dotenv

## Troubleshooting

### Video file not found

Ensure the video file path is correct and the file exists:

```bash
ls -la path/to/video.mp4
```

### Unsupported video format

Only MP4, AVI, and MOV formats are supported. Convert your video if needed:

```bash
ffmpeg -i input.mkv -c copy output.mp4
```

### Configuration file not found

Ensure the config file path is correct:

```bash
ls -la .env.production
```

### Port already in use

If the API server fails to start with "address already in use" error, try a different port:

```bash
store-intelligence-api --port 8001
```

### Database connection error

Ensure the database directory exists:

```bash
mkdir -p data
```

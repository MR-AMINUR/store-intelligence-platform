# Docker Quick Start Guide

Get the Store Intelligence Platform running in Docker in under 5 minutes.

## Prerequisites

```bash
# Verify Docker is installed
docker --version  # Should be 20.10+
docker-compose --version  # Should be 1.29+
```

## Step 1: Prepare Required Files

### Create Directories

```bash
mkdir -p data models config videos logs
```

### Download YOLOv8 Model

```bash
# Download the nano model (smallest, fastest)
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -P ./models
```

### Create Zone Configuration

Create `config/zones.json`:

```json
{
  "zones": [
    {
      "zone_id": "entrance",
      "zone_name": "Store Entrance",
      "zone_type": "GENERAL",
      "polygon": [
        {"x": 100, "y": 100},
        {"x": 300, "y": 100},
        {"x": 300, "y": 300},
        {"x": 100, "y": 300}
      ]
    },
    {
      "zone_id": "checkout",
      "zone_name": "Checkout Counter",
      "zone_type": "BILLING_QUEUE",
      "polygon": [
        {"x": 500, "y": 100},
        {"x": 800, "y": 100},
        {"x": 800, "y": 300},
        {"x": 500, "y": 300}
      ]
    }
  ]
}
```

## Step 2: Build and Start

```bash
# Build the Docker image
docker-compose build

# Start the services
docker-compose up -d

# Check the logs
docker-compose logs -f api
```

## Step 3: Verify Deployment

```bash
# Check health endpoint
curl http://localhost:8000/health

# Expected output:
# {
#   "status": "healthy",
#   "checks": {"database": "ok", "response_time_ms": 5},
#   "timestamp": "2024-01-15T10:30:00Z"
# }
```

## Step 4: Test the API

### Ingest a Test Event

```bash
curl -X POST http://localhost:8000/events/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "test-001",
    "event_type": "ENTRY",
    "timestamp": "2024-01-15T10:00:00Z",
    "store_id": "store_001",
    "track_id": 1,
    "metadata": {}
  }'
```

### Get Store Metrics

```bash
curl http://localhost:8000/stores/store_001/metrics
```

## Common Commands

```bash
# View logs
docker-compose logs -f api

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Execute command in container
docker-compose exec api bash

# Check database
docker-compose exec api sqlite3 /app/data/events.db "SELECT COUNT(*) FROM events;"
```

## Environment Configuration

Create `.env` file for custom configuration:

```bash
# API Configuration
API_PORT=8080

# Logging
LOG_LEVEL=DEBUG

# Detection
CONFIDENCE_THRESHOLD=0.6

# Store
STORE_ID=my_store_001
```

Then restart:

```bash
docker-compose down
docker-compose up -d
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs api

# Verify files exist
ls -la models/yolov8n.pt
ls -la config/zones.json
```

### Port Already in Use

```bash
# Change port in .env file
echo "API_PORT=8080" > .env
docker-compose up -d
```

### Model Not Found

```bash
# Download model inside container
docker-compose exec api python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
docker-compose exec api mv yolov8n.pt /app/models/
docker-compose restart
```

## What Gets Created

### Directory Structure After Setup

```
.
├── data/               # Persistent database storage
│   └── events.db       # SQLite database (created automatically)
├── models/             # YOLOv8 model files
│   └── yolov8n.pt      # Person detection model
├── config/             # Configuration files
│   └── zones.json      # Zone definitions
├── videos/             # Input video files (optional)
├── logs/               # Application logs
├── Dockerfile          # Docker image definition
├── docker-compose.yml  # Service orchestration
└── docker-entrypoint.sh # Initialization script
```

### Database Schema

The database is automatically initialized with:
- `events` table with indexes on store_id, track_id, event_type, timestamp
- WAL mode enabled for concurrent reads

## Next Steps

1. **Process a video**: Place a video file in `./videos/` and run:
   ```bash
   docker-compose run --rm api store-intelligence-process --video /app/videos/your_video.mp4
   ```

2. **View full documentation**: See `DOCKER_DEPLOYMENT.md` for complete deployment guide

3. **API documentation**: Visit the `/docs` endpoint:
   ```bash
   open http://localhost:8000/docs
   ```

## Getting Help

- **View logs**: `docker-compose logs -f api`
- **Check health**: `curl http://localhost:8000/health`
- **Interactive API docs**: `http://localhost:8000/docs`
- **Full deployment guide**: See `DOCKER_DEPLOYMENT.md`

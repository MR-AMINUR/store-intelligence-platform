# Docker Deployment Guide

This guide explains how to deploy the Store Intelligence Platform using Docker and Docker Compose.

## Overview

The Docker deployment includes:
- **Dockerfile**: Multi-stage build for optimized image size
- **docker-compose.yml**: Orchestration of services with proper volume mounts
- **docker-entrypoint.sh**: Initialization script that runs on container start
- **init_db.py**: Database schema initialization script

## Prerequisites

- Docker 20.10+ installed
- Docker Compose 1.29+ installed
- At least 2GB of available disk space
- (Optional) NVIDIA Docker runtime for GPU support

## Quick Start

### 1. Build the Docker Image

```bash
docker-compose build
```

This will create a Docker image named `store-intelligence-platform:latest`.

### 2. Start the Services

```bash
docker-compose up -d
```

This starts the API server in detached mode.

### 3. Check Service Health

```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs -f api

# Check API health endpoint
curl http://localhost:8000/health
```

### 4. Stop the Services

```bash
docker-compose down
```

## Architecture

### Dockerfile

The Dockerfile uses a multi-stage build approach:

1. **Base Stage**: Sets up Python 3.10-slim with system dependencies (OpenCV, etc.)
2. **Dependencies Stage**: Installs Python packages from requirements.txt
3. **Application Stage**: Copies application code and configures runtime

Key features:
- Non-root user (`appuser`) for security
- WAL-enabled SQLite for concurrent reads
- Health check endpoint integration
- Multi-architecture support (amd64, arm64)

### docker-compose.yml

Defines the following services:

#### API Service
- **Container Name**: `store-intelligence-api`
- **Port Mapping**: `8000:8000` (configurable via `API_PORT` env var)
- **Restart Policy**: `unless-stopped`
- **Health Check**: Polls `/health` endpoint every 30 seconds

#### Volume Mounts

| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `./data` | `/app/data` | SQLite database persistence |
| `./videos` | `/app/videos` | Input video files |
| `./models` | `/app/models` | YOLOv8 model files |
| `./config` | `/app/config` | Zone configuration (zones.json) |
| `./logs` | `/app/logs` | Application logs |

### Entrypoint Script

The `docker-entrypoint.sh` script runs on container start:

1. **Database Initialization**: Runs `init_db.py` to create schema
2. **Health Check**: Verifies database connectivity
3. **Service Start**: Executes the main command (API server)

This ensures the database is always initialized before the API server starts.

## Configuration

### Environment Variables

All configuration is done via environment variables. You can:

1. **Set in docker-compose.yml** (for default values)
2. **Create .env file** (for local overrides)
3. **Pass at runtime** (using `-e` flag with `docker run`)

#### Database Configuration

```bash
DB_PATH=/app/data/events.db          # SQLite database file path
```

#### API Server Configuration

```bash
API_HOST=0.0.0.0                     # API bind address
API_PORT=8000                        # API port (also update port mapping)
WORKERS=1                            # Number of uvicorn workers
```

#### Logging Configuration

```bash
LOG_LEVEL=INFO                       # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
```

#### Model Configuration

```bash
YOLO_MODEL_PATH=/app/models/yolov8n.pt   # Path to YOLOv8 model
CONFIDENCE_THRESHOLD=0.5                  # Detection confidence threshold
```

#### Tracker Configuration

```bash
TRACKER_MAX_AGE=30                   # Max frames to keep lost tracks
```

#### Zone Configuration

```bash
ZONE_CONFIG_PATH=/app/config/zones.json   # Zone definitions file
STORE_ID=store_001                        # Default store identifier
```

### Example .env File

Create a `.env` file in the project root:

```bash
# API Configuration
API_PORT=8080
WORKERS=4

# Logging
LOG_LEVEL=DEBUG

# Detection
CONFIDENCE_THRESHOLD=0.6

# Store
STORE_ID=my_store_001
```

## Volume Management

### Persistent Data

The SQLite database is stored in the `./data` volume mount:

```bash
# Backup database
docker-compose exec api cp /app/data/events.db /app/data/events.db.backup

# Restore database
docker-compose exec api cp /app/data/events.db.backup /app/data/events.db
```

### Model Files

Place YOLOv8 model files in the `./models` directory:

```bash
# Download YOLOv8 nano model (smallest)
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -P ./models

# Or download larger models for better accuracy
# YOLOv8 small:  yolov8s.pt
# YOLOv8 medium: yolov8m.pt
# YOLOv8 large:  yolov8l.pt
```

### Video Files

Place video files for processing in the `./videos` directory:

```bash
cp /path/to/store_footage.mp4 ./videos/
```

### Configuration Files

Create zone configuration in `./config/zones.json`:

```json
{
  "zones": [
    {
      "zone_id": "cosmetics",
      "zone_name": "Cosmetics Section",
      "zone_type": "GENERAL",
      "polygon": [
        {"x": 100, "y": 100},
        {"x": 400, "y": 100},
        {"x": 400, "y": 400},
        {"x": 100, "y": 400}
      ]
    },
    {
      "zone_id": "checkout",
      "zone_name": "Checkout Area",
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

## Database Initialization

The database schema is automatically initialized when the container starts via the `docker-entrypoint.sh` script.

### Manual Initialization

You can also manually initialize the database:

```bash
# Inside the container
docker-compose exec api python /app/init_db.py

# From host (if database is mounted)
python init_db.py --db-path ./data/events.db
```

### Schema Details

The initialization creates:
- **events table**: Primary storage for all events
- **Indexes**: On store_id, track_id, event_type, timestamp
- **WAL mode**: Enabled for concurrent reads

## Running Video Processing

The default container runs the API server. To process videos:

### Option 1: One-off Container

```bash
docker-compose run --rm api store-intelligence-process --video /app/videos/sample.mp4
```

### Option 2: Separate Processor Service

Uncomment the `video-processor` service in `docker-compose.yml` and modify the command:

```yaml
video-processor:
  ...
  command: ["store-intelligence-process", "--video", "/app/videos/sample.mp4"]
```

Then start it:

```bash
docker-compose up video-processor
```

## Monitoring and Debugging

### View Logs

```bash
# All logs
docker-compose logs -f

# API logs only
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api
```

### Execute Commands Inside Container

```bash
# Open shell
docker-compose exec api bash

# Run Python commands
docker-compose exec api python -c "from src.config import ConfigManager; print(ConfigManager().get('DB_PATH'))"

# Check database
docker-compose exec api sqlite3 /app/data/events.db "SELECT COUNT(*) FROM events;"
```

### Health Monitoring

```bash
# Check health endpoint
curl http://localhost:8000/health

# Detailed health check
docker-compose exec api curl http://localhost:8000/health | jq
```

## Performance Tuning

### Multi-Worker Configuration

For production deployments, increase the number of workers:

```yaml
environment:
  - WORKERS=4  # Adjust based on CPU cores
```

**Rule of thumb**: `(2 × CPU_cores) + 1`

### Database Optimization

SQLite is optimized with:
- **WAL mode**: Concurrent reads during writes
- **Indexes**: On frequently queried columns
- **Connection pooling**: Automatic retry with exponential backoff

For high-throughput scenarios, consider migrating to PostgreSQL.

### Memory Configuration

For GPU inference (if NVIDIA Docker runtime is available):

```yaml
services:
  api:
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=0  # Use first GPU
```

## Troubleshooting

### Container Won't Start

1. Check logs: `docker-compose logs api`
2. Verify volume permissions: `ls -la ./data ./models ./config`
3. Ensure model file exists: `ls -la ./models/yolov8n.pt`

### Database Locked Errors

- SQLite WAL mode handles most concurrent access
- If issues persist, reduce worker count or migrate to PostgreSQL

### Model Not Found

```bash
# Download YOLOv8 model
docker-compose exec api python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
docker-compose exec api mv yolov8n.pt /app/models/
```

### API Not Accessible

1. Check port mapping in docker-compose.yml
2. Verify firewall rules: `sudo ufw status`
3. Check if port is already in use: `netstat -tulpn | grep 8000`

## Production Deployment

### Security Considerations

1. **Use secrets management** for sensitive configuration (not environment variables)
2. **Enable HTTPS** with reverse proxy (nginx, Traefik)
3. **Implement authentication** for API endpoints
4. **Regular backups** of database volume
5. **Update base image** regularly for security patches

### Example Production Setup with Nginx

```yaml
# docker-compose.prod.yml
services:
  api:
    restart: always
    environment:
      - LOG_LEVEL=WARNING
      - WORKERS=4
    networks:
      - internal

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
    networks:
      - internal

networks:
  internal:
    driver: bridge
```

## Cleanup

### Remove Containers and Networks

```bash
docker-compose down
```

### Remove Volumes (WARNING: Deletes data)

```bash
docker-compose down -v
```

### Remove Images

```bash
docker rmi store-intelligence-platform:latest
```

## Support

For issues or questions:
- Check logs: `docker-compose logs`
- Review configuration: `docker-compose config`
- Verify health: `curl http://localhost:8000/health`

## References

- [Dockerfile Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [SQLite WAL Mode](https://www.sqlite.org/wal.html)
- [Uvicorn Deployment](https://www.uvicorn.org/deployment/)

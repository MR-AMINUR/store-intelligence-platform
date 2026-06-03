# Store Intelligence Platform

![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen)
![Tests](https://img.shields.io/badge/tests-342%20passed-success)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A production-ready computer vision-based retail analytics platform that processes CCTV footage to extract actionable insights about customer behavior using AI-powered person detection and tracking.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
  - [Local Installation](#local-installation)
  - [Docker Deployment](#docker-deployment)
- [Usage](#usage)
  - [CLI Commands](#cli-commands)
  - [API Endpoints](#api-endpoints)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Development](#development)
- [Testing](#testing)
- [API Documentation](#api-documentation)
- [Performance](#performance)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

The Store Intelligence Platform is an end-to-end computer vision system that analyzes CCTV footage from retail stores to:

- **Detect and track customers** using YOLOv8 (person detection) and ByteTrack (multi-object tracking)
- **Generate structured events** capturing customer journey milestones (entry, exit, zone interactions, billing queue activities, reentry)
- **Store events persistently** in SQLite database with idempotency guarantees
- **Provide REST API analytics** including store metrics, conversion funnels, spatial heatmaps, and anomaly detection
- **Support real-time and batch processing** of video streams

### Key Use Cases

- **Store Traffic Analysis**: Monitor foot traffic patterns and peak hours
- **Zone Effectiveness**: Measure customer engagement with different store sections
- **Queue Management**: Optimize checkout staffing based on queue wait times
- **Conversion Funnels**: Analyze drop-off points in the customer journey
- **Anomaly Detection**: Identify unusual patterns (crowd surges, high abandonment rates)

---

## ✨ Features

### Computer Vision
- ✅ **YOLOv8 Person Detection** with configurable confidence thresholds
- ✅ **ByteTrack Multi-Object Tracking** for consistent identity across frames
- ✅ **GPU/CPU Auto-Detection** with automatic fallback
- ✅ **Handles Occlusions** (up to 30 frames without detection)
- ✅ **Frame Decode Error Recovery** for robust video processing

### Event Generation
- ✅ **Entry/Exit Detection** with automatic pairing
- ✅ **Zone Interaction Tracking** (enter, exit, dwell time calculation)
- ✅ **Billing Queue Monitoring** (join, abandon, wait time, position tracking)
- ✅ **Reentry Detection** with time-since-last-exit classification
- ✅ **ISO 8601 Timestamps** for all events
- ✅ **JSON Schema Validation** for data integrity

### Data Storage
- ✅ **SQLite Database** with WAL mode for concurrent reads
- ✅ **Idempotent Event Insertion** (duplicate protection)
- ✅ **Indexed Queries** (store_id, track_id, event_type, timestamp)
- ✅ **Batch Insertion** with atomic transactions
- ✅ **Retry Logic** with exponential backoff for lock contention

### REST API
- ✅ **FastAPI Framework** with automatic OpenAPI documentation
- ✅ **Event Ingestion Endpoint** (single/batch, idempotent)
- ✅ **Store Metrics** (entries, exits, occupancy, visit duration)
- ✅ **Conversion Funnel** with stage-wise conversion rates
- ✅ **Spatial Heatmap** with configurable resolution
- ✅ **Anomaly Detection** (crowd surge, queue abandonment, dwell anomalies, off-hours activity)
- ✅ **Health Check** with connectivity testing
- ✅ **CORS Support** for web client integration
- ✅ **Request Logging** with correlation IDs
- ✅ **Error Sanitization** (no internal details exposed)

### DevOps & Quality
- ✅ **Docker & Docker Compose** support
- ✅ **CLI Entry Points** for video processing and API server
- ✅ **Structured JSON Logging** with correlation IDs
- ✅ **95% Test Coverage** (342 passing tests)
- ✅ **Property-Based Testing** (35 properties with Hypothesis)
- ✅ **Environment-Based Configuration** (.env support)
- ✅ **Graceful Error Handling** with comprehensive validation

---

## 🏗️ Architecture

```
┌─────────────┐
│ Video Input │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ Video Processor  │ ◄── Reads frames, extracts metadata
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Person Detector  │ ◄── YOLOv8 detection (CPU/GPU)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Person Tracker   │ ◄── ByteTrack (maintains Track IDs)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Event Generator  │ ◄── Entry/Exit/Zone/Queue/Reentry events
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   Event Store    │ ◄── SQLite (idempotent, indexed)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   API Server     │ ◄── FastAPI (metrics, funnel, heatmap, anomalies)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ External Clients │
└──────────────────┘
```

**For detailed architecture, see [DESIGN.md](DESIGN.md)**

---

## 🚀 Quick Start

### Local Installation

#### Prerequisites
- Python 3.10 or higher
- pip (Python package installer)
- Git

#### Step 1: Clone Repository
```bash
git clone <repository-url>
cd store-intelligence-platform
```

#### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

#### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 4: Download YOLOv8 Model
```bash
# Create models directory
mkdir -p models

# Download YOLOv8 nano model (lightweight, fast)
# The model will be auto-downloaded on first run, or download manually:
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -O models/yolov8n.pt
```

#### Step 5: Configure Environment
```bash
cp .env.example .env
# Edit .env if needed (defaults work for local development)
```

#### Step 6: Initialize Database
```bash
# Database will be auto-created on first run
# Or manually create the directory:
mkdir -p data
```

#### Step 7: Run Tests (Optional but Recommended)
```bash
pytest tests/ -v
```

#### Step 8: Start API Server
```bash
store-intelligence-api

# Or with custom settings:
store-intelligence-api --host 0.0.0.0 --port 8000
```

#### Step 9: Access API Documentation
Open your browser to:
- **API Docs (Swagger UI)**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

### Docker Deployment

#### Prerequisites
- Docker
- Docker Compose

#### Step 1: Build and Start
```bash
docker-compose up -d
```

#### Step 2: Verify Deployment
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f

# Test health endpoint
curl http://localhost:8000/health
```

#### Step 3: Stop Services
```bash
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

---

## 📖 Usage

### CLI Commands

#### Process Video Files

```bash
# Basic usage
store-intelligence-process --video path/to/video.mp4

# With custom configuration
store-intelligence-process --video footage.mp4 --config .env.production

# Enable debug logging
store-intelligence-process --video footage.mp4 --log-level DEBUG

# Get help
store-intelligence-process --help
```

**Output Example:**
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

#### Start API Server

```bash
# Default settings (0.0.0.0:8000)
store-intelligence-api

# Custom host and port
store-intelligence-api --host 127.0.0.1 --port 5000

# Development mode with auto-reload
store-intelligence-api --reload

# Production mode with multiple workers
store-intelligence-api --workers 4

# With custom configuration
store-intelligence-api --config .env.production

# Get help
store-intelligence-api --help
```

**For detailed CLI usage, see [CLI_USAGE.md](CLI_USAGE.md)**

---

### API Endpoints

#### Event Ingestion

**POST /events/ingest**

Ingest single event or batch of events (idempotent).

```bash
# Single event
curl -X POST http://localhost:8000/events/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt_001",
    "event_type": "ENTRY",
    "timestamp": "2024-01-15T10:30:00Z",
    "store_id": "store_001",
    "track_id": 42,
    "metadata": {}
  }'

# Batch ingestion
curl -X POST http://localhost:8000/events/ingest \
  -H "Content-Type: application/json" \
  -d '[
    {"event_id": "evt_001", "event_type": "ENTRY", ...},
    {"event_id": "evt_002", "event_type": "EXIT", ...}
  ]'
```

**Response:**
```json
{
  "success": true,
  "events_processed": 1,
  "errors": []
}
```

#### Store Metrics

**GET /stores/{id}/metrics**

Get aggregated store metrics (entries, exits, occupancy, visit duration).

```bash
# Basic metrics
curl http://localhost:8000/stores/store_001/metrics

# With time range filter
curl "http://localhost:8000/stores/store_001/metrics?start_time=2024-01-15T00:00:00Z&end_time=2024-01-15T23:59:59Z"
```

**Response:**
```json
{
  "store_id": "store_001",
  "total_entries": 1250,
  "total_exits": 1200,
  "current_occupancy": 50,
  "average_visit_duration_seconds": 1800.5,
  "time_range": {
    "start": "2024-01-15T00:00:00Z",
    "end": "2024-01-15T23:59:59Z"
  }
}
```

#### Conversion Funnel

**GET /stores/{id}/funnel**

Get customer journey funnel with conversion rates.

```bash
# Store-wide funnel
curl http://localhost:8000/stores/store_001/funnel

# Zone-specific funnel
curl http://localhost:8000/stores/store_001/funnel?zone_id=zone_cosmetics
```

**Response:**
```json
{
  "store_id": "store_001",
  "stages": [
    {"stage": "entries", "count": 1000, "conversion_rate": 1.0},
    {"stage": "zone_visits", "count": 800, "conversion_rate": 0.8},
    {"stage": "billing_queue_joins", "count": 600, "conversion_rate": 0.75},
    {"stage": "completed_purchases", "count": 550, "conversion_rate": 0.917}
  ]
}
```

#### Spatial Heatmap

**GET /stores/{id}/heatmap**

Generate spatial density heatmap from customer trajectories.

```bash
# Default resolution (50px grid)
curl http://localhost:8000/stores/store_001/heatmap

# Custom resolution
curl http://localhost:8000/stores/store_001/heatmap?resolution=100
```

**Response:**
```json
{
  "store_id": "store_001",
  "resolution": 50,
  "grid": {"width": 20, "height": 15},
  "density": [[0.1, 0.3, ...], [...], ...]
}
```

#### Anomaly Detection

**GET /stores/{id}/anomalies**

Detect unusual patterns in store metrics.

```bash
# Last 24 hours (default)
curl http://localhost:8000/stores/store_001/anomalies

# Custom time window (in hours)
curl http://localhost:8000/stores/store_001/anomalies?time_window=48
```

**Response:**
```json
{
  "store_id": "store_001",
  "anomalies": [
    {
      "type": "sudden_crowd_surge",
      "severity": "high",
      "timestamp": "2024-01-15T14:30:00Z",
      "description": "Occupancy increased by 150% in 10 minutes",
      "metrics": {
        "baseline": 50,
        "observed": 125,
        "threshold": 100
      }
    }
  ]
}
```

#### Health Check

**GET /health**

Check system health and database connectivity.

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "response_time_ms": 45
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**For complete API documentation, visit http://localhost:8000/docs**

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
# Database Configuration
DB_PATH=./data/events.db

# API Server Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Logging Configuration
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# YOLOv8 Model Configuration
YOLO_MODEL_PATH=./models/yolov8n.pt
CONFIDENCE_THRESHOLD=0.5  # 0.0 to 1.0

# Person Tracker Configuration
TRACKER_MAX_AGE=30  # frames

# Zone Configuration
ZONE_CONFIG_PATH=./config/zones.json

# Store Configuration
STORE_ID=store_001
```

### Zone Configuration

Define zones in `config/zones.json`:

```json
{
  "zones": [
    {
      "zone_id": "zone_001",
      "zone_name": "Electronics Section",
      "zone_type": "GENERAL",
      "polygon": [
        {"x": 250, "y": 100},
        {"x": 450, "y": 100},
        {"x": 450, "y": 300},
        {"x": 250, "y": 300}
      ]
    },
    {
      "zone_id": "zone_billing",
      "zone_name": "Billing Queue",
      "zone_type": "BILLING_QUEUE",
      "polygon": [
        {"x": 100, "y": 600},
        {"x": 400, "y": 600},
        {"x": 400, "y": 700},
        {"x": 100, "y": 700}
      ]
    }
  ]
}
```

**Zone Types:**
- `GENERAL`: Regular store zones (cosmetics, electronics, clothing, etc.)
- `BILLING_QUEUE`: Checkout/billing queue area (enables queue analytics)

---

## 📁 Project Structure

```
store-intelligence-platform/
├── .kiro/
│   └── specs/                      # Project specifications
│       └── store-intelligence-platform/
│           ├── requirements.md     # Functional requirements
│           ├── design.md          # Technical design
│           └── tasks.md           # Implementation tasks
├── src/                           # Source code
│   ├── api_server.py             # FastAPI application
│   ├── cli.py                    # CLI entry points
│   ├── config.py                 # Configuration manager
│   ├── event_generator.py        # Event generation logic
│   ├── event_store.py            # Database layer
│   ├── logger.py                 # Structured logging
│   ├── models.py                 # Data models
│   ├── person_detector.py        # YOLOv8 detection
│   ├── person_tracker.py         # ByteTrack tracking
│   ├── pipeline.py               # Video processing pipeline
│   └── video_processor.py        # Video decoding
├── tests/                         # Test suite (342 tests)
│   ├── test_api_server_*.py      # API tests
│   ├── test_cli.py               # CLI tests
│   ├── test_config.py            # Config tests
│   ├── test_event_*.py           # Event tests
│   ├── test_logger*.py           # Logger tests
│   ├── test_models*.py           # Model tests
│   ├── test_person_*.py          # Detection/tracking tests
│   ├── test_pipeline*.py         # Pipeline tests
│   └── test_video_*.py           # Video processing tests
├── config/                        # Configuration files
│   └── zones.json                # Zone definitions
├── data/                          # Database storage
│   └── events.db                 # SQLite database
├── models/                        # ML model files
│   └── yolov8n.pt               # YOLOv8 model
├── .env.example                   # Example environment variables
├── .gitignore                     # Git ignore rules
├── conftest.py                    # Pytest configuration
├── pytest.ini                     # Pytest settings
├── requirements.txt               # Python dependencies
├── CLI_USAGE.md                   # CLI documentation
├── DESIGN.md                      # Architecture documentation
├── CHOICES.md                     # Design decisions
└── README.md                      # This file
```

---

## 🛠️ Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -r requirements.txt

# Install pre-commit hooks (optional)
pre-commit install
```

### Code Quality Tools

```bash
# Format code with black
black src/ tests/

# Lint with flake8
flake8 src/ tests/

# Type check with mypy
mypy src/

# Run all quality checks
black src/ tests/ && flake8 src/ tests/ && mypy src/
```

### Running the Application

```bash
# Process a video file
store-intelligence-process --video sample_video.mp4

# Start API server in development mode
store-intelligence-api --reload

# Start with debug logging
store-intelligence-api --log-level DEBUG --reload
```

---

## 🧪 Testing

### Run All Tests

```bash
# All tests with coverage
pytest tests/ -v --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
```

### Run Specific Test Types

```bash
# Unit tests only
pytest tests/ -m unit -v

# Property-based tests only
pytest tests/ -m property -v

# Integration tests only
pytest tests/ -m integration -v

# Performance tests only
pytest tests/ -m performance -v

# Specific test file
pytest tests/test_api_server_core.py -v

# Specific test function
pytest tests/test_event_store.py::TestEventInsertion::test_insert_event_success -v
```

### Test Coverage

Current coverage: **95%**

```
Name                     Stmts   Miss  Cover
--------------------------------------------
src/api_server.py          213      9   96%
src/cli.py                 121     12   90%
src/config.py               52      0  100%
src/event_generator.py     259     18   93%
src/event_store.py         285     25   91%
src/logger.py               85      0  100%
src/models.py               84      0  100%
src/person_detector.py      61      0  100%
src/person_tracker.py      132      2   98%
src/pipeline.py            104      3   97%
src/video_processor.py      83     10   88%
--------------------------------------------
TOTAL                     1480     79   95%
```

---

## 📚 API Documentation

### Interactive Documentation

Once the API server is running, access interactive documentation at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Authentication

Currently, the API does not require authentication. For production deployment, consider adding:
- API key authentication
- JWT tokens
- OAuth2

### Rate Limiting

No rate limiting is currently implemented. For production, consider using:
- nginx rate limiting
- API gateway (AWS API Gateway, Kong, etc.)
- Python middleware (slowapi, etc.)

---

## ⚡ Performance

### Benchmarks

- **Detection Speed**: ≥10 FPS on CPU (YOLOv8n), ≥30 FPS on GPU
- **Health Endpoint**: <100ms response time
- **Metrics Query**: <500ms for 1M events
- **Event Insertion**: ≥1000 events/second (batch mode)
- **Video Processing**: 1-hour video in <2 hours (real-time capable)

### Optimization Tips

1. **Use GPU for Detection**: Set `CUDA_VISIBLE_DEVICES` if GPU available
2. **Batch Event Insertion**: Use `/events/ingest` with arrays for better throughput
3. **Optimize Resolution**: Lower confidence threshold for fewer false negatives
4. **Database Tuning**: SQLite WAL mode enabled by default for concurrent reads
5. **Horizontal Scaling**: Run multiple API workers with `--workers N`

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Video File Not Found
```
Error: Video file not found: path/to/video.mp4
```
**Solution**: Check file path is correct and file exists

#### 2. YOLOv8 Model Not Found
```
Error: YOLO_MODEL_PATH does not exist: ./models/yolov8n.pt
```
**Solution**: Download model or update `YOLO_MODEL_PATH` in `.env`

#### 3. Port Already in Use
```
Error: address already in use
```
**Solution**: Use different port with `--port` flag or stop conflicting process

#### 4. Database Lock Error
```
Error: database is locked
```
**Solution**: Enable WAL mode (done by default) or reduce concurrent writes

#### 5. Out of Memory
```
Error: CUDA out of memory
```
**Solution**: Reduce batch size, use CPU mode, or use smaller model (yolov8n)

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# CLI
store-intelligence-process --video video.mp4 --log-level DEBUG

# API
store-intelligence-api --log-level DEBUG
```

### Getting Help

- **Issues**: Open an issue on GitHub
- **Discussions**: Use GitHub Discussions
- **Documentation**: Check DESIGN.md and CHOICES.md

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest tests/ -v`)
5. Run code quality checks (`black`, `flake8`, `mypy`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add type hints to all functions
- Write tests for new features
- Update documentation
- Maintain ≥70% code coverage

---

## 📄 License

MIT License - see LICENSE file for details

---

## 🙏 Acknowledgments

- **YOLOv8**: Ultralytics for state-of-the-art object detection
- **ByteTrack**: Multi-object tracking algorithm
- **FastAPI**: Modern Python web framework
- **Hypothesis**: Property-based testing library

---

## 📊 Project Status

- **Version**: 1.0.0 (Beta)
- **Status**: Production-Ready
- **Test Coverage**: 95%
- **Tests**: 342 passing
- **Last Updated**: 2024

---

## 🔗 Related Documentation

- [Technical Design (DESIGN.md)](DESIGN.md) - System architecture and component design
- [Design Choices (CHOICES.md)](CHOICES.md) - Technology decisions and trade-offs
- [CLI Usage Guide (CLI_USAGE.md)](CLI_USAGE.md) - Detailed CLI documentation
- [Requirements Specification](.kiro/specs/store-intelligence-platform/requirements.md) - Functional requirements
- [Implementation Tasks](.kiro/specs/store-intelligence-platform/tasks.md) - Development roadmap

---

**Built with ❤️ for retail analytics and computer vision**

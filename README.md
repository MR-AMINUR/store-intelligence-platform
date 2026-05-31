# Store Intelligence Platform

A computer vision-based retail analytics platform that processes CCTV footage to extract actionable insights about customer behavior.

## Overview

The Store Intelligence Platform analyzes video footage from retail stores to:
- Detect and track customers using YOLOv8 and ByteTrack
- Generate structured events (entry, exit, zone interactions, billing queue activities)
- Store events in a persistent database
- Provide REST API endpoints for analytics (metrics, conversion funnels, heatmaps, anomaly detection)

## Features

- **Person Detection**: YOLOv8-based detection with configurable confidence thresholds
- **Person Tracking**: ByteTrack algorithm for consistent identity across frames
- **Event Generation**: Structured events for customer journey analysis
- **Zone Analytics**: Track customer interactions with store zones
- **Billing Queue Monitoring**: Detect queue joins, abandons, and wait times
- **REST API**: FastAPI-based endpoints for data access and analytics
- **Persistent Storage**: SQLite database with idempotency guarantees
- **Docker Support**: Containerized deployment with docker-compose

## Quick Start

### Prerequisites

- Python 3.10 or higher
- pip

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd store-intelligence-platform
```

2. Create and activate virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run tests:
```bash
pytest tests/ -v
```

## Project Structure

```
store-intelligence-platform/
├── src/                    # Source code
├── tests/                  # Test suite
├── config/                 # Configuration files
├── data/                   # Database storage
├── models/                 # ML model files
├── requirements.txt        # Python dependencies
├── .env.example           # Example environment variables
└── README.md              # This file
```

## Development

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed setup instructions.

### Running Tests

```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/ -m unit

# Property tests only
pytest tests/ -m property

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type check
mypy src/
```

## Documentation

- [Requirements](requirements.md) - Functional requirements
- [Design](design.md) - Technical design and architecture
- [Setup Guide](SETUP_GUIDE.md) - Detailed setup instructions

## License

[Add license information]

## Status

🚧 **Under Development** - This project is currently in active development.
This an implementation of a real world problem to monitor CCTV footage with AI agent

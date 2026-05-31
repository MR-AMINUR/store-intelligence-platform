# Quick Reference Guide

## Common Commands

### Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Activate virtual environment (Linux/macOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify setup
python verify_setup.py
```

### Development
```bash
# Run all tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test types
pytest tests/ -m unit          # Unit tests only
pytest tests/ -m property      # Property tests only
pytest tests/ -m integration   # Integration tests only

# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type check
mypy src/

# Run all quality checks
make all
```

### Running the Application
```bash
# Start API server
uvicorn src.api:app --reload

# Or using make
make run-api

# Process video (once CLI is implemented)
python -m src.cli process-video --video-path path/to/video.mp4
```

### Docker
```bash
# Build image
docker build -t store-intelligence-platform .

# Run with docker-compose
docker-compose up

# Stop containers
docker-compose down
```

## Project Structure Quick Reference

```
src/
├── __init__.py           # Package initialization
├── config.py             # Configuration manager (Task 2)
├── logger.py             # Logging utilities (Task 3)
├── models.py             # Data models (Task 4)
├── video_processor.py    # Video processing (Task 5)
├── detector.py           # Person detection (Task 6)
├── tracker.py            # Person tracking (Task 8)
├── event_generator.py    # Event generation (Task 9)
├── event_store.py        # Database layer (Task 12-13)
├── api.py                # FastAPI server (Task 15-17)
├── pipeline.py           # Pipeline orchestrator (Task 18)
└── cli.py                # CLI entry points (Task 20)

tests/
├── __init__.py
├── test_config.py
├── test_logger.py
├── test_models.py
├── test_video_processor.py
├── test_detector.py
├── test_tracker.py
├── test_event_generator.py
├── test_event_store.py
├── test_api.py
└── test_integration.py
```

## Environment Variables

```bash
# Database
DB_PATH=./data/events.db

# API Server
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO

# Detection
YOLO_MODEL_PATH=./models/yolov8n.pt
CONFIDENCE_THRESHOLD=0.5

# Tracking
TRACKER_MAX_AGE=30

# Configuration
ZONE_CONFIG_PATH=./config/zones.json
STORE_ID=store_001
```

## Testing Markers

Use pytest markers to run specific test categories:

```bash
pytest -m unit          # Fast unit tests
pytest -m property      # Property-based tests
pytest -m integration   # Integration tests
pytest -m performance   # Performance tests
pytest -m slow          # Slow running tests
```

## Code Quality Standards

- **Line Length**: 100 characters (black, flake8)
- **Type Hints**: Required for all functions (mypy)
- **Docstrings**: Google-style for all public functions
- **Test Coverage**: Minimum 70%
- **Style Guide**: PEP 8

## Useful Links

- [Requirements](requirements.md) - Functional requirements
- [Design](design.md) - Technical design
- [Setup Guide](SETUP_GUIDE.md) - Detailed setup
- [Tasks](.kiro/specs/store-intelligence-platform/tasks.md) - Implementation tasks

## Troubleshooting

### Import Errors
```bash
# Make sure you're in the project root
cd /path/to/store-intelligence-platform

# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Test Failures
```bash
# Run with verbose output
pytest tests/ -vv

# Run specific test file
pytest tests/test_config.py -v

# Run specific test function
pytest tests/test_config.py::test_function_name -v
```

### Coverage Issues
```bash
# Generate detailed coverage report
pytest tests/ --cov=src --cov-report=html

# Open coverage report
# Windows: start htmlcov/index.html
# Linux: xdg-open htmlcov/index.html
# macOS: open htmlcov/index.html
```

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/task-name

# Make changes and commit
git add .
git commit -m "Implement feature X"

# Run tests before pushing
make all

# Push to remote
git push origin feature/task-name
```

## Performance Tips

- Use `yolov8n.pt` (nano) for CPU, `yolov8s.pt` or `yolov8m.pt` for GPU
- Enable GPU acceleration by installing PyTorch with CUDA
- Use batch processing for multiple videos
- Configure appropriate confidence thresholds (default: 0.5)

## Support

For issues or questions:
1. Check this quick reference
2. Review [SETUP_GUIDE.md](SETUP_GUIDE.md)
3. Check [design.md](design.md) for architecture details
4. Review [requirements.md](requirements.md) for specifications

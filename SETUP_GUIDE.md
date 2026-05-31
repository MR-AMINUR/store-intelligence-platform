# Setup Guide - Store Intelligence Platform

This guide will help you set up the development environment for the Store Intelligence Platform.

## Prerequisites

- Python 3.10 or higher
- pip (Python package installer)
- Git

## Setup Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd store-intelligence-platform
```

### 2. Create Virtual Environment

#### On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

#### On Linux/macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file and customize it:

```bash
cp .env.example .env
```

Edit `.env` to set your configuration parameters.

### 5. Download YOLOv8 Model

The YOLOv8 model will be automatically downloaded on first use. To pre-download:

```bash
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

### 6. Create Zone Configuration

Create a `config/zones.json` file with your store's zone definitions. See `config/README.md` for the format.

### 7. Verify Installation

Run the test suite to verify everything is set up correctly:

```bash
pytest tests/ -v
```

## Directory Structure

```
store-intelligence-platform/
├── src/                    # Source code
│   ├── __init__.py
│   ├── config.py          # Configuration manager
│   ├── logger.py          # Logging utilities
│   ├── models.py          # Data models
│   ├── video_processor.py # Video processing
│   ├── detector.py        # Person detection
│   ├── tracker.py         # Person tracking
│   ├── event_generator.py # Event generation
│   ├── event_store.py     # Database layer
│   ├── api.py             # FastAPI server
│   ├── pipeline.py        # Pipeline orchestrator
│   └── cli.py             # CLI entry points
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_logger.py
│   ├── test_models.py
│   ├── test_video_processor.py
│   ├── test_detector.py
│   ├── test_tracker.py
│   ├── test_event_generator.py
│   ├── test_event_store.py
│   ├── test_api.py
│   └── test_integration.py
├── config/                # Configuration files
│   └── zones.json
├── data/                  # Database storage
│   └── events.db
├── models/                # ML model files
│   └── yolov8n.pt
├── requirements.txt       # Python dependencies
├── .env.example          # Example environment variables
├── .gitignore            # Git ignore rules
├── setup.py              # Package setup
└── README.md             # Project documentation
```

## Next Steps

1. Read the `README.md` for usage instructions
2. Review the `design.md` for architecture details
3. Check `requirements.md` for functional requirements
4. Start developing or running the application

## Troubleshooting

### OpenCV Installation Issues

If you encounter issues installing opencv-python, try:

```bash
pip install opencv-python-headless
```

### CUDA/GPU Support

For GPU acceleration with YOLOv8, install PyTorch with CUDA support:

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Virtual Environment Not Activating

Make sure you're using the correct activation command for your shell:
- Windows CMD: `venv\Scripts\activate.bat`
- Windows PowerShell: `venv\Scripts\Activate.ps1`
- Linux/macOS: `source venv/bin/activate`

## Development Workflow

1. Activate virtual environment
2. Make code changes
3. Run tests: `pytest tests/ -v`
4. Run linter: `flake8 src/ tests/`
5. Format code: `black src/ tests/`
6. Type check: `mypy src/`
7. Commit changes

## Support

For issues or questions, please refer to the project documentation or open an issue in the repository.

# Computer Vision Pipeline - Store Intelligence Platform

Complete end-to-end computer vision pipeline that transforms raw CCTV footage into structured events for the Store Intelligence Platform.

## Architecture

```
Raw CCTV Video
    ↓
Video Upload
    ↓
YOLOv8 Person Detection (detector.py)
    ↓
Multi-Object Tracking - ByteTrack (tracker.py)
    ↓
Zone Mapping (zone_manager.py)
    ↓
Event Generation (event_generator.py)
    ↓
POST /events/ingest (event_sender.py)
    ↓
Existing FastAPI Backend
    ↓
SQLite Database
    ↓
Analytics Engine
    ↓
Dashboard
```

## Features

✅ **YOLOv8 Person Detection**
- GPU acceleration with CPU fallback
- Configurable confidence threshold
- Person-only filtering (class_id = 0)

✅ **ByteTrack Multi-Object Tracking**
- Consistent track IDs across frames
- IoU-based matching
- Occlusion handling (max_age threshold)

✅ **Store Zone Management**
- Configurable zones via JSON
- Point-in-polygon testing
- General and billing queue zones

✅ **Event Generation**
- ENTRY, EXIT, ZONE_ENTER, ZONE_EXIT, ZONE_DWELL
- BILLING_QUEUE_JOIN, BILLING_QUEUE_ABANDON
- REENTRY detection

✅ **API Integration**
- Automatic batching
- Retry logic with exponential backoff
- Health checking

✅ **Performance**
- 20+ FPS processing speed
- Batch inference support
- Frame skipping for lower FPS

✅ **Error Handling**
- Camera disconnects
- Invalid videos
- Empty frames
- Tracking loss
- API failures
- Network retries

## Installation

### 1. Install Dependencies

```bash
# Core dependencies
pip install -r requirements.txt

# Additional packages for pipeline
pip install ultralytics opencv-python-headless requests numpy torch
```

### 2. Download YOLOv8 Model

```bash
# Download YOLOv8 nano model (fastest)
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -O models/yolov8n.pt

# Or use larger models for better accuracy
# yolov8s.pt (small), yolov8m.pt (medium), yolov8l.pt (large)
```

### 3. Configure Zones

Edit `config/zones.json` to define your store zones:

```json
{
  "zones": [
    {
      "zone_id": "entrance",
      "zone_name": "Store Entrance",
      "zone_type": "GENERAL",
      "polygon": [
        {"x": 50, "y": 50},
        {"x": 200, "y": 50},
        {"x": 200, "y": 150},
        {"x": 50, "y": 150}
      ]
    },
    {
      "zone_id": "checkout",
      "zone_name": "Checkout Area",
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

## Usage

### Basic Usage

```bash
# Process video with default settings
python -m pipeline.run_pipeline --video sample.mp4
```

### With Custom Configuration

```bash
# Use configuration file
python -m pipeline.run_pipeline --video sample.mp4 --config my_config.json
```

### With Environment Variables

```bash
# Set environment variables
export API_BASE_URL=http://localhost:8000
export STORE_ID=store_001
export CONFIDENCE_THRESHOLD=0.6

# Run pipeline
python -m pipeline.run_pipeline --video sample.mp4
```

### With CLI Arguments

```bash
# Override specific parameters
python -m pipeline.run_pipeline --video sample.mp4 \
    --store-id store_002 \
    --api-url http://localhost:8000 \
    --confidence 0.6 \
    --no-replay-timing \
    --verbose
```

## Configuration

### Configuration File (JSON)

Create `pipeline_config.json`:

```json
{
  "store_id": "store_001",
  "camera_name": "camera_001",
  "mode": "file",
  "replay_timing": true,
  "detector": {
    "model_path": "./models/yolov8n.pt",
    "confidence_threshold": 0.5,
    "device": "auto",
    "batch_size": 1
  },
  "tracker": {
    "max_age": 30,
    "min_hits": 3,
    "iou_threshold": 0.3
  },
  "zone": {
    "config_path": "./config/zones.json",
    "dwell_threshold_seconds": 5.0
  },
  "video": {
    "frame_skip": 0,
    "target_fps": null,
    "resize_width": null,
    "resize_height": null
  },
  "api": {
    "base_url": "http://localhost:8000",
    "ingest_endpoint": "/events/ingest",
    "timeout_seconds": 30,
    "max_retries": 3,
    "retry_delay_seconds": 1.0,
    "batch_size": 50
  }
}
```

### Environment Variables

```bash
# Store Configuration
export STORE_ID=store_001
export CAMERA_NAME=camera_001
export PIPELINE_MODE=file
export REPLAY_TIMING=true

# Detector Configuration
export YOLO_MODEL_PATH=./models/yolov8n.pt
export CONFIDENCE_THRESHOLD=0.5
export DEVICE=auto
export BATCH_SIZE=1

# Tracker Configuration
export TRACKER_MAX_AGE=30
export TRACKER_MIN_HITS=3
export TRACKER_IOU_THRESHOLD=0.3

# Zone Configuration
export ZONE_CONFIG_PATH=./config/zones.json
export DWELL_THRESHOLD=5.0

# Video Configuration
export FRAME_SKIP=0
export TARGET_FPS=30

# API Configuration
export API_BASE_URL=http://localhost:8000
export API_TIMEOUT=30
export API_MAX_RETRIES=3
export API_BATCH_SIZE=50
```

## Module Structure

```
pipeline/
├── __init__.py           # Package initialization
├── config.py             # Configuration management
├── detector.py           # YOLOv8 person detection
├── tracker.py            # ByteTrack multi-object tracking
├── zone_manager.py       # Zone definition and queries
├── event_generator.py    # Event generation from tracks
├── event_sender.py       # HTTP client for API integration
├── video_processor.py    # Video file processing
├── run_pipeline.py       # Main pipeline orchestrator and CLI
└── README.md             # This file
```

## Event Types Generated

| Event Type | Description | Metadata |
|------------|-------------|----------|
| ENTRY | Person enters store | - |
| EXIT | Person exits store | - |
| ZONE_ENTER | Person enters zone | zone_id, zone_name |
| ZONE_EXIT | Person exits zone | zone_id, zone_name, zone_duration_seconds |
| ZONE_DWELL | Person dwells in zone | zone_id, zone_name, dwell_duration_seconds |
| BILLING_QUEUE_JOIN | Person joins checkout queue | queue_position |
| BILLING_QUEUE_ABANDON | Person abandons queue | queue_wait_time_seconds, high_wait_time |
| REENTRY | Person re-enters after exit | time_since_last_exit_seconds, immediate_return, previous_track_id |

## Performance Tuning

### For Real-Time Processing (20+ FPS)

```json
{
  "detector": {
    "model_path": "./models/yolov8n.pt",
    "batch_size": 1
  },
  "video": {
    "frame_skip": 0,
    "resize_width": 640,
    "resize_height": 480
  }
}
```

### For High Accuracy (Lower FPS)

```json
{
  "detector": {
    "model_path": "./models/yolov8l.pt",
    "confidence_threshold": 0.6,
    "batch_size": 4
  },
  "video": {
    "frame_skip": 0
  }
}
```

### For Fast Batch Processing

```json
{
  "detector": {
    "model_path": "./models/yolov8n.pt",
    "batch_size": 8
  },
  "video": {
    "frame_skip": 2,
    "target_fps": 15
  },
  "replay_timing": false
}
```

## Example Workflow

### 1. Start Backend Server

```bash
# Terminal 1: Start FastAPI backend
python -m src.api_server
```

### 2. Process CCTV Footage

```bash
# Terminal 2: Run pipeline
python -m pipeline.run_pipeline \
    --video store_footage.mp4 \
    --store-id store_001 \
    --api-url http://localhost:8000
```

### 3. View Results

```bash
# Open dashboard in browser
# http://localhost:3000

# Or query API directly
curl http://localhost:8000/stores/store_001/metrics
curl http://localhost:8000/stores/store_001/funnel
curl http://localhost:8000/stores/store_001/anomalies?time_window=24
```

## Troubleshooting

### Pipeline Not Starting

**Issue**: `ModuleNotFoundError: No module named 'pipeline'`

**Solution**:
```bash
# Run from project root
cd /path/to/store-intelligence-platform
python -m pipeline.run_pipeline --video sample.mp4
```

### YOLOv8 Model Not Found

**Issue**: `FileNotFoundError: YOLO model not found`

**Solution**:
```bash
# Download model
mkdir -p models
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -O models/yolov8n.pt
```

### Backend API Not Reachable

**Issue**: `Connection error: Failed to connect to http://localhost:8000`

**Solution**:
```bash
# Start backend server
python -m src.api_server

# Or update API URL
python -m pipeline.run_pipeline --video sample.mp4 --api-url http://your-server:8000
```

### Low FPS / Slow Processing

**Issue**: Processing slower than 10 FPS

**Solutions**:
1. Use smaller YOLOv8 model: `yolov8n.pt` instead of `yolov8l.pt`
2. Enable frame skipping: `--frame-skip 2`
3. Reduce resolution in config
4. Ensure GPU is being used (check logs for "Device: cuda")

### GPU Not Detected

**Issue**: Pipeline using CPU instead of GPU

**Solution**:
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Install GPU-enabled PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

## Integration with Existing Backend

The pipeline is designed to integrate seamlessly with your existing backend:

1. **No Backend Modifications Required**: Pipeline sends events via existing `/events/ingest` API
2. **Same Event Schema**: Events match your existing `Event` model
3. **Existing Analytics Work**: Dashboard updates automatically with new data
4. **Independent Operation**: Pipeline can run separately from backend

## Logs

Pipeline logs are written to:
- **Console**: Real-time progress and errors
- **File**: `pipeline.log` (detailed logs with timestamps)

Example log output:

```
2024-06-28 10:00:00 - pipeline.detector - INFO - YOLOv8 model loaded successfully from ./models/yolov8n.pt
2024-06-28 10:00:01 - pipeline.tracker - INFO - PersonTracker initialized (max_age=30, min_hits=3, iou_threshold=0.3)
2024-06-28 10:00:02 - pipeline.zone_manager - INFO - Loaded 6 zones from ./config/zones.json
2024-06-28 10:00:03 - pipeline.event_sender - INFO - Backend API health check passed
2024-06-28 10:00:05 - pipeline.run_pipeline - INFO - Progress: 100 frames | 22.5 FPS | 45 detections | 12 tracks | 8 events
...
2024-06-28 10:05:00 - pipeline.run_pipeline - INFO - Pipeline processing complete
```

## License

This pipeline module is part of the Store Intelligence Platform and follows the same license as the main project.

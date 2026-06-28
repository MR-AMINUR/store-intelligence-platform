# Pipeline Quick Reference Card

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Download YOLOv8 model
mkdir -p models
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -O models/yolov8n.pt

# Test installation
python test_pipeline_installation.py
```

## Basic Usage

```bash
# Start backend
python -m src.api_server

# Process video (basic)
python -m pipeline.run_pipeline --video sample.mp4

# Process video (with options)
python -m pipeline.run_pipeline \
    --video sample.mp4 \
    --store-id store_001 \
    --api-url http://localhost:8000 \
    --confidence 0.5 \
    --verbose
```

## Configuration Methods

### Method 1: CLI Arguments (Highest Priority)

```bash
python -m pipeline.run_pipeline \
    --video sample.mp4 \
    --store-id store_001 \
    --api-url http://localhost:8000 \
    --confidence 0.6 \
    --no-replay-timing
```

### Method 2: Configuration File

```bash
# Create config file: pipeline_config.json
python -m pipeline.run_pipeline \
    --video sample.mp4 \
    --config pipeline_config.json
```

### Method 3: Environment Variables

```bash
export API_BASE_URL=http://localhost:8000
export STORE_ID=store_001
export CONFIDENCE_THRESHOLD=0.6

python -m pipeline.run_pipeline --video sample.mp4
```

## CLI Arguments Reference

| Argument | Type | Description | Example |
|----------|------|-------------|---------|
| `--video` | Required | Path to video file | `--video sample.mp4` |
| `--config` | Optional | Config JSON file | `--config my_config.json` |
| `--store-id` | Optional | Store identifier | `--store-id store_001` |
| `--api-url` | Optional | Backend API URL | `--api-url http://localhost:8000` |
| `--confidence` | Optional | Confidence threshold [0-1] | `--confidence 0.6` |
| `--no-replay-timing` | Flag | Process as fast as possible | `--no-replay-timing` |
| `--verbose` | Flag | Enable verbose logging | `--verbose` |

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `STORE_ID` | `store_001` | Store identifier |
| `API_BASE_URL` | `http://localhost:8000` | Backend API URL |
| `YOLO_MODEL_PATH` | `./models/yolov8n.pt` | YOLOv8 model path |
| `CONFIDENCE_THRESHOLD` | `0.5` | Detection confidence [0-1] |
| `DEVICE` | `auto` | Device: auto/cuda/cpu |
| `TRACKER_MAX_AGE` | `30` | Max frames to keep track |
| `ZONE_CONFIG_PATH` | `./config/zones.json` | Zone config path |
| `FRAME_SKIP` | `0` | Frames to skip |
| `API_BATCH_SIZE` | `50` | Events per API batch |

## Common Commands

### Process Single Video

```bash
python -m pipeline.run_pipeline --video store_footage.mp4
```

### Process Multiple Videos (Loop)

```bash
for video in videos/*.mp4; do
    python -m pipeline.run_pipeline --video "$video" --store-id store_001
done
```

### Process with Custom Zones

```bash
# Edit config/zones.json first
python -m pipeline.run_pipeline --video sample.mp4
```

### Process Fast (No Replay Timing)

```bash
python -m pipeline.run_pipeline \
    --video sample.mp4 \
    --no-replay-timing
```

### Process with Debug Logging

```bash
python -m pipeline.run_pipeline \
    --video sample.mp4 \
    --verbose
```

## Performance Tuning

### High Performance (GPU)

```json
{
  "detector": {
    "model_path": "./models/yolov8n.pt",
    "batch_size": 1,
    "device": "cuda"
  },
  "video": {
    "frame_skip": 0,
    "resize_width": 640,
    "resize_height": 480
  },
  "replay_timing": false
}
```

### High Accuracy (Slower)

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

### CPU-Friendly (Low Resource)

```json
{
  "detector": {
    "model_path": "./models/yolov8n.pt",
    "device": "cpu"
  },
  "video": {
    "frame_skip": 2,
    "resize_width": 640,
    "resize_height": 480
  }
}
```

## Verification Commands

```bash
# Check backend health
curl http://localhost:8000/health

# Check events were inserted
curl http://localhost:8000/stores/store_001/metrics

# Check conversion funnel
curl http://localhost:8000/stores/store_001/funnel

# Check anomalies
curl http://localhost:8000/stores/store_001/anomalies?time_window=24
```

## Troubleshooting

### Backend Not Reachable

```bash
# Start backend
python -m src.api_server

# Or use remote backend
python -m pipeline.run_pipeline \
    --video sample.mp4 \
    --api-url https://your-backend.com
```

### YOLO Model Not Found

```bash
# Download model
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -O models/yolov8n.pt
```

### Low FPS

```bash
# Use smaller model
python -m pipeline.run_pipeline \
    --video sample.mp4 \
    --config pipeline_config.json \
    --no-replay-timing

# Or enable frame skipping via environment
export FRAME_SKIP=2
python -m pipeline.run_pipeline --video sample.mp4
```

### GPU Not Detected

```bash
# Check CUDA
python -c "import torch; print(torch.cuda.is_available())"

# Install CUDA PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

## File Locations

```
pipeline/                      # Pipeline module
├── config.py                  # Configuration
├── detector.py                # YOLOv8 detection
├── tracker.py                 # ByteTrack tracking
├── zone_manager.py            # Zone management
├── event_generator.py         # Event generation
├── event_sender.py            # API client
├── video_processor.py         # Video processing
├── run_pipeline.py            # Main orchestrator
└── README.md                  # Documentation

config/
└── zones.json                 # Zone configuration

models/
└── yolov8n.pt                 # YOLOv8 model weights

pipeline_config.json           # Sample config
pipeline.log                   # Runtime logs
```

## Event Types

| Type | Trigger | Metadata |
|------|---------|----------|
| ENTRY | Person enters | - |
| EXIT | Person exits | - |
| ZONE_ENTER | Enters zone | zone_id, zone_name |
| ZONE_EXIT | Exits zone | zone_id, zone_name, duration |
| ZONE_DWELL | Dwells >5s | zone_id, zone_name, duration |
| BILLING_QUEUE_JOIN | Joins checkout | queue_position |
| BILLING_QUEUE_ABANDON | Leaves queue | wait_time, high_wait_time |
| REENTRY | Re-enters <5min | time_since_exit, immediate_return |

## YOLOv8 Model Sizes

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| yolov8n | 6 MB | Fastest | Good | Real-time, low-end GPU |
| yolov8s | 22 MB | Fast | Better | Real-time, mid-range GPU |
| yolov8m | 52 MB | Medium | Very Good | Batch processing |
| yolov8l | 87 MB | Slow | Excellent | Offline processing |

Download: `wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8{n,s,m,l}.pt`

## Support Resources

- **Pipeline README**: `pipeline/README.md`
- **Integration Guide**: `PIPELINE_INTEGRATION_GUIDE.md`
- **Completion Summary**: `CV_PIPELINE_COMPLETION_SUMMARY.md`
- **Test Installation**: `python test_pipeline_installation.py`
- **Logs**: `pipeline.log`

---

**Quick Links**:
- Backend API Docs: http://localhost:8000/docs
- Frontend Dashboard: http://localhost:3000
- GitHub YOLOv8: https://github.com/ultralytics/ultralytics

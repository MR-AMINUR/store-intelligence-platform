# Models Directory

This directory stores machine learning model files for the Store Intelligence Platform.

## Required Models

- `yolov8n.pt` - YOLOv8 nano model for person detection (recommended for CPU)
- `yolov8s.pt` - YOLOv8 small model (optional, better accuracy)
- `yolov8m.pt` - YOLOv8 medium model (optional, best accuracy)

## Downloading Models

YOLOv8 models will be automatically downloaded by the Ultralytics library on first use.

Alternatively, you can manually download models:

```bash
# Using Python
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

Or download directly from:
- https://github.com/ultralytics/assets/releases

## Notes

- Model files are excluded from version control due to their size (see `.gitignore`)
- The default model is `yolov8n.pt` (nano) which provides good performance on CPU
- For GPU deployments, consider using larger models (yolov8s.pt or yolov8m.pt) for better accuracy

"""YOLOv8 Person Detector for CV Pipeline.

This module provides person detection using YOLOv8 with GPU acceleration
and automatic CPU fallback.
"""

import logging
from typing import Any, List

import numpy as np
import torch
from ultralytics import YOLO

# Configure logging
logger = logging.getLogger(__name__)


class BoundingBox:
    """Bounding box representation.
    
    Attributes:
        x: X-coordinate of top-left corner
        y: Y-coordinate of top-left corner
        width: Box width
        height: Box height
    """
    
    def __init__(self, x: float, y: float, width: float, height: float):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }


class Detection:
    """Person detection result.
    
    Attributes:
        bbox: Bounding box
        confidence: Detection confidence score
        class_id: Object class ID (0 for person)
    """
    
    def __init__(self, bbox: BoundingBox, confidence: float, class_id: int = 0):
        self.bbox = bbox
        self.confidence = confidence
        self.class_id = class_id
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "bbox": self.bbox.to_dict(),
            "confidence": self.confidence,
            "class_id": self.class_id,
        }


class PersonDetector:
    """YOLOv8-based person detector.
    
    Detects people in video frames using YOLOv8. Supports GPU acceleration
    with automatic CPU fallback. Filters detections by confidence threshold
    and only returns person class (class_id = 0).
    
    Attributes:
        model: YOLOv8 model instance
        confidence_threshold: Minimum confidence for detections
        device: Device being used ('cuda' or 'cpu')
        batch_size: Batch size for inference
    """
    
    PERSON_CLASS_ID = 0  # COCO class ID for person
    
    def __init__(
        self,
        model_path: str,
        confidence_threshold: float = 0.5,
        device: str = "auto",
        batch_size: int = 1,
    ):
        """Initialize person detector.
        
        Args:
            model_path: Path to YOLOv8 model weights
            confidence_threshold: Minimum confidence score [0, 1]
            device: Device to use ('auto', 'cuda', or 'cpu')
            batch_size: Batch size for inference
            
        Raises:
            FileNotFoundError: If model file doesn't exist
            ValueError: If confidence_threshold not in [0, 1]
        """
        if not (0 <= confidence_threshold <= 1):
            raise ValueError(f"Confidence threshold must be in [0, 1], got {confidence_threshold}")
        
        self.confidence_threshold = confidence_threshold
        self.batch_size = batch_size
        
        # Determine device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        logger.info(f"Initializing YOLOv8 detector on device: {self.device}")
        
        try:
            # Load YOLOv8 model with PyTorch 2.6+ compatibility patch
            self._load_model(model_path)
            logger.info(f"YOLOv8 model loaded successfully from {model_path}")
        except FileNotFoundError:
            logger.error(f"Model file not found: {model_path}")
            raise
        except Exception as e:
            logger.error(f"Failed to load YOLOv8 model: {e}")
            raise
    
    def _load_model(self, model_path: str) -> None:
        """Load YOLO model with PyTorch 2.6+ compatibility.
        
        Args:
            model_path: Path to model weights
        """
        # Patch torch.load for PyTorch 2.6+ compatibility
        # PyTorch 2.6 changed default to weights_only=True which breaks YOLOv8
        original_load = torch.load
        
        def patched_load(f: Any, *args: Any, **kwargs: Any) -> Any:
            kwargs['weights_only'] = False
            return original_load(f, *args, **kwargs)
        
        try:
            torch.load = patched_load
            self.model = YOLO(model_path)
            self.model.to(self.device)
        finally:
            torch.load = original_load
    
    def detect(self, frame: np.ndarray) -> List[Detection]:
        """Detect people in a video frame.
        
        Args:
            frame: Video frame as numpy array (HxWx3 BGR format)
            
        Returns:
            List of Detection objects for detected people
        """
        if frame is None or frame.size == 0:
            logger.warning("Invalid frame provided (None or empty)")
            return []
        
        try:
            # Run YOLOv8 inference
            results = self.model(
                frame,
                verbose=False,
                device=self.device,
                conf=self.confidence_threshold,
            )
            
            # Extract person detections
            detections = []
            
            if len(results) > 0:
                result = results[0]
                boxes = result.boxes
                
                for box in boxes:
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    
                    # Filter for person class only
                    if class_id == self.PERSON_CLASS_ID and confidence >= self.confidence_threshold:
                        # Extract bounding box (xyxy format)
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        
                        # Convert to (x, y, width, height)
                        bbox = BoundingBox(
                            x=float(x1),
                            y=float(y1),
                            width=float(x2 - x1),
                            height=float(y2 - y1),
                        )
                        
                        detection = Detection(bbox=bbox, confidence=confidence, class_id=class_id)
                        detections.append(detection)
            
            logger.debug(f"Detected {len(detections)} people in frame")
            return detections
            
        except Exception as e:
            logger.error(f"Detection failed: {e}")
            return []
    
    def detect_batch(self, frames: List[np.ndarray]) -> List[List[Detection]]:
        """Detect people in a batch of frames.
        
        Args:
            frames: List of video frames
            
        Returns:
            List of detection lists (one per frame)
        """
        if not frames:
            return []
        
        try:
            # Run batch inference
            results = self.model(
                frames,
                verbose=False,
                device=self.device,
                conf=self.confidence_threshold,
            )
            
            # Extract detections for each frame
            batch_detections = []
            
            for result in results:
                frame_detections = []
                boxes = result.boxes
                
                for box in boxes:
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    
                    if class_id == self.PERSON_CLASS_ID and confidence >= self.confidence_threshold:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        
                        bbox = BoundingBox(
                            x=float(x1),
                            y=float(y1),
                            width=float(x2 - x1),
                            height=float(y2 - y1),
                        )
                        
                        detection = Detection(bbox=bbox, confidence=confidence, class_id=class_id)
                        frame_detections.append(detection)
                
                batch_detections.append(frame_detections)
            
            logger.debug(f"Batch detection complete: {len(frames)} frames processed")
            return batch_detections
            
        except Exception as e:
            logger.error(f"Batch detection failed: {e}")
            return [[] for _ in frames]

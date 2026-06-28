"""ByteTrack Person Tracker for CV Pipeline.

This module provides multi-object tracking using the ByteTrack algorithm
with IoU-based matching for maintaining consistent track IDs across frames.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple

import numpy as np

from pipeline.detector import BoundingBox, Detection

# Configure logging
logger = logging.getLogger(__name__)


class TrackState(Enum):
    """Track state enumeration."""
    ACTIVE = "active"
    LOST = "lost"
    REMOVED = "removed"


@dataclass
class Position:
    """2D position with frame number."""
    x: float
    y: float
    frame_number: int


@dataclass
class Track:
    """Tracked object representation.
    
    Attributes:
        track_id: Unique track identifier
        bbox: Current bounding box
        frame_number: Last update frame number
        age: Frames since last detection
        hits: Total number of detections
        state: Current track state
        trajectory: Position history
    """
    track_id: int
    bbox: BoundingBox
    frame_number: int
    age: int = 0
    hits: int = 1
    state: TrackState = TrackState.ACTIVE
    trajectory: List[Position] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "track_id": self.track_id,
            "bbox": self.bbox.to_dict(),
            "frame_number": self.frame_number,
            "age": self.age,
            "hits": self.hits,
            "state": self.state.value,
        }


class PersonTracker:
    """ByteTrack-based person tracker.
    
    Tracks detected persons across video frames using IoU matching.
    Maintains consistent track IDs and handles occlusions gracefully.
    
    Attributes:
        max_age: Maximum frames to keep track without detection
        min_hits: Minimum hits before track is confirmed
        iou_threshold: IoU threshold for matching
        next_id: Next available track ID
        tracks: Active tracks dictionary
    """
    
    def __init__(
        self,
        max_age: int = 30,
        min_hits: int = 3,
        iou_threshold: float = 0.3,
    ):
        """Initialize person tracker.
        
        Args:
            max_age: Maximum frames to keep track without detection
            min_hits: Minimum detections before track is confirmed
            iou_threshold: IoU threshold for matching [0, 1]
            
        Raises:
            ValueError: If parameters are invalid
        """
        if max_age <= 0:
            raise ValueError(f"max_age must be positive, got {max_age}")
        
        if not (0 <= iou_threshold <= 1):
            raise ValueError(f"iou_threshold must be in [0, 1], got {iou_threshold}")
        
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.next_id = 1
        self.tracks: Dict[int, Track] = {}
        
        logger.info(f"PersonTracker initialized (max_age={max_age}, min_hits={min_hits}, iou_threshold={iou_threshold})")
    
    def update(self, detections: List[Detection], frame_number: int) -> List[Track]:
        """Update tracks with new detections.
        
        Args:
            detections: List of detections from current frame
            frame_number: Current frame number
            
        Returns:
            List of active tracks
        """
        logger.debug(f"Updating tracks: {len(detections)} detections, {len(self.tracks)} active tracks")
        
        # Handle empty detections
        if not detections:
            return self._age_tracks(frame_number)
        
        # Match detections to tracks
        matched_pairs, unmatched_detections = self._match_detections_to_tracks(detections)
        
        # Track which tracks were updated
        updated_track_ids = set()
        
        # Update matched tracks
        for track_id, detection in matched_pairs:
            self._update_track(track_id, detection, frame_number)
            updated_track_ids.add(track_id)
        
        # Create new tracks for unmatched detections
        for detection in unmatched_detections:
            track_id = self._create_track(detection, frame_number)
            updated_track_ids.add(track_id)
        
        # Age unmatched tracks
        self._age_unmatched_tracks(updated_track_ids, frame_number)
        
        # Remove old tracks
        self._remove_old_tracks()
        
        # Return confirmed tracks (hits >= min_hits)
        confirmed_tracks = [
            track for track in self.tracks.values()
            if track.hits >= self.min_hits
        ]
        
        logger.debug(f"Tracks updated: {len(confirmed_tracks)} confirmed, {len(self.tracks)} total")
        return confirmed_tracks
    
    def _match_detections_to_tracks(
        self,
        detections: List[Detection],
    ) -> Tuple[List[Tuple[int, Detection]], List[Detection]]:
        """Match detections to tracks using IoU.
        
        Args:
            detections: List of detections
            
        Returns:
            Tuple of (matched_pairs, unmatched_detections)
        """
        if not self.tracks:
            return [], detections
        
        # Calculate IoU matrix
        track_ids = list(self.tracks.keys())
        iou_matrix = np.zeros((len(detections), len(track_ids)))
        
        for i, detection in enumerate(detections):
            for j, track_id in enumerate(track_ids):
                track = self.tracks[track_id]
                iou_matrix[i, j] = self._compute_iou(detection.bbox, track.bbox)
        
        # Greedy matching
        matched_pairs = []
        matched_detection_indices = set()
        matched_track_indices = set()
        
        # Sort matches by IoU (highest first)
        matches = []
        for i in range(len(detections)):
            for j in range(len(track_ids)):
                if iou_matrix[i, j] > self.iou_threshold:
                    matches.append((i, j, iou_matrix[i, j]))
        
        matches.sort(key=lambda x: x[2], reverse=True)
        
        # Assign matches greedily
        for det_idx, track_idx, iou in matches:
            if det_idx not in matched_detection_indices and track_idx not in matched_track_indices:
                matched_pairs.append((track_ids[track_idx], detections[det_idx]))
                matched_detection_indices.add(det_idx)
                matched_track_indices.add(track_idx)
        
        # Unmatched detections
        unmatched_detections = [
            detections[i] for i in range(len(detections))
            if i not in matched_detection_indices
        ]
        
        logger.debug(f"Matching: {len(matched_pairs)} matched, {len(unmatched_detections)} unmatched")
        return matched_pairs, unmatched_detections
    
    def _compute_iou(self, bbox1: BoundingBox, bbox2: BoundingBox) -> float:
        """Compute IoU between two bounding boxes.
        
        Args:
            bbox1: First bounding box
            bbox2: Second bounding box
            
        Returns:
            IoU value [0, 1]
        """
        # Intersection coordinates
        x1_inter = max(bbox1.x, bbox2.x)
        y1_inter = max(bbox1.y, bbox2.y)
        x2_inter = min(bbox1.x + bbox1.width, bbox2.x + bbox2.width)
        y2_inter = min(bbox1.y + bbox1.height, bbox2.y + bbox2.height)
        
        # Intersection area
        inter_width = max(0, x2_inter - x1_inter)
        inter_height = max(0, y2_inter - y1_inter)
        inter_area = inter_width * inter_height
        
        # Union area
        bbox1_area = bbox1.width * bbox1.height
        bbox2_area = bbox2.width * bbox2.height
        union_area = bbox1_area + bbox2_area - inter_area
        
        if union_area == 0:
            return 0.0
        
        return inter_area / union_area
    
    def _update_track(self, track_id: int, detection: Detection, frame_number: int) -> None:
        """Update existing track with new detection.
        
        Args:
            track_id: Track ID
            detection: New detection
            frame_number: Current frame number
        """
        track = self.tracks[track_id]
        track.bbox = detection.bbox
        track.frame_number = frame_number
        track.age = 0
        track.hits += 1
        track.state = TrackState.ACTIVE
        
        # Update trajectory
        center_x = detection.bbox.x + detection.bbox.width / 2
        center_y = detection.bbox.y + detection.bbox.height / 2
        position = Position(x=center_x, y=center_y, frame_number=frame_number)
        track.trajectory.append(position)
    
    def _create_track(self, detection: Detection, frame_number: int) -> int:
        """Create new track from detection.
        
        Args:
            detection: Detection to create track from
            frame_number: Current frame number
            
        Returns:
            New track ID
        """
        track_id = self.next_id
        self.next_id += 1
        
        # Create track
        track = Track(
            track_id=track_id,
            bbox=detection.bbox,
            frame_number=frame_number,
            age=0,
            hits=1,
            state=TrackState.ACTIVE,
        )
        
        # Initial trajectory position
        center_x = detection.bbox.x + detection.bbox.width / 2
        center_y = detection.bbox.y + detection.bbox.height / 2
        position = Position(x=center_x, y=center_y, frame_number=frame_number)
        track.trajectory.append(position)
        
        self.tracks[track_id] = track
        logger.debug(f"New track created: {track_id}")
        
        return track_id
    
    def _age_unmatched_tracks(self, matched_track_ids: set, frame_number: int) -> None:
        """Age tracks that were not matched.
        
        Args:
            matched_track_ids: Set of track IDs that were matched
            frame_number: Current frame number
        """
        for track_id, track in self.tracks.items():
            if track_id not in matched_track_ids:
                track.age += 1
                track.state = TrackState.LOST
    
    def _age_tracks(self, frame_number: int) -> List[Track]:
        """Age all tracks when no detections present.
        
        Args:
            frame_number: Current frame number
            
        Returns:
            List of confirmed tracks
        """
        for track in self.tracks.values():
            track.age += 1
            track.state = TrackState.LOST
        
        self._remove_old_tracks()
        
        confirmed_tracks = [
            track for track in self.tracks.values()
            if track.hits >= self.min_hits
        ]
        
        return confirmed_tracks
    
    def _remove_old_tracks(self) -> None:
        """Remove tracks that exceed max_age."""
        tracks_to_remove = []
        
        for track_id, track in self.tracks.items():
            if track.age > self.max_age:
                track.state = TrackState.REMOVED
                tracks_to_remove.append(track_id)
        
        for track_id in tracks_to_remove:
            del self.tracks[track_id]
            logger.debug(f"Track removed: {track_id} (exceeded max_age)")
    
    def get_trajectory(self, track_id: int) -> List[Position]:
        """Get trajectory for a track.
        
        Args:
            track_id: Track ID
            
        Returns:
            List of positions
        """
        if track_id in self.tracks:
            return self.tracks[track_id].trajectory
        return []
    
    def reset(self) -> None:
        """Reset tracker state."""
        self.tracks.clear()
        self.next_id = 1
        logger.info("Tracker reset")

"""Event Generation for CV Pipeline.

This module transforms tracking data into structured events that
match the Store Intelligence Platform event schema.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from pipeline.tracker import Track
from pipeline.zone_manager import Zone, ZoneManager, ZoneType

# Configure logging
logger = logging.getLogger(__name__)


class EventType:
    """Event type constants."""
    ENTRY = "ENTRY"
    EXIT = "EXIT"
    ZONE_ENTER = "ZONE_ENTER"
    ZONE_EXIT = "ZONE_EXIT"
    ZONE_DWELL = "ZONE_DWELL"
    BILLING_QUEUE_JOIN = "BILLING_QUEUE_JOIN"
    BILLING_QUEUE_ABANDON = "BILLING_QUEUE_ABANDON"
    REENTRY = "REENTRY"


class Event:
    """Event representation matching API schema.
    
    Attributes:
        event_id: Unique event identifier (UUID)
        event_type: Type of event
        timestamp: ISO 8601 timestamp
        store_id: Store identifier
        track_id: Track identifier
        metadata: Event-specific metadata
    """
    
    def __init__(
        self,
        event_id: str,
        event_type: str,
        timestamp: str,
        store_id: str,
        track_id: int,
        metadata: dict,
    ):
        self.event_id = event_id
        self.event_type = event_type
        self.timestamp = timestamp
        self.store_id = store_id
        self.track_id = track_id
        self.metadata = metadata
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "store_id": self.store_id,
            "track_id": self.track_id,
            "metadata": self.metadata,
        }


class EventGenerator:
    """Generates events from tracking data.
    
    Tracks person movements across zones and generates appropriate
    events (ENTRY, EXIT, ZONE_ENTER, ZONE_EXIT, ZONE_DWELL, etc.)
    
    Attributes:
        store_id: Store identifier
        zone_manager: Zone manager instance
        fps: Video FPS for time calculations
        dwell_threshold_seconds: Threshold for ZONE_DWELL events
        track_state: Track state dictionary
        zone_state: Zone state dictionary
        exit_history: Exit history for reentry detection
        billing_queue_state: Billing queue state
    """
    
    def __init__(
        self,
        store_id: str,
        zone_manager: ZoneManager,
        fps: int = 30,
        dwell_threshold_seconds: float = 5.0,
        base_timestamp: Optional[datetime] = None,
    ):
        """Initialize event generator.
        
        Args:
            store_id: Store identifier
            zone_manager: Zone manager instance
            fps: Video FPS for timestamp calculation
            dwell_threshold_seconds: Threshold for dwell events
            base_timestamp: Base timestamp for frame-to-time conversion
        """
        self.store_id = store_id
        self.zone_manager = zone_manager
        self.fps = fps
        self.dwell_threshold_seconds = dwell_threshold_seconds
        self.base_timestamp = base_timestamp or datetime.now(timezone.utc)
        
        # State tracking
        self.track_state: Dict[int, int] = {}  # track_id -> last_seen_frame
        self.zone_state: Dict[int, dict] = {}  # track_id -> {zone_id, enter_frame, dwell_generated}
        self.exit_history: Dict[int, datetime] = {}  # track_id -> exit_timestamp
        self.billing_queue_state: Dict[int, dict] = {}  # track_id -> {enter_frame, queue_position}
        
        logger.info(f"EventGenerator initialized (store_id={store_id}, fps={fps}, dwell_threshold={dwell_threshold_seconds}s)")
    
    def process_tracks(self, tracks: List[Track], frame_number: int) -> List[Event]:
        """Process tracks and generate events.
        
        Args:
            tracks: List of current tracks
            frame_number: Current frame number
            
        Returns:
            List of generated events
        """
        events = []
        current_track_ids = {track.track_id for track in tracks}
        
        # 1. Detect ENTRY events (new tracks)
        for track in tracks:
            if track.track_id not in self.track_state:
                entry_event = self._generate_entry_event(track, frame_number)
                events.append(entry_event)
                
                # Check for reentry
                reentry_event = self._check_reentry(track, frame_number)
                if reentry_event:
                    events.append(reentry_event)
        
        # 2. Detect EXIT events (absent tracks)
        exit_events = self._detect_exit_events(current_track_ids, frame_number)
        events.extend(exit_events)
        
        # 3. Detect zone interactions
        for track in tracks:
            zone_events = self._detect_zone_interactions(track, frame_number)
            events.extend(zone_events)
        
        # 4. Update track state
        for track in tracks:
            self.track_state[track.track_id] = frame_number
        
        logger.debug(f"Frame {frame_number}: Generated {len(events)} events")
        return events
    
    def finalize(self) -> List[Event]:
        """Generate final EXIT events for remaining tracks.
        
        Returns:
            List of EXIT events
        """
        events = []
        
        for track_id, last_frame in list(self.track_state.items()):
            exit_event = self._generate_exit_event(track_id, last_frame)
            events.append(exit_event)
            
            # Handle zone exit
            if track_id in self.zone_state:
                zone_exit_event = self._generate_zone_exit_event(track_id, last_frame)
                events.append(zone_exit_event)
            
            # Handle billing queue abandonment
            if track_id in self.billing_queue_state:
                abandon_event = self._generate_billing_queue_abandon_event(track_id, last_frame)
                events.append(abandon_event)
        
        # Clear state
        self.track_state.clear()
        self.zone_state.clear()
        self.billing_queue_state.clear()
        
        logger.info(f"Finalized: Generated {len(events)} EXIT events")
        return events
    
    def _generate_entry_event(self, track: Track, frame_number: int) -> Event:
        """Generate ENTRY event."""
        event_id = str(uuid.uuid4())
        timestamp = self._frame_to_timestamp(frame_number)
        
        return Event(
            event_id=event_id,
            event_type=EventType.ENTRY,
            timestamp=timestamp,
            store_id=self.store_id,
            track_id=track.track_id,
            metadata={},
        )
    
    def _generate_exit_event(self, track_id: int, last_frame: int) -> Event:
        """Generate EXIT event."""
        event_id = str(uuid.uuid4())
        timestamp = self._frame_to_timestamp(last_frame)
        
        # Store exit timestamp for reentry detection
        self.exit_history[track_id] = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        return Event(
            event_id=event_id,
            event_type=EventType.EXIT,
            timestamp=timestamp,
            store_id=self.store_id,
            track_id=track_id,
            metadata={},
        )
    
    def _detect_exit_events(self, current_track_ids: set, frame_number: int) -> List[Event]:
        """Detect EXIT events for absent tracks."""
        events = []
        max_age = 30  # Frames
        
        absent_track_ids = set(self.track_state.keys()) - current_track_ids
        
        for track_id in absent_track_ids:
            last_seen = self.track_state[track_id]
            frames_absent = frame_number - last_seen
            
            if frames_absent > max_age:
                exit_event = self._generate_exit_event(track_id, last_seen)
                events.append(exit_event)
                
                # Handle zone exit
                if track_id in self.zone_state:
                    zone_exit_event = self._generate_zone_exit_event(track_id, last_seen)
                    events.append(zone_exit_event)
                    del self.zone_state[track_id]
                
                # Handle billing queue abandonment
                if track_id in self.billing_queue_state:
                    abandon_event = self._generate_billing_queue_abandon_event(track_id, last_seen)
                    events.append(abandon_event)
                
                # Remove from track state
                del self.track_state[track_id]
        
        return events
    
    def _check_reentry(self, track: Track, frame_number: int) -> Optional[Event]:
        """Check for REENTRY event."""
        current_timestamp = datetime.fromisoformat(
            self._frame_to_timestamp(frame_number).replace('Z', '+00:00')
        )
        reentry_threshold = 300  # seconds
        
        # Check exit history
        for prev_track_id, exit_timestamp in list(self.exit_history.items()):
            time_since_exit = (current_timestamp - exit_timestamp).total_seconds()
            
            if time_since_exit > reentry_threshold:
                del self.exit_history[prev_track_id]
                continue
            
            if 0 <= time_since_exit <= reentry_threshold:
                event_id = str(uuid.uuid4())
                timestamp = self._frame_to_timestamp(frame_number)
                immediate_return = time_since_exit < 60
                
                # Remove from exit history
                del self.exit_history[prev_track_id]
                
                return Event(
                    event_id=event_id,
                    event_type=EventType.REENTRY,
                    timestamp=timestamp,
                    store_id=self.store_id,
                    track_id=track.track_id,
                    metadata={
                        'time_since_last_exit_seconds': time_since_exit,
                        'immediate_return': immediate_return,
                        'previous_track_id': prev_track_id,
                    },
                )
        
        return None
    
    def _detect_zone_interactions(self, track: Track, frame_number: int) -> List[Event]:
        """Detect zone-related events."""
        events = []
        
        # Calculate track centroid
        centroid_x = track.bbox.x + track.bbox.width / 2
        centroid_y = track.bbox.y + track.bbox.height / 2
        
        # Get current zone
        current_zone = self.zone_manager.get_zone_at_point(centroid_x, centroid_y)
        
        # Get previous zone state
        previous_zone_id = None
        if track.track_id in self.zone_state:
            previous_zone_id = self.zone_state[track.track_id].get('zone_id')
        
        # Case 1: Entered new zone
        if current_zone and (previous_zone_id != current_zone.zone_id):
            # Exit previous zone if any
            if previous_zone_id:
                zone_exit_event = self._generate_zone_exit_event(track.track_id, frame_number)
                events.append(zone_exit_event)
            
            # Enter new zone
            zone_enter_event = self._generate_zone_enter_event(track, current_zone, frame_number)
            events.append(zone_enter_event)
            
            # Update zone state
            self.zone_state[track.track_id] = {
                'zone_id': current_zone.zone_id,
                'zone_name': current_zone.zone_name,
                'zone_type': current_zone.zone_type,
                'enter_frame': frame_number,
                'dwell_generated': False,
            }
            
            # Handle billing queue
            if current_zone.zone_type == ZoneType.BILLING_QUEUE:
                billing_join_event = self._generate_billing_queue_join_event(track, frame_number)
                events.append(billing_join_event)
        
        # Case 2: Exited zone
        elif not current_zone and previous_zone_id:
            zone_exit_event = self._generate_zone_exit_event(track.track_id, frame_number)
            events.append(zone_exit_event)
            
            # Check billing queue abandonment
            zone_type = self.zone_state[track.track_id].get('zone_type')
            if zone_type == ZoneType.BILLING_QUEUE:
                abandon_event = self._generate_billing_queue_abandon_event(track.track_id, frame_number)
                events.append(abandon_event)
            
            del self.zone_state[track.track_id]
        
        # Case 3: Still in same zone - check dwell
        elif current_zone and previous_zone_id == current_zone.zone_id:
            dwell_event = self._check_zone_dwell(track.track_id, frame_number)
            if dwell_event:
                events.append(dwell_event)
        
        return events
    
    def _generate_zone_enter_event(self, track: Track, zone: Zone, frame_number: int) -> Event:
        """Generate ZONE_ENTER event."""
        event_id = str(uuid.uuid4())
        timestamp = self._frame_to_timestamp(frame_number)
        
        return Event(
            event_id=event_id,
            event_type=EventType.ZONE_ENTER,
            timestamp=timestamp,
            store_id=self.store_id,
            track_id=track.track_id,
            metadata={
                'zone_id': zone.zone_id,
                'zone_name': zone.zone_name,
            },
        )
    
    def _generate_zone_exit_event(self, track_id: int, frame_number: int) -> Event:
        """Generate ZONE_EXIT event."""
        event_id = str(uuid.uuid4())
        timestamp = self._frame_to_timestamp(frame_number)
        
        zone_info = self.zone_state.get(track_id, {})
        zone_id = zone_info.get('zone_id', 'unknown')
        zone_name = zone_info.get('zone_name', 'unknown')
        enter_frame = zone_info.get('enter_frame', frame_number)
        
        duration_seconds = (frame_number - enter_frame) / self.fps
        
        return Event(
            event_id=event_id,
            event_type=EventType.ZONE_EXIT,
            timestamp=timestamp,
            store_id=self.store_id,
            track_id=track_id,
            metadata={
                'zone_id': zone_id,
                'zone_name': zone_name,
                'zone_duration_seconds': duration_seconds,
            },
        )
    
    def _check_zone_dwell(self, track_id: int, frame_number: int) -> Optional[Event]:
        """Check for ZONE_DWELL event."""
        zone_info = self.zone_state.get(track_id, {})
        enter_frame = zone_info.get('enter_frame')
        dwell_generated = zone_info.get('dwell_generated', False)
        
        if not enter_frame or dwell_generated:
            return None
        
        duration_seconds = (frame_number - enter_frame) / self.fps
        
        if duration_seconds >= self.dwell_threshold_seconds:
            event_id = str(uuid.uuid4())
            timestamp = self._frame_to_timestamp(frame_number)
            
            zone_id = zone_info.get('zone_id', 'unknown')
            zone_name = zone_info.get('zone_name', 'unknown')
            
            # Mark as generated
            self.zone_state[track_id]['dwell_generated'] = True
            
            return Event(
                event_id=event_id,
                event_type=EventType.ZONE_DWELL,
                timestamp=timestamp,
                store_id=self.store_id,
                track_id=track_id,
                metadata={
                    'zone_id': zone_id,
                    'zone_name': zone_name,
                    'dwell_duration_seconds': duration_seconds,
                },
            )
        
        return None
    
    def _generate_billing_queue_join_event(self, track: Track, frame_number: int) -> Event:
        """Generate BILLING_QUEUE_JOIN event."""
        event_id = str(uuid.uuid4())
        timestamp = self._frame_to_timestamp(frame_number)
        
        queue_position = len(self.billing_queue_state) + 1
        
        self.billing_queue_state[track.track_id] = {
            'enter_frame': frame_number,
            'queue_position': queue_position,
        }
        
        return Event(
            event_id=event_id,
            event_type=EventType.BILLING_QUEUE_JOIN,
            timestamp=timestamp,
            store_id=self.store_id,
            track_id=track.track_id,
            metadata={'queue_position': queue_position},
        )
    
    def _generate_billing_queue_abandon_event(self, track_id: int, frame_number: int) -> Event:
        """Generate BILLING_QUEUE_ABANDON event."""
        event_id = str(uuid.uuid4())
        timestamp = self._frame_to_timestamp(frame_number)
        
        queue_info = self.billing_queue_state.get(track_id, {})
        enter_frame = queue_info.get('enter_frame', frame_number)
        
        wait_seconds = (frame_number - enter_frame) / self.fps
        high_wait_time = wait_seconds > 300
        
        # Remove from queue state
        if track_id in self.billing_queue_state:
            del self.billing_queue_state[track_id]
        
        return Event(
            event_id=event_id,
            event_type=EventType.BILLING_QUEUE_ABANDON,
            timestamp=timestamp,
            store_id=self.store_id,
            track_id=track_id,
            metadata={
                'queue_wait_time_seconds': wait_seconds,
                'high_wait_time': high_wait_time,
            },
        )
    
    def _frame_to_timestamp(self, frame_number: int) -> str:
        """Convert frame number to ISO 8601 timestamp.
        
        Args:
            frame_number: Frame number
            
        Returns:
            ISO 8601 timestamp string with 'Z' suffix
        """
        seconds = frame_number / self.fps
        timestamp = self.base_timestamp + timedelta(seconds=seconds)
        return timestamp.isoformat().replace('+00:00', 'Z')

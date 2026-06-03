"""Property-based tests for EventGenerator using Hypothesis."""

import pytest
from datetime import datetime
from hypothesis import given, settings, strategies as st
from hypothesis import assume

from src.event_generator import EventGenerator
from src.models import BoundingBox, EventType, Point, Track, TrackState, Zone, ZoneType


# Custom strategies for generating test data

@st.composite
def valid_bbox_strategy(draw):
    """Generate valid bounding boxes."""
    x = draw(st.floats(min_value=0, max_value=1000))
    y = draw(st.floats(min_value=0, max_value=1000))
    width = draw(st.floats(min_value=10, max_value=200))
    height = draw(st.floats(min_value=10, max_value=200))
    return BoundingBox(x=x, y=y, width=width, height=height)


@st.composite
def track_strategy(draw):
    """Generate valid Track objects."""
    track_id = draw(st.integers(min_value=1, max_value=1000))
    bbox = draw(valid_bbox_strategy())
    frame_number = draw(st.integers(min_value=0, max_value=10000))
    age = draw(st.integers(min_value=0, max_value=50))
    state = draw(st.sampled_from([TrackState.ACTIVE, TrackState.LOST]))
    
    return Track(
        track_id=track_id,
        bbox=bbox,
        frame_number=frame_number,
        age=age,
        state=state
    )


@st.composite
def zone_strategy(draw):
    """Generate valid Zone objects."""
    zone_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    zone_name = draw(st.text(min_size=1, max_size=50))
    zone_type = draw(st.sampled_from([ZoneType.GENERAL, ZoneType.BILLING_QUEUE]))
    
    # Generate a simple rectangular polygon
    x = draw(st.floats(min_value=0, max_value=800))
    y = draw(st.floats(min_value=0, max_value=800))
    width = draw(st.floats(min_value=50, max_value=200))
    height = draw(st.floats(min_value=50, max_value=200))
    
    polygon = [
        Point(x=x, y=y),
        Point(x=x + width, y=y),
        Point(x=x + width, y=y + height),
        Point(x=x, y=y + height)
    ]
    
    return Zone(
        zone_id=zone_id,
        zone_name=zone_name,
        polygon=polygon,
        zone_type=zone_type
    )


def get_sample_zones():
    """Create sample zones for testing."""
    return [
        Zone(
            zone_id="cosmetics",
            zone_name="Cosmetics Section",
            polygon=[
                Point(x=100, y=100),
                Point(x=300, y=100),
                Point(x=300, y=300),
                Point(x=100, y=300)
            ],
            zone_type=ZoneType.GENERAL
        ),
        Zone(
            zone_id="billing_queue",
            zone_name="Billing Queue",
            polygon=[
                Point(x=400, y=400),
                Point(x=600, y=400),
                Point(x=600, y=600),
                Point(x=400, y=600)
            ],
            zone_type=ZoneType.BILLING_QUEUE
        )
    ]


# Property 2: Event Pairing Invariant
@pytest.mark.property
@settings(max_examples=20, deadline=None)
@given(
    tracks=st.lists(track_strategy(), min_size=1, max_size=10, unique_by=lambda t: t.track_id),
    frame_numbers=st.lists(st.integers(min_value=1, max_value=1000), min_size=2, max_size=50)
)
def test_property_event_pairing_invariant(tracks, frame_numbers):
    """Property 2: Every ENTRY event must have a corresponding EXIT event.
    
    When we finalize the event generator, every track that entered
    must have an exit event.
    """
    sample_zones = get_sample_zones()
    generator = EventGenerator(
        store_id="store_001",
        zones=sample_zones,
        logger=None,
        fps=30
    )
    
    all_events = []
    
    # Process tracks across multiple frames
    for i, frame_number in enumerate(sorted(frame_numbers)):
        # Alternate between showing and hiding tracks
        active_tracks = tracks if i % 2 == 0 else []
        events = generator.process_tracks(active_tracks, frame_number)
        all_events.extend(events)
    
    # Finalize to ensure all tracks exit
    final_events = generator.finalize()
    all_events.extend(final_events)
    
    # Count ENTRY and EXIT events per track
    track_entries = {}
    track_exits = {}
    
    for event in all_events:
        if event.event_type == EventType.ENTRY:
            track_entries[event.track_id] = track_entries.get(event.track_id, 0) + 1
        elif event.event_type == EventType.EXIT:
            track_exits[event.track_id] = track_exits.get(event.track_id, 0) + 1
    
    # Property: Every track with an ENTRY must have at least one EXIT
    for track_id, entry_count in track_entries.items():
        assert track_id in track_exits, f"Track {track_id} has ENTRY but no EXIT"
        assert track_exits[track_id] > 0, f"Track {track_id} has {entry_count} entries but no exits"


# Property 9: Entry Event Generation
@pytest.mark.property
@settings(max_examples=20, deadline=None)
@given(track=track_strategy(), frame_number=st.integers(min_value=1, max_value=1000))
def test_property_entry_event_generation(track, frame_number):
    """Property 9: Every new track must generate exactly one ENTRY event.
    
    When a track appears for the first time, exactly one ENTRY event
    should be generated with correct track_id and store_id.
    """
    sample_zones = get_sample_zones()
    generator = EventGenerator(
        store_id="store_001",
        zones=sample_zones,
        logger=None,
        fps=30
    )
    
    events = generator.process_tracks([track], frame_number)
    
    entry_events = [e for e in events if e.event_type == EventType.ENTRY]
    
    # Property: Exactly one ENTRY event generated
    assert len(entry_events) == 1, f"Expected 1 ENTRY event, got {len(entry_events)}"
    
    entry_event = entry_events[0]
    
    # Property: ENTRY event has correct attributes
    assert entry_event.track_id == track.track_id
    assert entry_event.store_id == "store_001"
    assert entry_event.event_id is not None
    assert len(entry_event.event_id) > 0
    assert isinstance(entry_event.timestamp, datetime)


# Property 10: Exit Event Generation
@pytest.mark.property
@settings(max_examples=20, deadline=None)
@given(
    track=track_strategy(),
    entry_frame=st.integers(min_value=1, max_value=100),
    absence_frames=st.integers(min_value=31, max_value=100)
)
def test_property_exit_event_generation(track, entry_frame, absence_frames):
    """Property 10: Tracks absent > max_age frames must generate EXIT event.
    
    When a track is absent for more than 30 frames (max_age), an EXIT
    event must be generated.
    """
    sample_zones = get_sample_zones()
    generator = EventGenerator(
        store_id="store_001",
        zones=sample_zones,
        logger=None,
        fps=30
    )
    
    # Track appears
    generator.process_tracks([track], entry_frame)
    
    # Track disappears for more than max_age frames
    exit_frame = entry_frame + absence_frames
    events = generator.process_tracks([], exit_frame)
    
    exit_events = [e for e in events if e.event_type == EventType.EXIT]
    
    # Property: EXIT event generated after max_age absence
    assert len(exit_events) >= 1, "EXIT event should be generated after max_age absence"
    
    # Find exit event for our track
    track_exit_events = [e for e in exit_events if e.track_id == track.track_id]
    assert len(track_exit_events) == 1, f"Expected 1 EXIT event for track {track.track_id}"
    
    exit_event = track_exit_events[0]
    assert exit_event.store_id == "store_001"
    assert exit_event.event_id is not None


# Property 11: Event ID Uniqueness
@pytest.mark.property
@settings(max_examples=20, deadline=None)
@given(
    tracks=st.lists(track_strategy(), min_size=5, max_size=20, unique_by=lambda t: t.track_id),
    frame_numbers=st.lists(st.integers(min_value=1, max_value=500), min_size=10, max_size=50)
)
def test_property_event_id_uniqueness(tracks, frame_numbers):
    """Property 11: All event_ids must be globally unique.
    
    No two events should ever have the same event_id, regardless
    of event type, track, or timing.
    """
    sample_zones = get_sample_zones()
    generator = EventGenerator(
        store_id="store_001",
        zones=sample_zones,
        logger=None,
        fps=30
    )
    
    all_events = []
    
    # Process multiple frames with varying tracks
    for i, frame_number in enumerate(sorted(frame_numbers)):
        # Vary which tracks are active
        active_tracks = tracks[i % len(tracks):(i % len(tracks)) + 3]
        events = generator.process_tracks(active_tracks, frame_number)
        all_events.extend(events)
    
    # Finalize
    final_events = generator.finalize()
    all_events.extend(final_events)
    
    # Property: All event IDs are unique
    event_ids = [e.event_id for e in all_events]
    unique_event_ids = set(event_ids)
    
    assert len(event_ids) == len(unique_event_ids), \
        f"Found {len(event_ids) - len(unique_event_ids)} duplicate event IDs"


# Property 12: Zone Boundary Detection
@pytest.mark.property
@settings(max_examples=20, deadline=None)
@given(
    track_id=st.integers(min_value=1, max_value=100),
    frame_number=st.integers(min_value=1, max_value=1000)
)
def test_property_zone_boundary_detection(track_id, frame_number):
    """Property 12: Track entering a zone must generate ZONE_ENTER event.
    
    When a track's centroid moves inside a zone's polygon, a ZONE_ENTER
    event must be generated with correct zone information.
    """
    sample_zones = get_sample_zones()
    generator = EventGenerator(
        store_id="store_001",
        zones=sample_zones,
        logger=None,
        fps=30
    )
    
    # Create track with centroid inside cosmetics zone (100-300, 100-300)
    # Centroid will be at bbox center: x + width/2, y + height/2
    track_inside_zone = Track(
        track_id=track_id,
        bbox=BoundingBox(x=150.0, y=150.0, width=50.0, height=80.0),  # centroid at (175, 190)
        frame_number=frame_number,
        age=0,
        state=TrackState.ACTIVE
    )
    
    events = generator.process_tracks([track_inside_zone], frame_number)
    
    zone_enter_events = [e for e in events if e.event_type == EventType.ZONE_ENTER]
    
    # Property: ZONE_ENTER event generated when track enters zone
    assert len(zone_enter_events) >= 1, "ZONE_ENTER event should be generated"
    
    # Check zone_enter event has correct metadata
    zone_enter = zone_enter_events[0]
    assert 'zone_id' in zone_enter.metadata
    assert 'zone_name' in zone_enter.metadata
    assert zone_enter.track_id == track_id


# Property 13: Zone Dwell Event Generation
@pytest.mark.property
@settings(max_examples=20, deadline=None)
@given(
    track_id=st.integers(min_value=1, max_value=100),
    entry_frame=st.integers(min_value=1, max_value=100),
    dwell_frames=st.integers(min_value=151, max_value=300)  # > 5 seconds at 30 fps
)
def test_property_zone_dwell_generation(track_id, entry_frame, dwell_frames):
    """Property 13: Track dwelling in zone > 5s must generate ZONE_DWELL event.
    
    When a track remains in a zone for more than 5 seconds (150 frames),
    a ZONE_DWELL event must be generated.
    """
    sample_zones = get_sample_zones()
    generator = EventGenerator(
        store_id="store_001",
        zones=sample_zones,
        logger=None,
        fps=30
    )
    
    # Track inside cosmetics zone
    track_in_zone = Track(
        track_id=track_id,
        bbox=BoundingBox(x=150.0, y=150.0, width=50.0, height=80.0),
        frame_number=entry_frame,
        age=0,
        state=TrackState.ACTIVE
    )
    
    all_events = []
    
    # Track enters zone
    events = generator.process_tracks([track_in_zone], entry_frame)
    all_events.extend(events)
    
    # Track remains in zone for dwell_frames
    for frame_offset in range(1, dwell_frames + 1):
        current_frame = entry_frame + frame_offset
        track_in_zone.frame_number = current_frame
        events = generator.process_tracks([track_in_zone], current_frame)
        all_events.extend(events)
    
    dwell_events = [e for e in all_events if e.event_type == EventType.ZONE_DWELL]
    
    # Property: ZONE_DWELL event generated when track dwells > 5 seconds
    assert len(dwell_events) >= 1, "ZONE_DWELL event should be generated after 5 seconds"
    
    dwell_event = dwell_events[0]
    assert dwell_event.track_id == track_id
    assert 'dwell_duration_seconds' in dwell_event.metadata
    assert dwell_event.metadata['dwell_duration_seconds'] >= 5.0


# Property 14: Billing Queue Event Generation
@pytest.mark.property
@settings(max_examples=20, deadline=None)
@given(
    track_id=st.integers(min_value=1, max_value=100),
    frame_number=st.integers(min_value=1, max_value=1000)
)
def test_property_billing_queue_event_generation(track_id, frame_number):
    """Property 14: Track entering BILLING_QUEUE zone must generate events.
    
    When a track enters a BILLING_QUEUE zone, both ZONE_ENTER and
    BILLING_QUEUE_JOIN events must be generated.
    """
    sample_zones = get_sample_zones()
    generator = EventGenerator(
        store_id="store_001",
        zones=sample_zones,
        logger=None,
        fps=30
    )
    
    # Track inside billing queue zone (400-600, 400-600)
    track_in_billing = Track(
        track_id=track_id,
        bbox=BoundingBox(x=450.0, y=450.0, width=50.0, height=80.0),  # centroid at (475, 490)
        frame_number=frame_number,
        age=0,
        state=TrackState.ACTIVE
    )
    
    events = generator.process_tracks([track_in_billing], frame_number)
    
    zone_enter_events = [e for e in events if e.event_type == EventType.ZONE_ENTER]
    billing_join_events = [e for e in events if e.event_type == EventType.BILLING_QUEUE_JOIN]
    
    # Property: Both ZONE_ENTER and BILLING_QUEUE_JOIN events generated
    assert len(zone_enter_events) >= 1, "ZONE_ENTER event should be generated"
    assert len(billing_join_events) == 1, "BILLING_QUEUE_JOIN event should be generated"
    
    billing_event = billing_join_events[0]
    assert billing_event.track_id == track_id
    assert 'queue_position' in billing_event.metadata
    assert billing_event.metadata['queue_position'] >= 1


# Property 15: High Wait Time Flagging
@pytest.mark.property
@settings(max_examples=20, deadline=None)
@given(
    track_id=st.integers(min_value=1, max_value=100),
    entry_frame=st.integers(min_value=1, max_value=100),
    wait_seconds=st.integers(min_value=301, max_value=400)  # > 300 seconds
)
def test_property_high_wait_time_flagging(track_id, entry_frame, wait_seconds):
    """Property 15: Queue wait time > 300s must flag high_wait_time.
    
    When a track abandons the billing queue after waiting more than
    300 seconds, the BILLING_QUEUE_ABANDON event must have
    high_wait_time=True.
    
    Note: Wait time is calculated from last_seen frame, so track must
    remain visible in the queue for the wait duration.
    """
    sample_zones = get_sample_zones()
    generator = EventGenerator(
        store_id="store_001",
        zones=sample_zones,
        logger=None,
        fps=30
    )
    
    # Track enters billing queue
    track_in_billing = Track(
        track_id=track_id,
        bbox=BoundingBox(x=450.0, y=450.0, width=50.0, height=80.0),
        frame_number=entry_frame,
        age=0,
        state=TrackState.ACTIVE
    )
    
    generator.process_tracks([track_in_billing], entry_frame)
    
    # Track remains in billing queue for wait_seconds
    wait_frames = wait_seconds * 30  # fps = 30
    last_frame_in_queue = entry_frame + wait_frames
    
    # Update track position to show it's still in queue
    track_in_billing.frame_number = last_frame_in_queue
    generator.process_tracks([track_in_billing], last_frame_in_queue)
    
    # Track exits billing queue (becomes absent for > max_age frames)
    exit_detection_frame = last_frame_in_queue + 31  # > max_age
    events = generator.process_tracks([], exit_detection_frame)
    
    abandon_events = [e for e in events if e.event_type == EventType.BILLING_QUEUE_ABANDON]
    
    # Property: high_wait_time flag is True when wait > 300 seconds
    assert len(abandon_events) >= 1, "BILLING_QUEUE_ABANDON event should be generated"
    
    abandon_event = abandon_events[0]
    assert 'high_wait_time' in abandon_event.metadata
    assert 'queue_wait_time_seconds' in abandon_event.metadata
    
    # Wait time should be approximately wait_seconds
    actual_wait = abandon_event.metadata['queue_wait_time_seconds']
    assert actual_wait >= 300, f"Wait time should be >= 300s, got {actual_wait}s"
    assert abandon_event.metadata['high_wait_time'] is True, \
        f"high_wait_time should be True for wait time {actual_wait}s"


# Property 16: Reentry Detection and Classification
@pytest.mark.property
@settings(max_examples=20, deadline=None)
@given(
    track_id_1=st.integers(min_value=1, max_value=50),
    track_id_2=st.integers(min_value=51, max_value=100),
    entry_frame=st.integers(min_value=1, max_value=100),
    exit_frame_offset=st.integers(min_value=31, max_value=50),
    reentry_seconds=st.integers(min_value=1, max_value=270)  # Account for max_age delay
)
def test_property_reentry_detection(track_id_1, track_id_2, entry_frame, exit_frame_offset, reentry_seconds):
    """Property 16: Track reentry within 300s must generate REENTRY event.
    
    When a new track appears within 300 seconds of a previous EXIT,
    a REENTRY event must be generated with correct metadata.
    
    Note: EXIT timestamp is based on last_seen_frame, not detection frame.
    So we need to account for max_age (30 frames) delay in detection.
    """
    sample_zones = get_sample_zones()
    generator = EventGenerator(
        store_id="store_001",
        zones=sample_zones,
        logger=None,
        fps=30
    )
    
    # First track enters
    track1 = Track(
        track_id=track_id_1,
        bbox=BoundingBox(x=50.0, y=50.0, width=50.0, height=80.0),
        frame_number=entry_frame,
        age=0,
        state=TrackState.ACTIVE
    )
    
    generator.process_tracks([track1], entry_frame)
    
    # First track exits (absent for > max_age frames)
    exit_frame = entry_frame + exit_frame_offset
    generator.process_tracks([], exit_frame)
    
    # Second track enters within 300 seconds of track1's LAST_SEEN time (entry_frame)
    # NOT within 300s of exit detection time
    reentry_frames = reentry_seconds * 30  # fps = 30
    reentry_frame = entry_frame + reentry_frames  # Calculate from last_seen, not exit_frame
    
    track2 = Track(
        track_id=track_id_2,
        bbox=BoundingBox(x=60.0, y=60.0, width=50.0, height=80.0),
        frame_number=reentry_frame,
        age=0,
        state=TrackState.ACTIVE
    )
    
    events = generator.process_tracks([track2], reentry_frame)
    
    reentry_events = [e for e in events if e.event_type == EventType.REENTRY]
    
    # Property: REENTRY event generated when new track appears within 300s of previous exit
    assert len(reentry_events) >= 1, f"REENTRY event should be generated within 300s (reentry_seconds={reentry_seconds})"
    
    reentry_event = reentry_events[0]
    assert reentry_event.track_id == track_id_2
    assert 'time_since_last_exit_seconds' in reentry_event.metadata
    assert 'immediate_return' in reentry_event.metadata
    assert reentry_event.metadata['immediate_return'] is True
    assert 'previous_track_id' in reentry_event.metadata


# Property 17: ISO 8601 Timestamp Format
@pytest.mark.property
@settings(max_examples=20, deadline=None)
@given(
    tracks=st.lists(track_strategy(), min_size=1, max_size=5, unique_by=lambda t: t.track_id),
    frame_number=st.integers(min_value=1, max_value=1000)
)
def test_property_iso8601_timestamp_format(tracks, frame_number):
    """Property 17: All event timestamps must be in ISO 8601 format.
    
    All events must have timestamps that are valid datetime objects
    with timezone information (UTC).
    """
    sample_zones = get_sample_zones()
    generator = EventGenerator(
        store_id="store_001",
        zones=sample_zones,
        logger=None,
        fps=30
    )
    
    events = generator.process_tracks(tracks, frame_number)
    
    # Property: All timestamps are datetime objects with timezone
    for event in events:
        assert isinstance(event.timestamp, datetime), \
            f"Event timestamp must be datetime object, got {type(event.timestamp)}"
        
        # Check that timestamp has timezone info
        assert event.timestamp.tzinfo is not None, \
            "Event timestamp must have timezone information"
        
        # Check that timestamp can be formatted as ISO 8601
        iso_string = event.timestamp.isoformat()
        assert 'T' in iso_string, "ISO 8601 format must contain 'T' separator"
        assert len(iso_string) > 10, "ISO 8601 format must include time component"

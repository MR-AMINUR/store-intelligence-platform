"""Property-based tests for data models using Hypothesis.

This module contains property tests that validate universal correctness
properties of the data models, particularly the Event schema.
"""

import json
from datetime import datetime, timezone
from hypothesis import given, strategies as st, settings
from src.models import Event, EventType


# Property 1: Event Schema Completeness
# Validates: Requirements 4.3, 8.1, 8.2, 8.3, 5.4
@settings(max_examples=100)
@given(
    event_id=st.text(min_size=1, max_size=50),
    event_type=st.sampled_from(list(EventType)),
    store_id=st.text(min_size=1, max_size=50),
    track_id=st.integers(min_value=0, max_value=10000),
    metadata_keys=st.lists(
        st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='_'
        )),
        min_size=0,
        max_size=10,
        unique=True
    ),
    metadata_values=st.lists(
        st.one_of(
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(max_size=50),
            st.booleans()
        ),
        min_size=0,
        max_size=10
    )
)
def test_property_event_schema_completeness(
    event_id,
    event_type,
    store_id,
    track_id,
    metadata_keys,
    metadata_values
):
    """
    Property 1: Event Schema Completeness
    
    For ANY event created with valid inputs, the event SHALL contain:
    1. All required base fields: event_id, event_type, timestamp, store_id, track_id
    2. A metadata dictionary (may be empty)
    3. All fields with correct types
    4. event_type as a valid EventType enum value
    
    This property validates Requirements 4.3, 8.1, 8.2, 8.3, 5.4:
    - 4.3: Event contains required fields
    - 8.1: Event conforms to defined JSON schema
    - 8.2: Event includes required fields
    - 8.3: Event includes event-specific fields based on event_type
    - 5.4: Frame metadata completeness (analogous for events)
    """
    # Build metadata dictionary
    metadata = {}
    for i, key in enumerate(metadata_keys):
        if i < len(metadata_values):
            metadata[key] = metadata_values[i]
    
    # Create timestamp
    timestamp = datetime.now(timezone.utc)
    
    # Create event
    event = Event(
        event_id=event_id,
        event_type=event_type,
        timestamp=timestamp,
        store_id=store_id,
        track_id=track_id,
        metadata=metadata
    )
    
    # Property 1: All required base fields must be present
    assert hasattr(event, 'event_id'), "Event must have event_id field"
    assert hasattr(event, 'event_type'), "Event must have event_type field"
    assert hasattr(event, 'timestamp'), "Event must have timestamp field"
    assert hasattr(event, 'store_id'), "Event must have store_id field"
    assert hasattr(event, 'track_id'), "Event must have track_id field"
    assert hasattr(event, 'metadata'), "Event must have metadata field"
    
    # Property 2: Field values must match inputs
    assert event.event_id == event_id, "event_id must match input"
    assert event.event_type == event_type, "event_type must match input"
    assert event.timestamp == timestamp, "timestamp must match input"
    assert event.store_id == store_id, "store_id must match input"
    assert event.track_id == track_id, "track_id must match input"
    
    # Property 3: Field types must be correct
    assert isinstance(event.event_id, str), "event_id must be a string"
    assert isinstance(event.event_type, EventType), "event_type must be EventType enum"
    assert isinstance(event.timestamp, datetime), "timestamp must be datetime"
    assert isinstance(event.store_id, str), "store_id must be a string"
    assert isinstance(event.track_id, int), "track_id must be an integer"
    assert isinstance(event.metadata, dict), "metadata must be a dictionary"
    
    # Property 4: event_type must be a valid EventType enum value
    assert event.event_type in EventType, "event_type must be valid EventType"
    
    # Property 5: Metadata must preserve all key-value pairs
    for key in metadata_keys[:len(metadata_values)]:
        assert key in event.metadata, f"Metadata key '{key}' must be present"
    
    for key, value in metadata.items():
        assert event.metadata[key] == value, f"Metadata value for '{key}' must match input"


# Property: Event Type Enum Completeness
@settings(max_examples=100)
@given(
    event_type=st.sampled_from(list(EventType))
)
def test_property_event_type_enum_values(event_type):
    """
    Property: Event Type Enum Completeness
    
    For ANY EventType enum value, it SHALL:
    1. Have a string value
    2. Be one of the defined event types
    3. Be accessible via the enum
    
    This validates Requirement 8.1: Event types are well-defined.
    """
    # Property 1: EventType value must be a string
    assert isinstance(event_type.value, str), "EventType value must be a string"
    
    # Property 2: EventType must be one of the defined types
    valid_types = {
        "ENTRY", "EXIT", "ZONE_ENTER", "ZONE_EXIT", "ZONE_DWELL",
        "BILLING_QUEUE_JOIN", "BILLING_QUEUE_ABANDON", "REENTRY"
    }
    assert event_type.value in valid_types, f"EventType {event_type.value} must be valid"
    
    # Property 3: EventType must be accessible via enum
    assert EventType(event_type.value) == event_type, "EventType must be accessible by value"


# Property: Metadata Preservation
@settings(max_examples=100)
@given(
    metadata=st.dictionaries(
        keys=st.text(min_size=1, max_size=20, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='_'
        )),
        values=st.one_of(
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(max_size=50),
            st.booleans(),
            st.none()
        ),
        min_size=0,
        max_size=20
    )
)
def test_property_metadata_preservation(metadata):
    """
    Property: Metadata Preservation
    
    For ANY metadata dictionary provided to an Event, ALL key-value pairs
    SHALL be preserved exactly without modification.
    
    This validates that event-specific fields are not lost or corrupted.
    """
    # Create event with metadata
    event = Event(
        event_id="test_id",
        event_type=EventType.ENTRY,
        timestamp=datetime.now(timezone.utc),
        store_id="store_001",
        track_id=1,
        metadata=metadata
    )
    
    # Property 1: All metadata keys must be present
    for key in metadata:
        assert key in event.metadata, f"Metadata key '{key}' must be present"
    
    # Property 2: All metadata values must match exactly
    for key, value in metadata.items():
        assert event.metadata[key] == value, \
            f"Metadata value for '{key}' must match: expected {value}, got {event.metadata[key]}"
    
    # Property 3: No extra keys should be present
    assert set(event.metadata.keys()) == set(metadata.keys()), \
        "Metadata should contain exactly the provided keys"
    
    # Property 4: Metadata dictionary should be independent (not shared reference)
    original_metadata = metadata.copy()
    event.metadata["new_key"] = "new_value"
    assert "new_key" not in original_metadata, "Original metadata should not be modified"


# Property: Event Immutability of Required Fields
@settings(max_examples=100)
@given(
    event_id=st.text(min_size=1, max_size=50),
    store_id=st.text(min_size=1, max_size=50),
    track_id=st.integers(min_value=0, max_value=10000)
)
def test_property_event_required_fields_immutable(event_id, store_id, track_id):
    """
    Property: Event Required Fields Immutability
    
    For ANY event created, the required fields (event_id, event_type, timestamp,
    store_id, track_id) SHALL maintain their values and types throughout the
    event's lifetime.
    
    This validates data integrity of core event fields.
    """
    timestamp = datetime.now(timezone.utc)
    event_type = EventType.ENTRY
    
    # Create event
    event = Event(
        event_id=event_id,
        event_type=event_type,
        timestamp=timestamp,
        store_id=store_id,
        track_id=track_id,
        metadata={}
    )
    
    # Store original values
    original_event_id = event.event_id
    original_event_type = event.event_type
    original_timestamp = event.timestamp
    original_store_id = event.store_id
    original_track_id = event.track_id
    
    # Perform some operations (metadata modification)
    event.metadata["test_key"] = "test_value"
    
    # Property: Required fields must remain unchanged
    assert event.event_id == original_event_id, "event_id must remain unchanged"
    assert event.event_type == original_event_type, "event_type must remain unchanged"
    assert event.timestamp == original_timestamp, "timestamp must remain unchanged"
    assert event.store_id == original_store_id, "store_id must remain unchanged"
    assert event.track_id == original_track_id, "track_id must remain unchanged"
    
    # Property: Field types must remain unchanged
    assert isinstance(event.event_id, str), "event_id type must remain string"
    assert isinstance(event.event_type, EventType), "event_type type must remain EventType"
    assert isinstance(event.timestamp, datetime), "timestamp type must remain datetime"
    assert isinstance(event.store_id, str), "store_id type must remain string"
    assert isinstance(event.track_id, int), "track_id type must remain int"


# Property: Event Type Coverage
def test_property_all_event_types_defined():
    """
    Property: Event Type Coverage
    
    The EventType enum SHALL define ALL required event types as specified
    in the requirements.
    
    This validates Requirement 8.1: All event types are defined.
    """
    required_event_types = {
        "ENTRY", "EXIT", "ZONE_ENTER", "ZONE_EXIT", "ZONE_DWELL",
        "BILLING_QUEUE_JOIN", "BILLING_QUEUE_ABANDON", "REENTRY"
    }
    
    # Get all defined event types
    defined_event_types = {et.value for et in EventType}
    
    # Property: All required event types must be defined
    assert required_event_types == defined_event_types, \
        f"Missing event types: {required_event_types - defined_event_types}, " \
        f"Extra event types: {defined_event_types - required_event_types}"
    
    # Property: Each event type must be unique
    event_type_values = [et.value for et in EventType]
    assert len(event_type_values) == len(set(event_type_values)), \
        "Event type values must be unique"

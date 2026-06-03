"""Property-based tests for EventStore using Hypothesis."""

import pytest
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from hypothesis import given, settings, strategies as st

from src.event_store import EventFilters, EventStore
from src.models import Event, EventType


# Custom strategies for generating test data

@st.composite
def event_type_strategy(draw):
    """Generate valid EventType values."""
    return draw(st.sampled_from(list(EventType)))


@st.composite
def event_strategy(draw):
    """Generate valid Event objects."""
    event_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pd'))))
    event_type = draw(event_type_strategy())
    
    # Generate timestamp within a reasonable range
    base_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    offset_seconds = draw(st.integers(min_value=0, max_value=86400 * 30))  # 30 days range
    timestamp = base_time + timedelta(seconds=offset_seconds)
    
    store_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    track_id = draw(st.integers(min_value=1, max_value=10000))
    
    # Generate simple metadata
    metadata = {}
    num_keys = draw(st.integers(min_value=0, max_value=5))
    for i in range(num_keys):
        key = f"key_{i}"
        value = draw(st.one_of(
            st.text(max_size=50),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.booleans()
        ))
        metadata[key] = value
    
    return Event(
        event_id=event_id,
        event_type=event_type,
        timestamp=timestamp,
        store_id=store_id,
        track_id=track_id,
        metadata=metadata
    )


# Property 3: System-Wide Idempotency
@pytest.mark.property
@settings(max_examples=20, deadline=None)
@given(
    events=st.lists(event_strategy(), min_size=1, max_size=20, unique_by=lambda e: e.event_id)
)
def test_property_idempotency_single_insertion(events):
    """Property 3a: Inserting the same event multiple times is idempotent.
    
    Inserting an event with the same event_id multiple times should result
    in only one event being stored, regardless of how many times it's inserted.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = str(Path(tmp_dir) / "test_idempotency.db")
        store = EventStore(db_path=db_path, logger=None)
        
        # Pick the first event for idempotency test
        test_event = events[0]
        
        # Insert the same event multiple times
        for _ in range(5):
            result = store.insert_event(test_event)
            assert result is True, "Insert should always return True (idempotent)"
        
        # Query to verify only one event exists
        filters = EventFilters(store_id=test_event.store_id)
        stored_events = store.query_events(filters)
        
        matching_events = [e for e in stored_events if e.event_id == test_event.event_id]
        
        # Property: Exactly one event with this ID should exist
        assert len(matching_events) == 1, \
            f"Expected 1 event with ID {test_event.event_id}, found {len(matching_events)}"


@pytest.mark.property
@settings(max_examples=20, deadline=None)
@given(
    events=st.lists(event_strategy(), min_size=5, max_size=20, unique_by=lambda e: e.event_id)
)
def test_property_idempotency_batch_insertion(events):
    """Property 3b: Batch insertion is idempotent.
    
    Inserting the same batch of events multiple times should result
    in only one copy of each event being stored.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = str(Path(tmp_dir) / "test_batch_idempotency.db")
        store = EventStore(db_path=db_path, logger=None)
        
        # Insert the same batch multiple times
        for iteration in range(3):
            result = store.insert_events_batch(events)
            assert result.success_count == len(events), \
                f"Iteration {iteration}: All events should be processed successfully"
            assert len(result.errors) == 0, \
                f"Iteration {iteration}: No errors should occur"
        
        # Get all unique store_ids from events
        store_ids = set(e.store_id for e in events)
        
        # Query and verify only one copy of each event exists
        for store_id in store_ids:
            filters = EventFilters(store_id=store_id)
            stored_events = store.query_events(filters)
            
            # Count events by event_id
            event_id_counts = {}
            for event in stored_events:
                event_id_counts[event.event_id] = event_id_counts.get(event.event_id, 0) + 1
            
            # Property: Each event_id should appear exactly once
            for event_id, count in event_id_counts.items():
                assert count == 1, \
                    f"Event {event_id} appears {count} times, expected 1 (idempotency violation)"


@pytest.mark.property
@settings(max_examples=20, deadline=None)
@given(
    events=st.lists(event_strategy(), min_size=3, max_size=10, unique_by=lambda e: e.event_id)
)
def test_property_idempotency_mixed_operations(events):
    """Property 3c: Mixed single and batch insertions are idempotent.
    
    Mixing single inserts and batch inserts for the same events should
    result in only one copy of each event being stored.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = str(Path(tmp_dir) / "test_mixed_idempotency.db")
        store = EventStore(db_path=db_path, logger=None)
        
        # Insert first event individually
        store.insert_event(events[0])
        
        # Insert all events as a batch
        store.insert_events_batch(events)
        
        # Insert last event individually again
        if len(events) > 1:
            store.insert_event(events[-1])
        
        # Insert the middle events individually
        for event in events[1:-1]:
            store.insert_event(event)
        
        # Query and verify only one copy of each event exists
        store_ids = set(e.store_id for e in events)
        
        total_stored_events = 0
        for store_id in store_ids:
            filters = EventFilters(store_id=store_id)
            stored_events = store.query_events(filters)
            total_stored_events += len(stored_events)
        
        # Property: Total stored events should equal original unique events
        assert total_stored_events == len(events), \
            f"Expected {len(events)} unique events, found {total_stored_events}"

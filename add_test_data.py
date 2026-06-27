#!/usr/bin/env python3
"""Quick script to add test data to the database for frontend demo."""

import sys
from datetime import datetime, timedelta
import uuid
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.event_store import EventStore
from src.models import Event, EventType
from src.logger import Logger

def generate_test_events(store_id: str, num_customers: int = 50):
    """Generate realistic test events for a store."""
    events = []
    base_time = datetime.now() - timedelta(hours=2)
    
    for customer_id in range(1, num_customers + 1):
        # Entry event
        entry_time = base_time + timedelta(seconds=customer_id * 20)
        events.append(Event(
            event_id=str(uuid.uuid4()),
            event_type=EventType.ENTRY,
            timestamp=entry_time,
            store_id=store_id,
            track_id=customer_id,
            metadata={"camera_id": "cam_entry"}
        ))
        
        # Zone enter (80% of customers)
        if customer_id % 5 != 0:
            zone_enter_time = entry_time + timedelta(seconds=30)
            events.append(Event(
                event_id=str(uuid.uuid4()),
                event_type=EventType.ZONE_ENTER,
                timestamp=zone_enter_time,
                store_id=store_id,
                track_id=customer_id,
                metadata={"zone_id": "shopping_zone", "camera_id": "cam_zone"}
            ))
            
            # Zone dwell (some customers)
            if customer_id % 3 == 0:
                events.append(Event(
                    event_id=str(uuid.uuid4()),
                    event_type=EventType.ZONE_DWELL,
                    timestamp=zone_enter_time + timedelta(seconds=15),
                    store_id=store_id,
                    track_id=customer_id,
                    metadata={"zone_id": "shopping_zone", "dwell_seconds": 15}
                ))
            
            # Zone exit
            zone_exit_time = zone_enter_time + timedelta(seconds=45)
            events.append(Event(
                event_id=str(uuid.uuid4()),
                event_type=EventType.ZONE_EXIT,
                timestamp=zone_exit_time,
                store_id=store_id,
                track_id=customer_id,
                metadata={"zone_id": "shopping_zone", "camera_id": "cam_zone"}
            ))
        
        # Exit event (90% of customers)
        if customer_id % 10 != 0:
            exit_time = entry_time + timedelta(seconds=120)
            events.append(Event(
                event_id=str(uuid.uuid4()),
                event_type=EventType.EXIT,
                timestamp=exit_time,
                store_id=store_id,
                track_id=customer_id,
                metadata={"camera_id": "cam_exit"}
            ))
    
    return events

def main():
    """Add test data to database."""
    logger = Logger(component="test_data_generator")
    event_store = EventStore(db_path="data/events.db", logger=logger)
    
    print("=" * 70)
    print("ADDING TEST DATA TO DATABASE")
    print("=" * 70)
    
    stores = [
        ("store_001", 50),
        ("store_002", 30),
        ("store_1", 40),
        ("store_2", 35),
    ]
    
    total_events = 0
    
    for store_id, num_customers in stores:
        print(f"\n📊 Generating events for {store_id}...")
        events = generate_test_events(store_id, num_customers)
        
        print(f"   Inserting {len(events)} events...")
        result = event_store.insert_events_batch(events)
        
        print(f"   ✅ Inserted: {result.success_count} events")
        if result.errors:
            print(f"   ⚠️  Errors: {len(result.errors)}")
        
        total_events += result.success_count
    
    print("\n" + "=" * 70)
    print(f"✅ COMPLETE: Added {total_events} test events to database")
    print("=" * 70)
    print(f"\nDatabase: data/events.db")
    print(f"\nYou can now:")
    print("  1. Refresh your frontend dashboard")
    print("  2. Select any store from the sidebar")
    print("  3. View metrics, funnel, and anomalies")
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()

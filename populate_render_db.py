"""Populate Render database with test data via API.

This script sends test events to the deployed Render backend
to populate it with sample data for testing.
"""

import requests
import json
from datetime import datetime, timedelta
import random
import uuid

# Render backend URL
API_URL = "https://store-intelligence-api-154l.onrender.com"

def generate_events_for_store(store_id: str, count: int = 100) -> list:
    """Generate realistic test events for a store.
    
    Args:
        store_id: Store identifier
        count: Number of events to generate
        
    Returns:
        List of event dictionaries
    """
    events = []
    base_time = datetime.now() - timedelta(hours=2)
    
    # Generate events for multiple tracks (customers)
    num_tracks = count // 4  # ~4 events per customer
    
    for track in range(1, num_tracks + 1):
        entry_time = base_time + timedelta(minutes=random.randint(0, 120))
        
        # 1. ENTRY event
        events.append({
            "event_id": str(uuid.uuid4()),
            "event_type": "ENTRY",
            "timestamp": entry_time.isoformat() + "Z",
            "store_id": store_id,
            "track_id": track,
            "metadata": {}
        })
        
        # 2. ZONE_ENTER event (80% of customers)
        if random.random() < 0.8:
            zone_time = entry_time + timedelta(seconds=random.randint(10, 60))
            events.append({
                "event_id": str(uuid.uuid4()),
                "event_type": "ZONE_ENTER",
                "timestamp": zone_time.isoformat() + "Z",
                "store_id": store_id,
                "track_id": track,
                "metadata": {"zone_id": f"zone_{random.randint(1, 3)}"}
            })
            
            # 3. ZONE_DWELL event (50% of zone visitors)
            if random.random() < 0.5:
                dwell_time = zone_time + timedelta(seconds=random.randint(30, 180))
                events.append({
                    "event_id": str(uuid.uuid4()),
                    "event_type": "ZONE_DWELL",
                    "timestamp": dwell_time.isoformat() + "Z",
                    "store_id": store_id,
                    "track_id": track,
                    "metadata": {
                        "zone_id": f"zone_{random.randint(1, 3)}",
                        "dwell_duration_seconds": random.randint(30, 180)
                    }
                })
        
        # 4. EXIT event (90% of customers)
        if random.random() < 0.9:
            exit_time = entry_time + timedelta(minutes=random.randint(5, 30))
            events.append({
                "event_id": str(uuid.uuid4()),
                "event_type": "EXIT",
                "timestamp": exit_time.isoformat() + "Z",
                "store_id": store_id,
                "track_id": track,
                "metadata": {}
            })
    
    return events


def send_events_batch(events: list, batch_size: int = 50):
    """Send events to Render API in batches.
    
    Args:
        events: List of events to send
        batch_size: Number of events per batch
    """
    total = len(events)
    success_count = 0
    error_count = 0
    
    print(f"\n📤 Sending {total} events in batches of {batch_size}...")
    
    for i in range(0, total, batch_size):
        batch = events[i:i + batch_size]
        
        try:
            response = requests.post(
                f"{API_URL}/events/ingest",
                json=batch,
                timeout=30
            )
            
            if response.status_code == 201:
                result = response.json()
                success_count += result.get("events_processed", 0)
                print(f"   ✅ Batch {i//batch_size + 1}: {len(batch)} events sent")
            else:
                error_count += len(batch)
                print(f"   ❌ Batch {i//batch_size + 1}: Error {response.status_code}")
                print(f"      {response.text}")
                
        except Exception as e:
            error_count += len(batch)
            print(f"   ❌ Batch {i//batch_size + 1}: {str(e)}")
    
    return success_count, error_count


def verify_data(store_id: str):
    """Verify data was inserted by querying metrics.
    
    Args:
        store_id: Store identifier to check
    """
    try:
        response = requests.get(
            f"{API_URL}/stores/{store_id}/metrics",
            timeout=10
        )
        
        if response.status_code == 200:
            metrics = response.json()
            print(f"\n✅ Verification for {store_id}:")
            print(f"   Total Entries: {metrics['total_entries']}")
            print(f"   Total Exits: {metrics['total_exits']}")
            print(f"   Current Occupancy: {metrics['current_occupancy']}")
            print(f"   Avg Visit Duration: {metrics['average_visit_duration_seconds']:.1f}s")
            return True
        else:
            print(f"\n❌ Verification failed: {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ Verification error: {str(e)}")
        return False


def main():
    """Main function to populate Render database."""
    print("=" * 70)
    print("  POPULATE RENDER DATABASE WITH TEST DATA")
    print("=" * 70)
    print(f"\nTarget: {API_URL}")
    
    # Check if API is reachable
    print("\n🔍 Checking API health...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        if response.status_code == 200:
            print("   ✅ API is healthy")
        else:
            print(f"   ⚠️  API returned {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Cannot reach API: {str(e)}")
        print("\n   Make sure your Render backend is deployed and running!")
        return
    
    # Generate and send data for each store
    stores = [
        {"id": "store_001", "name": "Store 001 (Downtown)", "events": 150},
        {"id": "store_002", "name": "Store 002 (Mall)", "events": 120},
        {"id": "store_1", "name": "Store 1 (Purplle)", "events": 180},
        {"id": "store_2", "name": "Store 2 (Purplle)", "events": 140},
    ]
    
    total_success = 0
    total_errors = 0
    
    for store in stores:
        print(f"\n" + "─" * 70)
        print(f"📊 Generating data for {store['name']}")
        
        # Generate events
        events = generate_events_for_store(store["id"], store["events"])
        print(f"   Generated {len(events)} events")
        
        # Send to API
        success, errors = send_events_batch(events, batch_size=50)
        total_success += success
        total_errors += errors
        
        # Verify
        verify_data(store["id"])
    
    # Final summary
    print(f"\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"✅ Total events sent successfully: {total_success}")
    if total_errors > 0:
        print(f"❌ Total errors: {total_errors}")
    print(f"\n🎉 Database population complete!")
    print(f"\nYou can now test your dashboard at:")
    print(f"   https://your-project.vercel.app")
    print("=" * 70)


if __name__ == "__main__":
    main()

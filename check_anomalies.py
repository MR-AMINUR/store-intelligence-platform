"""Quick script to debug anomalies endpoint."""

import sqlite3
from datetime import datetime, timezone, timedelta
import traceback

try:
    conn = sqlite3.connect('data/events.db')
    cursor = conn.cursor()
    
    # Check timestamp range
    cursor.execute("SELECT MIN(timestamp), MAX(timestamp), COUNT(*) FROM events WHERE store_id='store_001'")
    result = cursor.fetchone()
    print(f"📊 Events for store_001:")
    print(f"   Min timestamp: {result[0]}")
    print(f"   Max timestamp: {result[1]}")
    print(f"   Total count: {result[2]}")
    
    # Check current time and window
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=24)
    print(f"\n⏰ Time window:")
    print(f"   Current time: {now.isoformat()}")
    print(f"   Window start (24h ago): {window_start.isoformat()}")
    
    # Check events in window
    cursor.execute("SELECT COUNT(*) FROM events WHERE store_id='store_001' AND timestamp >= ?", 
                   (window_start.isoformat(),))
    in_window = cursor.fetchone()[0]
    print(f"   Events in last 24h: {in_window}")
    
    # Try to run the anomaly detection logic
    print(f"\n🔍 Testing anomaly detection logic...")
    
    # Test query 1: Sudden crowd surge (hourly occupancy)
    cursor.execute("""
        SELECT 
            strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
            SUM(CASE WHEN event_type = 'ENTRY' THEN 1 ELSE 0 END) -
            SUM(CASE WHEN event_type = 'EXIT' THEN 1 ELSE 0 END) as occupancy
        FROM events
        WHERE store_id = ? AND timestamp >= ?
        GROUP BY hour
        ORDER BY hour
    """, ('store_001', window_start.isoformat()))
    
    occupancy_data = cursor.fetchall()
    print(f"   Query 1 (Crowd surge): {len(occupancy_data)} hourly data points")
    if occupancy_data:
        print(f"   Sample: {occupancy_data[:3]}")
    
    # Test query 2: Queue abandonment
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN event_type = 'BILLING_QUEUE_JOIN' THEN 1 END) as joins,
            COUNT(CASE WHEN event_type = 'BILLING_QUEUE_ABANDON' THEN 1 END) as abandons
        FROM events
        WHERE store_id = ? AND timestamp >= ?
    """, ('store_001', window_start.isoformat()))
    
    row = cursor.fetchone()
    print(f"   Query 2 (Queue): Joins={row[0]}, Abandons={row[1]}")
    
    # Test query 3: Dwell times
    cursor.execute("""
        SELECT json_extract(metadata, '$.dwell_duration_seconds')
        FROM events
        WHERE store_id = ? 
        AND event_type = 'ZONE_DWELL'
        AND timestamp >= ?
    """, ('store_001', window_start.isoformat()))
    
    dwell_times = [row[0] for row in cursor.fetchall() if row[0] is not None]
    print(f"   Query 3 (Dwell times): {len(dwell_times)} dwell events")
    
    # Test query 4: Off-hours activity
    cursor.execute("""
        SELECT COUNT(*) FROM events
        WHERE store_id = ? 
        AND event_type = 'ENTRY'
        AND timestamp >= ?
        AND (
            CAST(strftime('%H', timestamp) AS INTEGER) < 9
            OR CAST(strftime('%H', timestamp) AS INTEGER) >= 21
        )
    """, ('store_001', window_start.isoformat()))
    
    off_hours = cursor.fetchone()[0]
    print(f"   Query 4 (Off-hours): {off_hours} entries")
    
    # Now test the actual endpoint
    print(f"\n🧪 Testing actual anomaly detection...")
    from src.event_store import EventStore
    
    store = EventStore(db_path='data/events.db', logger=None)
    anomalies = store.detect_anomalies('store_001', time_window=24)
    
    print(f"   ✅ Success! Found {len(anomalies)} anomalies")
    for i, anomaly in enumerate(anomalies, 1):
        print(f"   {i}. {anomaly.type} ({anomaly.severity}): {anomaly.description}")
    
    conn.close()
    
    print(f"\n✅ No errors detected! Anomalies endpoint should work.")
    
except Exception as e:
    print(f"\n❌ Error occurred:")
    print(f"   {type(e).__name__}: {str(e)}")
    print(f"\nFull traceback:")
    traceback.print_exc()

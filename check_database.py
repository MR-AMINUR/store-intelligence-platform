"""Check validation database results."""
import sqlite3
import os

db_path = 'data/purplle_validation.db'

if not os.path.exists(db_path):
    print(f"Database not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Total events
cursor.execute('SELECT COUNT(*) FROM events')
total = cursor.fetchone()[0]
print(f"Total events: {total}")

# By event type
cursor.execute('SELECT event_type, COUNT(*) FROM events GROUP BY event_type ORDER BY COUNT(*) DESC')
print('\nEvents by type:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]}')

# By store
cursor.execute('SELECT store_id, COUNT(*) FROM events GROUP BY store_id')
print('\nEvents by store:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]}')

# Sample events
cursor.execute('SELECT event_id, event_type, track_id, timestamp FROM events LIMIT 10')
print('\nSample events (first 10):')
for row in cursor.fetchall():
    print(f'  {row[0][:8]}... | {row[1]:20} | Track {row[2]} | {row[3][:19]}')

conn.close()

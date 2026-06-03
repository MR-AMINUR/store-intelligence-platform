#!/bin/bash
# Docker entrypoint script for Store Intelligence Platform
# This script:
# 1. Initializes the database schema on container start
# 2. Starts the API server

set -e  # Exit on error

echo "=== Store Intelligence Platform - Starting ==="

# Initialize database schema
echo "Initializing database schema..."
python /app/init_db.py --db-path "${DB_PATH:-/app/data/events.db}"

if [ $? -eq 0 ]; then
    echo "Database initialization successful"
else
    echo "ERROR: Database initialization failed"
    exit 1
fi

echo "Starting API server..."

# Execute the main command (passed as arguments to this script)
exec "$@"

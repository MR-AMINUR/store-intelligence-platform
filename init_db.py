#!/usr/bin/env python3
"""Database initialization script for Docker container startup.

This script initializes the SQLite database schema when the container starts.
It is designed to be idempotent - safe to run multiple times.

Usage:
    python init_db.py [--db-path PATH]

Environment Variables:
    DB_PATH: Path to SQLite database file (default: ./data/events.db)
"""

import argparse
import os
import sys
from pathlib import Path


def init_database(db_path: str) -> bool:
    """Initialize the SQLite database schema.
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        True if initialization successful, False otherwise
    """
    try:
        # Import EventStore to leverage existing schema initialization
        # Add parent directory to path to allow imports
        sys.path.insert(0, str(Path(__file__).parent))
        
        from src.event_store import EventStore
        from src.logger import Logger
        
        # Create logger for initialization
        logger = Logger(component="DatabaseInit", level="INFO")
        
        logger.info(
            "Initializing database",
            db_path=db_path
        )
        
        # Create EventStore instance - this will initialize schema
        event_store = EventStore(db_path=db_path, logger=logger)
        
        # Verify database health
        if event_store.health_check():
            logger.info(
                "Database initialization successful",
                db_path=db_path
            )
            return True
        else:
            logger.error(
                "Database health check failed after initialization",
                db_path=db_path
            )
            return False
            
    except Exception as e:
        print(f"ERROR: Database initialization failed: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point for database initialization script."""
    parser = argparse.ArgumentParser(
        description="Initialize SQLite database schema for Store Intelligence Platform"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=os.getenv("DB_PATH", "./data/events.db"),
        help="Path to SQLite database file (default: ./data/events.db or $DB_PATH)"
    )
    
    args = parser.parse_args()
    
    # Initialize database
    success = init_database(args.db_path)
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

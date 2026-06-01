# Implementation Plan: Store Intelligence Platform

## Overview

This implementation plan breaks down the Store Intelligence Platform into discrete coding tasks. The system is a computer vision-based retail analytics platform that processes CCTV footage using YOLOv8 for person detection, ByteTrack for tracking, generates structured events, stores them in SQLite, and provides REST API analytics endpoints. The implementation follows a bottom-up approach, building core components first, then integrating them, and finally adding comprehensive testing.

## Tasks

- [x] 1. Project Setup and Configuration
  - Create project directory structure (src/, tests/, config/, data/, models/)
  - Set up Python virtual environment with requirements.txt
  - Install dependencies: fastapi, uvicorn, opencv-python, ultralytics, numpy, sqlalchemy, pydantic, pytest, hypothesis, pytest-cov
  - Create .env.example file with all configuration parameters
  - Create .gitignore for Python project
  - _Requirements: 23.1, 23.2, 23.3_

- [ ] 2. Implement Configuration Manager
  - [x] 2.1 Create ConfigManager class with environment variable loading
    - Implement __init__ to load from os.environ
    - Implement get() method with default values
    - Define all configuration parameters (DB_PATH, API_HOST, API_PORT, LOG_LEVEL, YOLO_MODEL_PATH, CONFIDENCE_THRESHOLD, TRACKER_MAX_AGE, ZONE_CONFIG_PATH)
    - _Requirements: 23.1, 23.2_
  
  - [x] 2.2 Implement configuration validation
    - Validate file paths exist (model paths, zone config)
    - Validate numeric ranges (confidence 0-1, port 1-65535)
    - Raise ValueError with descriptive messages for invalid config
    - _Requirements: 23.3, 23.4_
  
  - [ ]* 2.3 Write unit tests for ConfigManager
    - Test loading valid configuration
    - Test validation errors for invalid values
    - Test default values
    - _Requirements: 20.1, 23.3_


- [ ] 3. Implement Logger
  - [ ] 3.1 Create Logger class with structured JSON logging
    - Implement __init__ with component name and log level
    - Implement debug, info, warning, error, critical methods
    - Format logs as JSON with timestamp, level, component, correlation_id, message, context
    - Use Python's logging module with custom formatter
    - _Requirements: 17.1, 17.2, 17.3_
  
  - [ ] 3.2 Add correlation ID support
    - Generate correlation_id for each processing job/API request
    - Propagate correlation_id through all log calls
    - Store correlation_id in thread-local storage or context variable
    - _Requirements: 17.3_
  
  - [ ]* 3.3 Write property test for Logger
    - **Property 33: Structured Logging Format**
    - **Validates: Requirements 17.1, 17.2, 17.3**
  
  - [ ]* 3.4 Write unit tests for Logger
    - Test log output format
    - Test log level filtering
    - Test correlation_id propagation
    - _Requirements: 20.1, 17.1_

- [ ] 4. Implement Data Models
  - [ ] 4.1 Create core data classes
    - Define Frame dataclass (frame_number, timestamp, image, resolution)
    - Define BoundingBox dataclass (x, y, width, height)
    - Define Detection dataclass (bbox, confidence, class_id)
    - Define Track dataclass (track_id, bbox, frame_number, age, state)
    - Define Zone dataclass (zone_id, zone_name, polygon, zone_type)
    - Define Event dataclass (event_id, event_type, timestamp, store_id, track_id, metadata)
    - Use Python dataclasses with type hints
    - _Requirements: 22.2, 22.3_
  
  - [ ] 4.2 Create EventType enum
    - Define all event types: ENTRY, EXIT, ZONE_ENTER, ZONE_EXIT, ZONE_DWELL, BILLING_QUEUE_JOIN, BILLING_QUEUE_ABANDON, REENTRY
    - _Requirements: 8.1_

  
  - [ ] 4.3 Create Pydantic models for API
    - Define IngestResponse model
    - Define StoreMetrics model
    - Define ConversionFunnel model
    - Define Heatmap model
    - Define Anomaly model
    - Define HealthStatus model
    - Add JSON schema validation
    - _Requirements: 10.1, 11.1, 12.1, 13.1, 14.1, 15.1_
  
  - [ ]* 4.4 Write property test for Event data model
    - **Property 1: Event Schema Completeness**
    - **Validates: Requirements 4.3, 8.1, 8.2, 8.3, 5.4**
  
  - [ ]* 4.5 Write unit tests for data models
    - Test dataclass initialization
    - Test Pydantic model validation
    - Test JSON serialization/deserialization
    - _Requirements: 20.1_

- [ ] 5. Implement Video Processor
  - [ ] 5.1 Create VideoProcessor class
    - Implement __init__ with video_path and logger
    - Implement read_frames() generator using OpenCV
    - Yield Frame objects with metadata (frame_number, timestamp, resolution)
    - Handle decode errors gracefully (log and continue)
    - Implement get_metadata() for video info
    - _Requirements: 1.1, 1.2, 1.3, 1.4_
  
  - [ ] 5.2 Add format validation
    - Validate video file exists
    - Check file extension against whitelist (MP4, AVI, MOV)
    - Raise FileNotFoundError or ValueError for invalid inputs
    - _Requirements: 1.2, 18.1_
  
  - [ ]* 5.3 Write property test for VideoProcessor
    - **Property 4: Frame Ordering Preservation**
    - **Validates: Requirements 1.5**
  
  - [ ]* 5.4 Write property test for frame metadata
    - **Property 5: Frame Metadata Completeness**
    - **Validates: Requirements 1.4**

  
  - [ ]* 5.5 Write unit tests for VideoProcessor
    - Test successful video processing
    - Test decode error handling
    - Test file not found error
    - Test unsupported format error
    - _Requirements: 20.1, 1.3, 18.1_

- [ ] 6. Implement Person Detector
  - [ ] 6.1 Create PersonDetector class with YOLOv8
    - Implement __init__ with model_path, confidence_threshold, logger
    - Load YOLOv8 model using ultralytics library
    - Auto-detect GPU or fallback to CPU
    - _Requirements: 2.1, 2.5_
  
  - [ ] 6.2 Implement detect() method
    - Accept frame as np.ndarray
    - Run YOLOv8 inference
    - Filter detections by confidence threshold
    - Filter for person class (class_id = 0)
    - Return List[Detection] with bbox and confidence
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [ ]* 6.3 Write property test for confidence filtering
    - **Property 6: Detection Confidence Filtering**
    - **Validates: Requirements 2.4**
  
  - [ ]* 6.4 Write property test for detection structure
    - **Property 7: Detection Structure Validity**
    - **Validates: Requirements 2.2, 2.3**
  
  - [ ]* 6.5 Write unit tests for PersonDetector
    - Test model loading
    - Test detection on sample frame
    - Test confidence filtering
    - Test model loading failure
    - Mock YOLOv8 model for faster tests
    - _Requirements: 20.1, 2.1, 2.4_

- [ ] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 8. Implement Person Tracker
  - [ ] 8.1 Create PersonTracker class with ByteTrack
    - Implement __init__ with max_age and logger
    - Initialize ByteTrack tracker
    - Initialize trajectory storage (dict: track_id -> List[Position])
    - _Requirements: 3.1, 3.2, 3.5_
  
  - [ ] 8.2 Implement update() method
    - Accept List[Detection] and frame_number
    - Update ByteTrack with detections
    - Maintain Track_IDs across frames
    - Handle occlusions (up to max_age frames)
    - Assign new Track_IDs after extended absence
    - Store trajectory positions
    - Return List[Track]
    - _Requirements: 3.1, 3.3, 3.4, 3.5_
  
  - [ ] 8.3 Implement get_trajectory() method
    - Accept track_id
    - Return List[Position] from trajectory storage
    - _Requirements: 3.5_
  
  - [ ]* 8.4 Write property test for trajectory maintenance
    - **Property 8: Trajectory History Maintenance**
    - **Validates: Requirements 3.5**
  
  - [ ]* 8.5 Write unit tests for PersonTracker
    - Test track assignment
    - Test occlusion handling
    - Test trajectory storage
    - Test track removal after max_age
    - Mock ByteTrack for controlled testing
    - _Requirements: 20.1, 3.1, 3.3, 3.4_

- [ ] 9. Implement Event Generator - Core Logic
  - [ ] 9.1 Create EventGenerator class
    - Implement __init__ with store_id, zones, logger
    - Initialize track state map (track_id -> last_seen_frame)
    - Initialize zone state map (track_id -> {zone_id, enter_frame})
    - Initialize exit history (track_id -> exit_timestamp)
    - Load zone configuration from JSON
    - _Requirements: 4.1, 4.2, 5.1, 5.2, 6.1, 7.1_

  
  - [ ] 9.2 Implement process_tracks() method - Entry/Exit detection
    - Accept List[Track] and frame_number
    - Detect new tracks (first appearance) -> generate ENTRY events
    - Detect absent tracks (>max_age frames) -> generate EXIT events
    - Update track state map
    - Generate unique event_ids using UUID
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  
  - [ ] 9.3 Implement zone interaction detection
    - Implement point-in-polygon test for track centroid
    - Detect zone entry -> generate ZONE_ENTER events
    - Detect zone exit -> generate ZONE_EXIT events
    - Detect dwell (>5 seconds) -> generate ZONE_DWELL events with duration
    - Update zone state map
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [ ] 9.4 Implement billing queue detection
    - Detect BILLING_QUEUE zone entry -> generate BILLING_QUEUE_JOIN events with queue_position
    - Detect queue exit without checkout -> generate BILLING_QUEUE_ABANDON events
    - Calculate queue_wait_time_seconds
    - Flag high_wait_time if >300 seconds
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [ ] 9.5 Implement reentry detection
    - Check new tracks against exit history (within 300s)
    - Generate REENTRY events with time_since_last_exit_seconds, previous_track_id
    - Set immediate_return flag if <300 seconds
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  
  - [ ] 9.6 Implement finalize() method
    - Generate EXIT events for all remaining active tracks
    - _Requirements: 4.2_
  
  - [ ] 9.7 Add event schema validation
    - Validate all events against JSON schema before emission
    - Log validation errors and discard invalid events
    - Ensure ISO 8601 timestamp format
    - _Requirements: 8.1, 8.4, 8.5_


- [ ] 10. Implement Event Generator - Property Tests
  - [ ]* 10.1 Write property test for event pairing
    - **Property 2: Event Pairing Invariant**
    - **Validates: Requirements 4.5, 5.6**
  
  - [ ]* 10.2 Write property test for entry event generation
    - **Property 9: Entry Event Generation**
    - **Validates: Requirements 4.1**
  
  - [ ]* 10.3 Write property test for exit event generation
    - **Property 10: Exit Event Generation**
    - **Validates: Requirements 4.2**
  
  - [ ]* 10.4 Write property test for event ID uniqueness
    - **Property 11: Event ID Uniqueness**
    - **Validates: Requirements 4.4**
  
  - [ ]* 10.5 Write property test for zone boundary detection
    - **Property 12: Zone Boundary Detection**
    - **Validates: Requirements 5.1, 5.2**
  
  - [ ]* 10.6 Write property test for zone dwell events
    - **Property 13: Zone Dwell Event Generation**
    - **Validates: Requirements 5.3, 5.5**
  
  - [ ]* 10.7 Write property test for billing queue events
    - **Property 14: Billing Queue Event Generation**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.5**
  
  - [ ]* 10.8 Write property test for high wait time flagging
    - **Property 15: High Wait Time Flagging**
    - **Validates: Requirements 6.4**
  
  - [ ]* 10.9 Write property test for reentry detection
    - **Property 16: Reentry Detection and Classification**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4**
  
  - [ ]* 10.10 Write property test for ISO 8601 timestamps
    - **Property 17: ISO 8601 Timestamp Format**
    - **Validates: Requirements 8.5**

  
  - [ ]* 10.11 Write unit tests for EventGenerator
    - Test entry/exit detection
    - Test zone interaction detection
    - Test billing queue detection
    - Test reentry detection
    - Test schema validation
    - Test edge cases (exact 30 frames, exact 5 seconds, exact 300 seconds)
    - _Requirements: 20.1, 20.5_

- [ ] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Implement Event Store - Database Layer
  - [ ] 12.1 Create EventStore class with SQLite
    - Implement __init__ with db_path and logger
    - Create SQLite connection with WAL mode for concurrent reads
    - Create events table schema with indexes
    - Implement schema initialization
    - _Requirements: 9.1, 9.2_
  
  - [ ] 12.2 Implement insert_event() method
    - Accept Event object
    - Use INSERT OR IGNORE for idempotency
    - Return True for success, True for duplicate (idempotent)
    - Serialize metadata as JSON
    - _Requirements: 9.1, 9.3_
  
  - [ ] 12.3 Implement insert_events_batch() method
    - Accept List[Event]
    - Use transaction for atomicity
    - Return BatchResult with success count and errors
    - _Requirements: 9.1, 10.6_
  
  - [ ] 12.4 Implement query_events() method
    - Accept EventFilters (store_id, track_id, event_type, time range)
    - Build SQL query with filters
    - Return List[Event]
    - Deserialize metadata from JSON
    - _Requirements: 9.1_

  
  - [ ] 12.5 Implement retry logic with exponential backoff
    - Wrap database operations in retry decorator
    - Retry up to 3 times with exponential backoff (1s, 2s, 4s)
    - Handle OperationalError for lock contention
    - _Requirements: 18.2_
  
  - [ ] 12.6 Implement health_check() method
    - Test database connectivity
    - Return boolean
    - _Requirements: 15.3_
  
  - [ ]* 12.7 Write property test for idempotency
    - **Property 3: System-Wide Idempotency**
    - **Validates: Requirements 9.3, 10.4, 16.1, 16.2, 16.5**
  
  - [ ]* 12.8 Write unit tests for EventStore
    - Test event insertion
    - Test batch insertion
    - Test idempotency
    - Test query with filters
    - Test retry logic
    - Test concurrent reads
    - Use in-memory SQLite for tests
    - _Requirements: 20.1, 20.4, 9.3, 9.4_

- [ ] 13. Implement Event Store - Analytics Methods
  - [ ] 13.1 Implement get_store_metrics() method
    - Accept store_id, start_time, end_time
    - Calculate total_entries (count ENTRY events)
    - Calculate total_exits (count EXIT events)
    - Calculate current_occupancy (entries - exits)
    - Calculate average_visit_duration_seconds
    - Return StoreMetrics
    - _Requirements: 11.2, 11.3, 11.5_
  
  - [ ] 13.2 Implement get_conversion_funnel() method
    - Accept store_id, optional zone_id
    - Calculate funnel stages: entries, zone_visits, billing_queue_joins, completed_purchases
    - Calculate conversion rates between stages
    - Filter by zone_id if provided
    - Return ConversionFunnel
    - _Requirements: 12.2, 12.3, 12.4_

  
  - [ ] 13.3 Implement get_heatmap() method
    - Accept store_id, resolution
    - Query trajectory positions from events
    - Create grid based on spatial bounds and resolution
    - Count positions in each grid cell
    - Normalize density values to [0, 1]
    - Return Heatmap
    - _Requirements: 13.2, 13.3, 13.4, 13.5_
  
  - [ ] 13.4 Implement detect_anomalies() method
    - Accept store_id, time_window
    - Detect sudden_crowd_surge (occupancy > mean + 2*std_dev)
    - Detect high_queue_abandonment (rate > mean + 2*std_dev)
    - Detect unusual_dwell_time (dwell > mean + 2*std_dev or < mean - 2*std_dev)
    - Detect off_hours_activity (entries outside 9 AM - 9 PM)
    - Assign severity levels (low, medium, high)
    - Return List[Anomaly]
    - _Requirements: 14.2, 14.3, 14.4, 14.5_
  
  - [ ]* 13.5 Write property test for metrics completeness
    - **Property 21: Store Metrics Completeness**
    - **Validates: Requirements 11.2**
  
  - [ ]* 13.6 Write property test for metrics time filtering
    - **Property 22: Store Metrics Time Filtering**
    - **Validates: Requirements 11.3**
  
  - [ ]* 13.7 Write property test for metrics calculation accuracy
    - **Property 23: Store Metrics Calculation Accuracy**
    - **Validates: Requirements 11.5**
  
  - [ ]* 13.8 Write property test for funnel completeness
    - **Property 24: Conversion Funnel Completeness**
    - **Validates: Requirements 12.2**
  
  - [ ]* 13.9 Write property test for conversion rate calculation
    - **Property 25: Conversion Rate Calculation**
    - **Validates: Requirements 12.3**

  
  - [ ]* 13.10 Write property test for funnel zone filtering
    - **Property 26: Funnel Zone Filtering**
    - **Validates: Requirements 12.4**
  
  - [ ]* 13.11 Write property test for heatmap grid structure
    - **Property 27: Heatmap Grid Structure**
    - **Validates: Requirements 13.2, 13.3**
  
  - [ ]* 13.12 Write property test for heatmap density calculation
    - **Property 28: Heatmap Density Calculation**
    - **Validates: Requirements 13.4**
  
  - [ ]* 13.13 Write property test for heatmap density normalization
    - **Property 29: Heatmap Density Normalization**
    - **Validates: Requirements 13.5**
  
  - [ ]* 13.14 Write property test for anomaly detection completeness
    - **Property 30: Anomaly Detection Completeness**
    - **Validates: Requirements 14.2, 14.3**
  
  - [ ]* 13.15 Write property test for anomaly statistical threshold
    - **Property 31: Anomaly Statistical Threshold**
    - **Validates: Requirements 14.4**
  
  - [ ]* 13.16 Write property test for anomaly time window filtering
    - **Property 32: Anomaly Time Window Filtering**
    - **Validates: Requirements 14.5**
  
  - [ ]* 13.17 Write unit tests for analytics methods
    - Test metrics calculation with sample data
    - Test funnel calculation
    - Test heatmap generation
    - Test anomaly detection
    - _Requirements: 20.1_

- [ ] 14. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 15. Implement API Server - Core Setup
  - [ ] 15.1 Create FastAPI application
    - Initialize FastAPI app
    - Add CORS middleware
    - Add request logging middleware
    - Add error handling middleware
    - Initialize EventStore instance
    - _Requirements: 10.1, 17.4_
  
  - [ ] 15.2 Implement global exception handler
    - Catch all unhandled exceptions
    - Log full stack trace
    - Return HTTP 500 with generic message (no internal details)
    - _Requirements: 18.4, 18.5_
  
  - [ ] 15.3 Implement request logging middleware
    - Log method, path, status_code, response_time for all requests
    - Generate correlation_id for each request
    - _Requirements: 17.4_

- [ ] 16. Implement API Server - Event Ingestion Endpoint
  - [ ] 16.1 Implement POST /events/ingest endpoint
    - Accept single Event or List[Event] in request body
    - Validate request payload using Pydantic
    - Call EventStore.insert_event() or insert_events_batch()
    - Return HTTP 201 for new events
    - Return HTTP 200 for duplicate event_id (idempotent)
    - Return HTTP 400 for validation errors with descriptive messages
    - Return HTTP 500 for server errors
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_
  
  - [ ]* 16.2 Write property test for API event ingestion success
    - **Property 18: API Event Ingestion Success**
    - **Validates: Requirements 10.2, 10.4**
  
  - [ ]* 16.3 Write property test for API validation error response
    - **Property 19: API Validation Error Response**
    - **Validates: Requirements 10.3, 18.3**

  
  - [ ]* 16.4 Write property test for batch ingestion atomicity
    - **Property 20: Batch Ingestion Atomicity**
    - **Validates: Requirements 10.6**
  
  - [ ]* 16.5 Write unit tests for /events/ingest endpoint
    - Test single event ingestion
    - Test batch event ingestion
    - Test validation errors
    - Test idempotency
    - Use TestClient from FastAPI
    - _Requirements: 20.3, 10.2, 10.3, 10.4_

- [ ] 17. Implement API Server - Analytics Endpoints
  - [ ] 17.1 Implement GET /stores/{id}/metrics endpoint
    - Accept store_id path parameter
    - Accept optional start_time, end_time query parameters
    - Call EventStore.get_store_metrics()
    - Return HTTP 200 with StoreMetrics JSON
    - Return HTTP 404 if store not found
    - Return HTTP 500 for server errors
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.6_
  
  - [ ] 17.2 Implement GET /stores/{id}/funnel endpoint
    - Accept store_id path parameter
    - Accept optional zone_id query parameter
    - Call EventStore.get_conversion_funnel()
    - Return HTTP 200 with ConversionFunnel JSON
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_
  
  - [ ] 17.3 Implement GET /stores/{id}/heatmap endpoint
    - Accept store_id path parameter
    - Accept optional resolution query parameter (default 50)
    - Call EventStore.get_heatmap()
    - Return HTTP 200 with Heatmap JSON
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6_
  
  - [ ] 17.4 Implement GET /stores/{id}/anomalies endpoint
    - Accept store_id path parameter
    - Accept optional time_window query parameter (default 24 hours)
    - Call EventStore.detect_anomalies()
    - Return HTTP 200 with List[Anomaly] JSON
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_

  
  - [ ] 17.5 Implement GET /health endpoint
    - Call EventStore.health_check()
    - Return HTTP 200 with HealthStatus JSON (healthy or degraded)
    - Return HTTP 503 if unhealthy
    - Include response_time_ms in response
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_
  
  - [ ]* 17.6 Write property test for error response sanitization
    - **Property 35: Error Response Sanitization**
    - **Validates: Requirements 18.4**
  
  - [ ]* 17.7 Write property test for API request logging
    - **Property 34: API Request Logging**
    - **Validates: Requirements 17.4**
  
  - [ ]* 17.8 Write unit tests for analytics endpoints
    - Test /stores/{id}/metrics with various filters
    - Test /stores/{id}/funnel with zone filtering
    - Test /stores/{id}/heatmap with resolution parameter
    - Test /stores/{id}/anomalies with time window
    - Test /health endpoint
    - Test 404 responses for missing stores
    - Use TestClient from FastAPI
    - _Requirements: 20.3, 11.1, 12.1, 13.1, 14.1, 15.1_

- [ ] 18. Implement Video Processing Pipeline Integration
  - [ ] 18.1 Create main pipeline orchestrator
    - Accept video_path, config, logger
    - Initialize VideoProcessor, PersonDetector, PersonTracker, EventGenerator, EventStore
    - Process video frame by frame
    - Detect people in each frame
    - Update tracks
    - Generate events
    - Store events
    - Call EventGenerator.finalize() at end
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 9.1_
  
  - [ ] 18.2 Add error handling to pipeline
    - Handle frame decode errors (log and continue)
    - Handle detection failures (log and continue with empty detections)
    - Handle database errors (retry with backoff)
    - _Requirements: 18.1, 18.2_

  
  - [ ]* 18.3 Write integration test for end-to-end pipeline
    - Use small test video (10-30 seconds)
    - Process video through complete pipeline
    - Verify events are generated and stored
    - Verify event types are correct
    - _Requirements: 20.3_

- [ ] 19. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 20. Create CLI Entry Points
  - [ ] 20.1 Create CLI for video processing
    - Accept video_path, config_path as arguments
    - Load configuration
    - Initialize logger
    - Run video processing pipeline
    - Print summary statistics
    - _Requirements: 1.1_
  
  - [ ] 20.2 Create CLI for API server
    - Accept config_path as argument
    - Load configuration
    - Initialize logger
    - Start FastAPI server with uvicorn
    - _Requirements: 10.1_
  
  - [ ] 20.3 Add command-line argument parsing
    - Use argparse for CLI arguments
    - Add --help documentation
    - _Requirements: 21.3_

- [ ] 21. Docker Setup
  - [ ] 21.1 Create Dockerfile
    - Use Python 3.10+ base image
    - Install system dependencies (OpenCV, etc.)
    - Copy application code
    - Install Python dependencies
    - Expose API port (8000)
    - Set entrypoint to API server
    - _Requirements: 19.1_
  
  - [ ] 21.2 Create docker-compose.yml
    - Define service for API server
    - Mount volumes for persistent data and video files
    - Set environment variables
    - _Requirements: 19.2, 19.3_

  
  - [ ] 21.3 Add database initialization script
    - Create script to initialize SQLite schema on container start
    - _Requirements: 19.4_
  
  - [ ] 21.4 Add volume mount configuration
    - Configure persistent data volume for SQLite database
    - Configure video files volume
    - _Requirements: 19.5_
  
  - [ ]* 21.5 Test Docker deployment
    - Build Docker image
    - Run container with docker-compose
    - Test API endpoints
    - Verify persistent data storage
    - _Requirements: 19.1, 19.2_

- [ ] 22. Documentation
  - [ ] 22.1 Create README.md
    - Add project overview
    - Add setup instructions (local and Docker)
    - Add usage examples (CLI and API)
    - Add API endpoint documentation with request/response examples
    - Add configuration documentation
    - _Requirements: 21.3, 21.4_
  
  - [ ] 22.2 Create DESIGN.md
    - Document system architecture
    - Document component responsibilities
    - Document data flow
    - Document design decisions
    - _Requirements: 21.1_
  
  - [ ] 22.3 Create CHOICES.md
    - Document design decisions with options considered
    - Document pros and cons of each option
    - Document rationale for chosen approach
    - Cover: YOLOv8 vs other detectors, ByteTrack vs other trackers, SQLite vs other databases, FastAPI vs other frameworks
    - _Requirements: 21.2_
  
  - [ ] 22.4 Add docstrings to all public functions and classes
    - Use Google-style docstrings
    - Document parameters, return values, exceptions
    - _Requirements: 22.5_


- [ ] 23. Code Quality and Testing
  - [ ] 23.1 Add type hints to all functions
    - Use Python type hints for all function signatures
    - Use mypy for type checking
    - _Requirements: 22.2_
  
  - [ ] 23.2 Format code with black and flake8
    - Run black for code formatting
    - Run flake8 for linting
    - Fix all linting errors
    - _Requirements: 22.1_
  
  - [ ] 23.3 Run pytest with coverage
    - Run all unit tests
    - Run all property tests (100 iterations minimum)
    - Run all integration tests
    - Generate coverage report (HTML and XML)
    - Ensure coverage >= 70%
    - _Requirements: 20.1, 20.2, 20.6_
  
  - [ ] 23.4 Create pytest configuration
    - Create pytest.ini with test discovery settings
    - Configure coverage settings
    - Configure Hypothesis settings (100 iterations, deterministic seed)
    - _Requirements: 20.1, 20.2_
  
  - [ ] 23.5 Create test fixtures
    - Create fixtures for sample events
    - Create fixtures for sample tracks
    - Create fixtures for sample zones
    - Create fixtures for test video files
    - _Requirements: 20.1_

- [ ] 24. Performance Testing
  - [ ]* 24.1 Write performance test for detector
    - Test detector achieves >= 10 FPS on CPU
    - Use sample frame, run 100 iterations
    - _Requirements: 24.1_
  
  - [ ]* 24.2 Write performance test for health endpoint
    - Test /health responds within 100ms
    - _Requirements: 24.2_

  
  - [ ]* 24.3 Write performance test for metrics endpoint
    - Test /stores/{id}/metrics responds within 500ms for 1M events
    - Create test database with 1M events
    - _Requirements: 24.3_
  
  - [ ]* 24.4 Write performance test for event store write throughput
    - Test EventStore achieves >= 1000 events/second
    - Use batch insertion
    - _Requirements: 24.4_

- [ ] 25. CI/CD Setup
  - [ ] 25.1 Create GitHub Actions workflow (or equivalent CI)
    - Run linter (flake8, black)
    - Run type checker (mypy)
    - Run unit tests with coverage
    - Run property tests (100 iterations)
    - Run integration tests
    - Generate coverage report
    - Fail if coverage < 70%
    - _Requirements: 20.1, 20.2_
  
  - [ ] 25.2 Add CI badge to README
    - Add build status badge
    - Add coverage badge
    - _Requirements: 21.3_

- [ ] 26. Final Integration and Testing
  - [ ]* 26.1 Run complete test suite
    - Run all unit tests
    - Run all property tests
    - Run all integration tests
    - Run all performance tests
    - Verify all tests pass
    - Verify coverage >= 70%
    - _Requirements: 20.1, 20.2, 20.3_
  
  - [ ]* 26.2 Test complete deployment
    - Build Docker image
    - Deploy with docker-compose
    - Process sample video through pipeline
    - Test all API endpoints
    - Verify persistent data storage
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5_

  
  - [ ] 26.3 Create sample zone configuration file
    - Create config/zones.json with example zones
    - Include GENERAL and BILLING_QUEUE zone types
    - _Requirements: 5.1, 6.1_
  
  - [ ] 26.4 Create sample .env file
    - Create .env.example with all configuration parameters
    - Document each parameter
    - _Requirements: 23.1, 23.2, 23.5_

- [ ] 27. Final Checkpoint - Production Readiness
  - Ensure all tests pass, ask the user if questions arise.
  - Verify all documentation is complete
  - Verify Docker deployment works
  - Verify CI/CD pipeline passes
  - Verify code coverage >= 70%
  - Verify all 35 property tests are implemented and passingted and passing

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties (35 total)
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end flows
- Performance tests validate non-functional requirements
- Minimum 70% code coverage required
- All property tests must run with minimum 100 iterations
- Docker deployment is required for production readiness
- Comprehensive documentation (README, DESIGN, CHOICES) is required



## Task Dependency Graph

```json
{
  "dependencies": {
    "1": ["2.1"],
    "2.1": ["2.2"],
    "3.1": ["3.2"],
    "4.1": ["4.2"],
    "4.2": ["4.3"],
    "5.1": ["5.2"],
    "6.1": ["6.2"],
    "8.1": ["8.2"],
    "8.2": ["8.3"],
    "9.1": ["9.2"],
    "9.2": ["9.3"],
    "9.3": ["9.4"],
    "9.4": ["9.5"],
    "9.5": ["9.6"],
    "9.6": ["9.7"],
    "12.1": ["12.2"],
    "12.2": ["12.3"],
    "12.3": ["12.4"],
    "12.4": ["12.5"],
    "12.5": ["12.6"],
    "13.1": ["13.2"],
    "13.2": ["13.3"],
    "13.3": ["13.4"],
    "15.1": ["15.2"],
    "15.2": ["15.3"],
    "15.3": ["16.1"],
    "17.1": ["17.2"],
    "17.2": ["17.3"],
    "17.3": ["17.4"],
    "17.4": ["17.5"],
    "18.1": ["18.2"],
    "20.1": ["20.2"],
    "20.2": ["20.3"],
    "21.1": ["21.2"],
    "21.2": ["21.3"],
    "21.3": ["21.4"],
    "22.1": ["22.2"],
    "22.2": ["22.3"],
    "22.3": ["22.4"],
    "23.1": ["23.2"],
    "23.2": ["23.3"],
    "23.3": ["23.4"],
    "23.4": ["23.5"],
    "25.1": ["25.2"],
    "26.3": ["26.4"]
  },
  "waves": [
    ["3.1", "4.1", "5.1", "6.1", "8.1", "9.1", "12.1", "13.1", "15.1", "17.1", "18.1", "20.1", "21.1", "22.1", "23.1", "25.1", "26.3"]
  ]
}
```

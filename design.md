# Technical Design Document

## Overview

The Store Intelligence Platform is a production-ready computer vision analytics system built using a pipeline architecture. This document describes the technical design, component responsibilities, data flow, and implementation details.

For detailed requirements, see [requirements specification](.kiro/specs/store-intelligence-platform/requirements.md).

---

## System Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Video Input Layer                         │
│                                                              │
│  ┌──────────────┐        ┌──────────────┐                  │
│  │ Video Files  │  OR    │ Video Stream │                  │
│  └──────┬───────┘        └──────┬───────┘                  │
└─────────┼────────────────────────┼──────────────────────────┘
          │                        │
          └────────────┬───────────┘
                       ▼
          ┌────────────────────────┐
          │   VideoProcessor       │
          │  - Frame extraction    │
          │  - Metadata generation │
          │  - Error handling      │
          └────────┬───────────────┘
                   ▼
          ┌────────────────────────┐
          │   PersonDetector       │
          │  - YOLOv8 inference    │
          │  - Confidence filter   │
          │  - GPU/CPU auto-detect │
          └────────┬───────────────┘
                   ▼
          ┌────────────────────────┐
          │   PersonTracker        │
          │  - ByteTrack tracking  │
          │  - Track ID assignment │
          │  - Trajectory storage  │
          └────────┬───────────────┘
                   ▼
          ┌────────────────────────┐
          │   EventGenerator       │
          │  - Entry/Exit events   │
          │  - Zone interactions   │
          │  - Queue monitoring    │
          │  - Reentry detection   │
          └────────┬───────────────┘
                   ▼
          ┌────────────────────────┐
          │     EventStore         │
          │  - SQLite database     │
          │  - Idempotent inserts  │
          │  - Analytics queries   │
          └────────┬───────────────┘
                   ▼
          ┌────────────────────────┐
          │     API Server         │
          │  - FastAPI endpoints   │
          │  - Event ingestion     │
          │  - Analytics APIs      │
          └────────┬───────────────┘
                   ▼
          ┌────────────────────────┐
          │   External Clients     │
          │  - Web dashboards      │
          │  - Mobile apps         │
          │  - Other systems       │
          └────────────────────────┘
```

### Cross-Cutting Concerns

```
┌──────────────────────────────────────────────────────────┐
│              Configuration Manager                        │
│  Loads and validates environment variables               │
└──────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│                    Logger                                 │
│  - Structured JSON logging                               │
│  - Correlation ID propagation                            │
│  - Component-level isolation                             │
└──────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. VideoProcessor

**Responsibility**: Decode video files and extract frames with metadata.

**Key Methods**:
- `__init__(video_path, logger)`: Initialize with video path
- `read_frames()`: Generator yielding Frame objects
- `get_metadata()`: Return video metadata (duration, fps, resolution)

**Implementation Details**:
- Uses OpenCV (`cv2.VideoCapture`) for video decoding
- Supports formats: MP4, AVI, MOV
- Handles decode errors gracefully (logs and continues)
- Yields Frame dataclass with:
  - `frame_number`: Sequential frame number
  - `timestamp`: Time offset from video start (seconds)
  - `image`: numpy array (HxWx3, BGR format)
  - `resolution`: Tuple (width, height)

**Error Handling**:
- File not found → `FileNotFoundError`
- Unsupported format → `ValueError`
- Decode failure → Log error, skip frame

---

### 2. PersonDetector

**Responsibility**: Detect people in video frames using YOLOv8.

**Key Methods**:
- `__init__(model_path, confidence_threshold, logger)`: Load YOLOv8 model
- `detect(frame)`: Detect people, return List[Detection]

**Implementation Details**:
- Uses Ultralytics YOLOv8 library
- Auto-detects GPU (CUDA) or falls back to CPU
- Filters detections:
  - Confidence ≥ threshold (default 0.5)
  - Class ID = 0 (person class in COCO dataset)
- Returns Detection dataclass:
  - `bbox`: BoundingBox(x, y, width, height)
  - `confidence`: Float [0, 1]
  - `class_id`: Always 0 for person

**Performance**:
- **CPU**: ≥10 FPS (YOLOv8n)
- **GPU**: ≥30 FPS (YOLOv8n)
- Configurable models: yolov8n (nano), yolov8s (small), yolov8m (medium)

---

### 3. PersonTracker

**Responsibility**: Maintain consistent Track IDs across frames using ByteTrack.

**Key Methods**:
- `__init__(max_age, logger)`: Initialize tracker
- `update(detections, frame_number)`: Update tracks, return List[Track]
- `get_trajectory(track_id)`: Return trajectory history

**Implementation Details**:
- Uses ByteTrack algorithm for multi-object tracking
- Maintains Track ID consistency across frames
- Handles occlusions: Keeps track alive for `max_age` frames (default 30)
- Stores trajectory: Dict[track_id → List[Position]]
- Returns Track dataclass:
  - `track_id`: Unique integer ID
  - `bbox`: Current bounding box
  - `frame_number`: Current frame
  - `age`: Frames since last detection
  - `state`: ACTIVE, LOST, or REMOVED

**Re-ID Logic**:
- Track absent ≤30 frames → Same Track ID retained
- Track absent >30 frames → New Track ID assigned on reappearance

---

### 4. EventGenerator

**Responsibility**: Generate structured events from tracking data.

**Key Methods**:
- `__init__(store_id, zones, logger, fps)`: Initialize with config
- `process_tracks(tracks, frame_number)`: Generate events from tracks
- `finalize()`: Generate final EXIT events
- `from_zone_config(config_path)`: Load zones from JSON

**Event Types Generated**:

1. **ENTRY**: New Track ID appears
2. **EXIT**: Track ID absent >max_age frames
3. **ZONE_ENTER**: Track enters zone polygon
4. **ZONE_EXIT**: Track exits zone polygon
5. **ZONE_DWELL**: Track in zone >5 seconds
6. **BILLING_QUEUE_JOIN**: Track enters billing queue zone
7. **BILLING_QUEUE_ABANDON**: Track leaves queue without checkout
8. **REENTRY**: Track ID reappears after previous exit (within 300s window)

**State Management**:
- Track state map: `track_id → last_seen_frame`
- Zone state map: `track_id → {zone_id, enter_frame, enter_timestamp}`
- Exit history: `track_id → {exit_timestamp, exit_frame}`

**Zone Detection**:
- Point-in-polygon test using ray-casting algorithm
- Track centroid = (bbox.x + bbox.width/2, bbox.y + bbox.height/2)

**Event Schema**:
```python
@dataclass
class Event:
    event_id: str         # UUID
    event_type: str       # EventType enum
    timestamp: datetime   # ISO 8601
    store_id: str
    track_id: int
    metadata: Dict        # Event-specific fields
```

---

### 5. EventStore

**Responsibility**: Persist events to SQLite database and provide analytics.

**Key Methods**:
- `__init__(db_path, logger)`: Initialize database connection
- `insert_event(event)`: Insert single event (idempotent)
- `insert_events_batch(events)`: Insert batch (atomic transaction)
- `query_events(filters)`: Query events with filters
- `get_store_metrics(store_id, time_range)`: Calculate store metrics
- `get_conversion_funnel(store_id, zone_id)`: Calculate funnel
- `get_heatmap(store_id, resolution)`: Generate spatial heatmap
- `detect_anomalies(store_id, time_window)`: Detect anomalies
- `health_check()`: Test database connectivity

**Database Schema**:
```sql
CREATE TABLE events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    store_id TEXT NOT NULL,
    track_id INTEGER NOT NULL,
    metadata TEXT NOT NULL,  -- JSON
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for query performance
CREATE INDEX idx_store_id ON events(store_id);
CREATE INDEX idx_track_id ON events(track_id);
CREATE INDEX idx_event_type ON events(event_type);
CREATE INDEX idx_timestamp ON events(timestamp);
CREATE INDEX idx_store_timestamp ON events(store_id, timestamp);
```

**Idempotency**:
- `event_id` is PRIMARY KEY (unique constraint)
- `INSERT OR IGNORE` for idempotent inserts
- Duplicate `event_id` → No-op, returns success

**Concurrency**:
- SQLite WAL (Write-Ahead Logging) mode enabled
- Supports concurrent reads during writes
- Retry logic with exponential backoff for lock contention

**Analytics Implementation**:

1. **Store Metrics**: Aggregate counts with SQL
2. **Conversion Funnel**: Sequential stage counting
3. **Heatmap**: Grid-based trajectory density
4. **Anomaly Detection**: Statistical thresholds (mean + 2σ)

---

### 6. API Server

**Responsibility**: Expose REST API for event ingestion and analytics.

**Framework**: FastAPI

**Middleware Stack**:
1. CORS middleware (allow all origins by default)
2. Request logging middleware (correlation IDs)
3. Error handling middleware (sanitize errors)

**Endpoints**:

| Method | Path | Purpose |
|--------|------|---------|
| POST | /events/ingest | Ingest events (single/batch) |
| GET | /stores/{id}/metrics | Store metrics |
| GET | /stores/{id}/funnel | Conversion funnel |
| GET | /stores/{id}/heatmap | Spatial heatmap |
| GET | /stores/{id}/anomalies | Anomaly detection |
| GET | /health | Health check |
| GET | /docs | OpenAPI documentation |

**Error Handling**:
- 400: Validation errors (descriptive messages)
- 404: Resource not found
- 500: Internal errors (sanitized, no stack traces)
- All errors logged with correlation IDs

**Response Format**:
```json
{
  "data": { ... },
  "correlation_id": "req-abc123"
}
```

---

### 7. ConfigManager

**Responsibility**: Load and validate configuration from environment variables.

**Parameters**:
- `DB_PATH`: SQLite database path
- `API_HOST`: API server bind address
- `API_PORT`: API server port (1-65535)
- `LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
- `YOLO_MODEL_PATH`: YOLOv8 model file path
- `CONFIDENCE_THRESHOLD`: Detection confidence (0.0-1.0)
- `TRACKER_MAX_AGE`: Max frames without detection (positive integer)
- `ZONE_CONFIG_PATH`: Zone configuration JSON path
- `STORE_ID`: Default store ID

**Validation Rules**:
- File paths must exist
- Numeric ranges enforced
- Descriptive error messages on validation failure

---

### 8. Logger

**Responsibility**: Structured JSON logging with correlation IDs.

**Log Format**:
```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "level": "INFO",
  "component": "PersonDetector",
  "correlation_id": "req-abc123",
  "message": "Detected 5 people in frame 42",
  "context": {
    "frame_number": 42,
    "detection_count": 5,
    "processing_time_ms": 45
  }
}
```

**Correlation ID Propagation**:
- Generated for each video processing job or API request
- Stored in thread-local storage
- Automatically included in all log entries
- Returned in API response headers

---

## Data Flow

### Video Processing Pipeline

```
1. VideoProcessor.read_frames()
   ↓ Frame(image, metadata)
   
2. PersonDetector.detect(frame.image)
   ↓ List[Detection(bbox, confidence)]
   
3. PersonTracker.update(detections, frame_number)
   ↓ List[Track(track_id, bbox, state)]
   
4. EventGenerator.process_tracks(tracks, frame_number)
   ↓ List[Event(event_type, timestamp, track_id, metadata)]
   
5. EventStore.insert_events_batch(events)
   ↓ BatchResult(success_count, errors)
   
6. EventGenerator.finalize()
   ↓ List[Event] (final EXIT events)
```

### API Request Flow

```
1. Client → POST /events/ingest
   ↓ Request body validated (Pydantic)
   
2. API Server → EventStore.insert_event()
   ↓ Database insert with idempotency check
   
3. EventStore → SQLite (INSERT OR IGNORE)
   ↓ Success/Duplicate result
   
4. API Server → Client
   ↓ JSON response with correlation_id
```

---

## Design Patterns

### 1. Pipeline Pattern
Sequential processing stages with clear interfaces.

### 2. Repository Pattern
EventStore abstracts database operations.

### 3. Factory Pattern
`EventGenerator.from_zone_config()` for configuration-based instantiation.

### 4. Strategy Pattern
Different anomaly detection strategies (crowd surge, queue abandonment, etc.).

### 5. Dependency Injection
Components receive dependencies (logger, config) via constructor.

---

## Performance Considerations

### Bottlenecks
1. **YOLOv8 Inference**: Slowest component (~100ms/frame on CPU)
2. **Database Writes**: ~1ms per event (batch reduces overhead)
3. **Video Decoding**: ~10ms/frame

### Optimizations
1. **GPU Acceleration**: 3-5x speedup for detection
2. **Batch Event Insertion**: 10x throughput improvement
3. **Database Indexing**: <10ms query time for 1M events
4. **SQLite WAL Mode**: Concurrent reads during writes

---

## Error Handling Strategy

### Graceful Degradation
- Frame decode error → Log and continue
- Detection failure → Continue with empty detections
- Database unavailable → Retry with exponential backoff (3 attempts)

### Error Isolation
- Component failures don't cascade
- Errors logged with full context
- API errors sanitized (no internal details exposed)

---

## Security Considerations

### Current Implementation
- No authentication/authorization (development mode)
- CORS enabled for all origins
- No rate limiting
- No input sanitization beyond validation

### Production Recommendations
1. Add API key authentication
2. Implement rate limiting
3. Restrict CORS origins
4. Add input sanitization
5. Enable HTTPS/TLS
6. Implement audit logging

---

## Scalability

### Horizontal Scaling
- **API Server**: Multiple uvicorn workers
- **Database**: Read replicas (SQLite limitations)

### Vertical Scaling
- **GPU**: Faster detection
- **CPU cores**: Parallel video processing
- **Memory**: Larger batch sizes

### Limitations
- SQLite write throughput (~1000 events/s)
- Single-process video processing
- No distributed tracking

### Future Improvements
- PostgreSQL for higher write throughput
- Distributed video processing (Celery, Ray)
- Redis for shared state (reentry detection)
- Kafka for event streaming

---

## Testing Strategy

### Unit Tests (200+ tests)
- Component isolation
- Mock external dependencies
- Edge case coverage

### Property-Based Tests (35 properties)
- Hypothesis framework
- 100+ iterations per property
- Invariant validation

### Integration Tests (20+ tests)
- End-to-end pipeline
- API endpoint validation
- Database operations

### Performance Tests (4 tests)
- Detection speed (≥10 FPS)
- API response time (<100ms health, <500ms metrics)
- Event insertion throughput (≥1000/s)

---

## Deployment Architecture

### Local Development
```
Developer Machine
├── Python 3.10+
├── Virtual Environment
├── SQLite Database (data/events.db)
├── YOLOv8 Model (models/yolov8n.pt)
└── API Server (localhost:8000)
```

### Docker Deployment
```
Docker Host
├── Container: store-intelligence-api
│   ├── FastAPI Server
│   ├── EventStore (SQLite)
│   └── Volume: /data (persistent)
├── Container: store-intelligence-processor (optional)
│   └── Video Processing Pipeline
└── Volume: shared-data
```

### Production Deployment
```
Load Balancer
├── API Server Instance 1
├── API Server Instance 2
└── API Server Instance N

Database Layer
├── PostgreSQL Primary
└── PostgreSQL Replicas

Storage Layer
├── S3 (Video Files)
└── EBS (Database)
```

---

## Monitoring & Observability

### Metrics to Track
- **Detection**: FPS, confidence distribution
- **Tracking**: Active tracks, track lifetime
- **Events**: Event generation rate, event type distribution
- **Database**: Query latency, connection pool usage
- **API**: Request rate, response time, error rate

### Logging
- Structured JSON logs
- Correlation IDs for request tracing
- Component-level log isolation
- Configurable log levels

### Health Checks
- Database connectivity
- Model availability
- Disk space
- Memory usage

---

## Configuration Management

### Environment-Based Config
- `.env` files for local development
- Environment variables for production
- Validation on startup

### Zone Configuration
- JSON file format
- Hot-reload support (future)
- Polygon validation

---

## API Versioning

### Current: v1 (implicit)
- All endpoints under root path
- No explicit version in URL

### Future: Explicit Versioning
- `/v1/events/ingest`
- `/v2/events/ingest`
- Backward compatibility guaranteed

---

## Future Enhancements

### Short-term
1. Docker deployment (Task 21)
2. CI/CD pipeline (Task 25)
3. Performance testing (Task 24)

### Medium-term
1. Real-time video stream processing
2. WebSocket API for live updates
3. PostgreSQL migration
4. Authentication & authorization

### Long-term
1. Multi-store support
2. Distributed video processing
3. ML model retraining pipeline
4. Advanced analytics (predictive)

---

## References

- **YOLOv8 Documentation**: https://docs.ultralytics.com/
- **ByteTrack Paper**: https://arxiv.org/abs/2110.06864
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **SQLite Documentation**: https://www.sqlite.org/docs.html

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Authors**: Development Team

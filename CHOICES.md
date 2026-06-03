# Design Choices & Trade-offs

This document explains the key technology and design decisions made in the Store Intelligence Platform, including alternatives considered, pros/cons of each option, and rationale for the chosen approach.

---

## Table of Contents

1. [Person Detection: YOLOv8](#1-person-detection-yolov8)
2. [Person Tracking: ByteTrack](#2-person-tracking-bytetrack)
3. [Database: SQLite](#3-database-sqlite)
4. [API Framework: FastAPI](#4-api-framework-fastapi)
5. [Programming Language: Python](#5-programming-language-python)
6. [Testing: Pytest + Hypothesis](#6-testing-pytest--hypothesis)
7. [Configuration: Environment Variables](#7-configuration-environment-variables)
8. [Logging: Structured JSON](#8-logging-structured-json)
9. [Video Processing: OpenCV](#9-video-processing-opencv)
10. [Deployment: Docker](#10-deployment-docker)

---

## 1. Person Detection: YOLOv8

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **YOLOv8** ✅ | State-of-the-art accuracy, Fast inference (≥10 FPS CPU), Easy integration (Ultralytics), Multiple model sizes, Active development | Requires model download, GPU recommended for real-time |
| YOLOv5 | Mature, Well-documented, Slightly faster | Less accurate than YOLOv8, Older architecture |
| Faster R-CNN | High accuracy | Very slow (~1 FPS CPU), Complex setup |
| SSD | Lightweight, Fast | Lower accuracy than YOLO, Less maintained |
| MediaPipe | Very fast, Mobile-friendly | Lower accuracy, Limited customization |

### Decision: YOLOv8

**Rationale**:
- **Accuracy**: 95%+ mAP on COCO dataset (better than YOLOv5)
- **Speed**: Meets requirement (≥10 FPS on CPU with yolov8n)
- **Ease of Use**: Single-line installation (`pip install ultralytics`)
- **Flexibility**: Multiple models (nano/small/medium/large) for speed/accuracy trade-off
- **GPU Support**: Automatic CUDA detection with seamless fallback to CPU
- **Active Development**: Regular updates, strong community support

**Trade-offs Accepted**:
- Model size (~6MB for yolov8n, ~22MB for yolov8s) - acceptable given accuracy gains
- Requires external model download - mitigated by auto-download on first run

---

## 2. Person Tracking: ByteTrack

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **ByteTrack** ✅ | State-of-the-art MOT accuracy, Handles occlusions well, Simple algorithm, Fast (~30 FPS) | Relatively new (2021) |
| DeepSORT | Mature, Well-tested, Deep learning features | Slower than ByteTrack, Requires feature extraction model |
| SORT | Lightweight, Fast | Poor occlusion handling, Lower accuracy |
| OC-SORT | Improved SORT | More complex than ByteTrack |
| FairMOT | End-to-end tracking | Slower, Higher complexity |

### Decision: ByteTrack

**Rationale**:
- **Accuracy**: Achieves state-of-the-art MOT20 benchmark results
- **Simplicity**: Does not require feature extraction (unlike DeepSORT)
- **Occlusion Handling**: Maintains Track IDs through occlusions (requirement)
- **Speed**: Fast enough for real-time (≥30 FPS)
- **Low False Positives**: Leverages low-confidence detections effectively

**Trade-offs Accepted**:
- Newer algorithm (less mature than SORT/DeepSORT) - mitigated by strong benchmark results
- Not as widely adopted - acceptable given superior performance

---

## 3. Database: SQLite

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **SQLite** ✅ | Zero configuration, Serverless, Single file, Fast reads, Perfect for embedded/local, WAL mode for concurrency | Write throughput limited (~1000/s), No horizontal scaling, Single process writes |
| PostgreSQL | High write throughput, Horizontal scaling, Rich features, Production-proven | Requires server setup, More complex, Overkill for local deployment |
| MySQL | High performance, Wide adoption | Server setup required, More complex than SQLite |
| MongoDB | Flexible schema, Horizontal scaling | Schema flexibility not needed, Overkill for structured events |
| InfluxDB | Time-series optimized | Event data not strictly time-series, Less familiar to developers |

### Decision: SQLite

**Rationale**:
- **Simplicity**: Zero-configuration, no server required
- **Portability**: Single file database, easy backup/migration
- **Performance**: Fast reads (meets <500ms requirement for 1M events)
- **Concurrency**: WAL mode enables concurrent reads during writes
- **Idempotency**: PRIMARY KEY constraint enforces event_id uniqueness
- **Deployment**: Perfect for Docker single-container deployment

**Trade-offs Accepted**:
- **Write Throughput**: ~1000 events/second (acceptable for current requirements)
- **No Horizontal Scaling**: Single-process writes (acceptable for single-store deployment)
- **Migration Path**: PostgreSQL migration planned for multi-store production deployment

**When to Migrate**:
- Multiple stores (>10) generating events simultaneously
- Write throughput >5000 events/second sustained
- Need for read replicas or geographic distribution

---

## 4. API Framework: FastAPI

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **FastAPI** ✅ | Automatic OpenAPI docs, Fast (ASGI), Type validation (Pydantic), Modern async support, Easy to learn | Newer framework (less mature) |
| Flask | Mature, Simple, Large ecosystem | Slower (WSGI), No automatic docs, Manual validation |
| Django REST Framework | Full-featured, ORM included, Admin panel | Heavyweight, Overkill for our needs, Slower |
| Express.js (Node) | Fast, Large ecosystem | Would require JavaScript (team is Python) |
| Gin (Go) | Very fast | Would require Go (team is Python), More boilerplate |

### Decision: FastAPI

**Rationale**:
- **Performance**: ASGI-based, faster than Flask/Django
- **Developer Experience**: Automatic OpenAPI/Swagger documentation
- **Type Safety**: Pydantic models for request/response validation
- **Modern**: Native async/await support
- **Ecosystem**: Growing adoption, good libraries available
- **Testing**: Excellent TestClient for integration testing

**Trade-offs Accepted**:
- Newer framework (2018) vs Flask (2010) - acceptable given strong adoption trajectory
- Smaller ecosystem than Flask - sufficient libraries available for our needs

---

## 5. Programming Language: Python

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **Python** ✅ | Rich CV/ML libraries, Easy prototyping, Large community, Good for data processing | Slower than compiled languages, GIL limitations |
| C++ | Very fast, Low-level control | Complex, Slower development, Harder to maintain |
| Java | Fast, Mature ecosystem | Verbose, Less CV libraries than Python |
| Go | Fast, Good concurrency | Fewer CV/ML libraries, Less familiar to ML engineers |
| Rust | Very fast, Memory safe | Steep learning curve, Fewer CV libraries |

### Decision: Python

**Rationale**:
- **CV/ML Libraries**: YOLOv8, OpenCV, NumPy, SciPy ecosystem
- **Productivity**: Faster development, easier maintenance
- **Team Expertise**: Most CV/ML engineers know Python
- **Performance**: Acceptable with GPU acceleration for detection
- **Ecosystem**: Rich libraries for data processing, APIs, testing

**Trade-offs Accepted**:
- Slower than C++/Go/Rust - acceptable given GPU acceleration and Python's native CV library bindings
- GIL limitations - acceptable for I/O-bound workload (video processing is more I/O-bound than CPU-bound)

---

## 6. Testing: Pytest + Hypothesis

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **Pytest + Hypothesis** ✅ | Powerful fixtures, Property-based testing, Good reporting, Large plugin ecosystem | Learning curve for Hypothesis |
| unittest (stdlib) | Built-in, No dependencies | More verbose, No property testing |
| nose2 | Plugin-based | Less maintained than pytest |
| Robot Framework | Keyword-driven, BDD support | Overkill, Less suitable for unit tests |

### Decision: Pytest + Hypothesis

**Rationale**:
- **Pytest**: Industry standard, excellent fixture system, clear assertions
- **Hypothesis**: Property-based testing for invariant validation (35 properties defined)
- **Coverage**: Built-in coverage reporting (achieved 95%)
- **Plugins**: Rich ecosystem (pytest-cov, pytest-asyncio, etc.)

**Trade-offs Accepted**:
- External dependency vs stdlib unittest - acceptable given superior developer experience
- Hypothesis learning curve - mitigated by clear documentation and examples

---

## 7. Configuration: Environment Variables

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **Environment Variables** ✅ | 12-factor app compliant, Docker-friendly, Simple, Secure (no commit) | String-only values, No nested config |
| YAML/JSON Files | Nested structure, Comments, Type-safe | Needs file management, Risk of committing secrets |
| ConfigParser (INI) | Simple, Built-in | Less flexible, Harder to override |
| Python Files | Full Python power | Security risk, Complex |
| HashiCorp Vault | Secure, Centralized | Overkill, Added complexity |

### Decision: Environment Variables

**Rationale**:
- **12-Factor App**: Strict separation of config from code
- **Docker Integration**: Natural fit for container deployment
- **Security**: Secrets not committed to version control
- **Simplicity**: No file parsing, direct `os.environ` access
- **Override**: Easy to override per environment

**Trade-offs Accepted**:
- String-only values - acceptable with type conversion in ConfigManager
- No nested config - acceptable for flat configuration structure

**Mitigation**:
- `.env.example` file for documentation
- `python-dotenv` for local development
- ConfigManager validates and converts types

---

## 8. Logging: Structured JSON

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **Structured JSON** ✅ | Machine-parseable, Searchable, Correlation IDs, Log aggregation friendly | Less human-readable in terminal |
| Plain Text | Human-readable, Simple | Hard to parse, No structured queries |
| CSV | Structured, Simple | Inflexible schema |
| Binary (Protobuf) | Compact, Fast | Not human-readable, Requires schema |
| Syslog | Standard format | Limited structure |

### Decision: Structured JSON Logging

**Rationale**:
- **Machine-Parseable**: Easy to index in ELK/Splunk/CloudWatch
- **Correlation IDs**: Track requests across components
- **Context**: Arbitrary structured data in `context` field
- **Searchable**: Filter by component, level, correlation_id
- **Standard**: JSON is universal format

**Trade-offs Accepted**:
- Less readable in terminal - mitigated by pretty-printing for development
- Larger log size vs plain text - acceptable given storage is cheap and benefits are significant

**Format Example**:
```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "level": "INFO",
  "component": "PersonDetector",
  "correlation_id": "req-abc123",
  "message": "Detected 5 people",
  "context": {"frame_number": 42, "detection_count": 5}
}
```

---

## 9. Video Processing: OpenCV

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **OpenCV** ✅ | Industry standard, Fast, Comprehensive, GPU support, Python bindings | Large library, Some APIs complex |
| FFmpeg (direct) | Powerful, Format support | CLI-based, Complex integration |
| MoviePy | Simple API, Pythonic | Slower, Built on FFmpeg |
| PyAV | Pythonic FFmpeg bindings | Less documented than OpenCV |
| scikit-video | Simple, Pure Python | Slower, Limited features |

### Decision: OpenCV

**Rationale**:
- **Industry Standard**: Most widely used CV library
- **Performance**: Optimized C++ core with Python bindings
- **Features**: Comprehensive video I/O, image processing, GPU acceleration
- **Documentation**: Extensive tutorials and community support
- **Ecosystem**: Works seamlessly with YOLOv8 and other CV tools

**Trade-offs Accepted**:
- Large dependency size (~100MB with contrib modules) - acceptable given comprehensive features
- Some API complexity - mitigated by wrapper classes (VideoProcessor)

---

## 10. Deployment: Docker

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **Docker** ✅ | Consistent environment, Easy deployment, Portable, Isolated dependencies | Overhead vs bare metal, Learning curve |
| Virtual Machines | Strong isolation, Flexible | Heavy, Slow startup, Resource-intensive |
| Bare Metal | Maximum performance | Dependency conflicts, Hard to replicate |
| Kubernetes | Orchestration, Scaling | Overkill for single-service, Complex |
| Serverless (Lambda) | Auto-scaling, Pay-per-use | Cold starts, Limited runtime, Complexity |

### Decision: Docker + Docker Compose

**Rationale**:
- **Consistency**: Identical environment across dev/staging/prod
- **Portability**: Runs on any Docker host (cloud, on-prem, local)
- **Isolation**: Dependencies isolated from host
- **Simplicity**: Single `docker-compose up` command
- **CI/CD**: Easy integration with CI/CD pipelines

**Trade-offs Accepted**:
- ~5-10% performance overhead vs bare metal - acceptable for deployment benefits
- Learning curve for Docker - mitigated by comprehensive documentation

**Future Migration Path**:
- Kubernetes for multi-instance orchestration
- Docker Swarm for simpler orchestration
- Cloud-native services (ECS, Cloud Run)

---

## Architecture Patterns

### Pattern: Pipeline Architecture

**Alternatives Considered**:
- **Microservices**: Separate services for detection, tracking, events
- **Monolith**: Single application with all logic
- **Event-Driven**: Message queue between components

**Chosen: Pipeline Architecture**

**Rationale**:
- **Sequential Processing**: Video processing is inherently sequential (frame by frame)
- **Simplicity**: Clear data flow, easy to understand and debug
- **Performance**: No network overhead between stages
- **Deployment**: Single process deployment simplifies operations

**Trade-offs**:
- No horizontal scaling of individual stages - acceptable for current throughput requirements
- Tight coupling between stages - acceptable given clear interfaces

---

## Data Model: Dataclasses vs ORM

**Alternatives Considered**:
- SQLAlchemy ORM
- Django ORM
- Pydantic models
- Dataclasses

**Chosen: Dataclasses (core) + Pydantic (API)**

**Rationale**:
- **Dataclasses**: Lightweight, type-safe, built-in
- **Pydantic**: Validation for API requests/responses
- **No ORM**: SQLite is simple enough for raw SQL
- **Flexibility**: Easy to serialize to JSON/dict

**Trade-offs**:
- No automatic query generation - acceptable given simple queries
- Manual SQL - mitigated by clear separation in EventStore

---

## Idempotency: Database vs Application

**Alternatives Considered**:
- Application-level deduplication (in-memory cache)
- Distributed cache (Redis)
- Database unique constraint

**Chosen: Database Unique Constraint**

**Rationale**:
- **Durability**: Survives application restarts
- **Simplicity**: Built-in SQLite PRIMARY KEY constraint
- **Correctness**: Database enforces uniqueness atomically
- **No External Dependencies**: No Redis/Memcached required

**Trade-offs**:
- Requires database lookup for every insert - acceptable given insert performance (<1ms)

---

## Event Schema: Fixed vs Flexible

**Alternatives Considered**:
- Fixed schema (separate tables per event type)
- Flexible schema (single table with JSON metadata)
- Hybrid (fixed fields + JSON metadata)

**Chosen: Hybrid Approach**

**Rationale**:
- **Fixed Fields**: `event_id`, `event_type`, `timestamp`, `store_id`, `track_id` - indexable, queryable
- **Flexible Metadata**: JSON column for event-specific fields - extensible without schema changes
- **Best of Both**: Structured queries + flexibility

**Trade-offs**:
- JSON queries less efficient than columns - acceptable given infrequent metadata queries

---

## Summary of Key Decisions

| Component | Choice | Primary Reason |
|-----------|--------|----------------|
| Detection | YOLOv8 | Best accuracy/speed trade-off |
| Tracking | ByteTrack | State-of-the-art MOT performance |
| Database | SQLite | Simplicity and zero-configuration |
| API | FastAPI | Modern, fast, automatic docs |
| Language | Python | Rich CV/ML ecosystem |
| Testing | Pytest + Hypothesis | Property-based testing support |
| Config | Env Variables | 12-factor app compliance |
| Logging | Structured JSON | Machine-parseable, searchable |
| Video | OpenCV | Industry standard |
| Deployment | Docker | Consistency and portability |

---

## Future Decisions to Make

### When to Migrate from SQLite to PostgreSQL

**Triggers**:
- Write throughput consistently >5000 events/second
- Need for read replicas (multiple API server instances)
- Multi-store deployment with centralized database
- Geographic distribution requirements

**Migration Strategy**:
1. Update EventStore to support PostgreSQL (SQLAlchemy)
2. Implement connection pooling (pgbouncer)
3. Set up read replicas
4. Migrate data using `pg_dump` + data transformation script

### When to Adopt Microservices

**Triggers**:
- Need to scale detection/tracking independently
- Multiple teams working on different components
- Different deployment frequencies for components
- Resource isolation requirements (GPU for detection)

**Migration Strategy**:
1. Extract detection service (gRPC/REST)
2. Extract tracking service
3. Extract event generation service
4. Implement service mesh (Istio/Linkerd)

---

## Lessons Learned

### What Worked Well
✅ Pipeline architecture simplicity  
✅ Property-based testing caught edge cases  
✅ SQLite sufficient for single-store deployment  
✅ FastAPI automatic docs saved documentation time  
✅ YOLOv8 accuracy exceeded expectations  

### What Could Be Improved
🔄 Earlier performance testing would have identified bottlenecks sooner  
🔄 Docker setup should have been done earlier for consistent environments  
🔄 More comprehensive integration tests with real videos  

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Authors**: Development Team

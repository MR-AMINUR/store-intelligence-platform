"""FastAPI REST API server for Store Intelligence Platform.

This module provides the REST API endpoints for event ingestion and analytics
queries, with middleware for CORS, request logging, and error handling.
"""

import time
import traceback
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional, Union
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import ConfigManager
from src.event_store import EventStore
from src.logger import Logger
from src.models import Event, EventType, IngestResponse


# ============================================================================
# Application State Management
# ============================================================================

class AppState:
    """Application state container for shared resources."""
    
    def __init__(self) -> None:
        self.event_store: Optional[EventStore] = None
        self.logger: Optional[Logger] = None


app_state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Lifespan context manager for application startup/shutdown.
    
    Initializes EventStore and Logger on startup and cleans up on shutdown.
    """
    # Startup
    config = ConfigManager()
    
    # Initialize logger
    log_level = config.get("LOG_LEVEL", "INFO")
    app_state.logger = Logger(component="api_server", level=log_level)
    app_state.logger.info("API server starting up")
    
    # Initialize event store
    db_path = config.get("DB_PATH", "data/events.db")
    app_state.event_store = EventStore(
        db_path=db_path,
        logger=app_state.logger
    )
    app_state.logger.info("EventStore initialized", db_path=db_path)
    
    yield
    
    # Shutdown
    app_state.logger.info("API server shutting down")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Store Intelligence Platform API",
    description="REST API for retail analytics with computer vision event processing",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# Middleware
# ============================================================================

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all HTTP requests with correlation IDs.
    
    Logs method, path, status code, and response time for each request.
    Generates a unique correlation_id for request tracing.
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process request and log details.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
        
        Returns:
            HTTP response with correlation_id header
        """
        # Generate correlation ID for this request
        correlation_id = str(uuid.uuid4())
        
        # Store correlation_id in request state for access by handlers
        request.state.correlation_id = correlation_id
        
        # Record start time
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        
        # Log request details
        if app_state.logger:
            app_state.logger.info(
                "API request processed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                response_time_ms=round(response_time_ms, 2),
                correlation_id=correlation_id
            )
        
        # Add correlation_id to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for all unhandled exceptions.
    
    Logs full stack trace but returns generic error message to client
    to avoid leaking internal implementation details.
    
    Args:
        request: HTTP request that caused the exception
        exc: Exception that was raised
    
    Returns:
        JSONResponse with HTTP 500 and generic error message
    """
    # Get correlation_id if available
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    # Log full stack trace
    if app_state.logger:
        app_state.logger.error(
            "Unhandled exception",
            error=str(exc),
            error_type=exc.__class__.__name__,
            traceback=traceback.format_exc(),
            path=request.url.path,
            method=request.method,
            correlation_id=correlation_id
        )
    
    # Return generic error message (no internal details)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "correlation_id": correlation_id
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler for Pydantic validation errors.
    
    Returns detailed validation error messages with HTTP 400.
    
    Args:
        request: HTTP request that failed validation
        exc: Validation exception with error details
    
    Returns:
        JSONResponse with HTTP 400 and validation error details
    """
    # Get correlation_id if available
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    # Convert errors to JSON-serializable format
    # Pydantic v2 errors may contain non-serializable objects
    errors = []
    for error in exc.errors():
        # Create a serializable copy of the error
        serializable_error = {
            "type": error.get("type"),
            "loc": error.get("loc"),
            "msg": error.get("msg"),
            "input": str(error.get("input")) if error.get("input") is not None else None
        }
        errors.append(serializable_error)
    
    # Log validation error
    if app_state.logger:
        app_state.logger.warning(
            "Request validation failed",
            error_count=len(errors),
            path=request.url.path,
            method=request.method,
            correlation_id=correlation_id
        )
    
    return JSONResponse(
        status_code=400,
        content={
            "detail": "Validation error",
            "errors": errors,
            "correlation_id": correlation_id
        }
    )


# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.get("/", tags=["root"])
async def root():
    """Root endpoint returning API information."""
    return {
        "service": "Store Intelligence Platform API",
        "version": "1.0.0",
        "status": "running"
    }


# ============================================================================
# Helper Functions
# ============================================================================

def get_event_store() -> EventStore:
    """Get EventStore instance from application state.
    
    Returns:
        EventStore instance
    
    Raises:
        RuntimeError: If EventStore not initialized
    """
    if app_state.event_store is None:
        raise RuntimeError("EventStore not initialized")
    return app_state.event_store


def get_logger() -> Logger:
    """Get Logger instance from application state.
    
    Returns:
        Logger instance
    
    Raises:
        RuntimeError: If Logger not initialized
    """
    if app_state.logger is None:
        raise RuntimeError("Logger not initialized")
    return app_state.logger


# ============================================================================
# Pydantic Models for API Requests
# ============================================================================

class EventIngestion(BaseModel):
    """Request model for event ingestion.
    
    Accepts event data with validation for all required fields.
    """
    event_id: str = Field(..., description="Unique event identifier (UUID)")
    event_type: str = Field(..., description="Event type (ENTRY, EXIT, ZONE_ENTER, etc.)")
    timestamp: str = Field(..., description="Event timestamp in ISO 8601 format")
    store_id: str = Field(..., description="Store identifier")
    track_id: int = Field(..., description="Track identifier")
    metadata: dict = Field(default_factory=dict, description="Event-specific metadata")
    
    @field_validator('event_type')
    @classmethod
    def validate_event_type(cls, v):
        """Validate that event_type is a valid EventType enum value."""
        try:
            EventType(v)
        except ValueError:
            valid_types = [e.value for e in EventType]
            raise ValueError(f"Invalid event_type. Must be one of: {', '.join(valid_types)}")
        return v
    
    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v):
        """Validate that timestamp is in ISO 8601 format."""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError("timestamp must be in ISO 8601 format (e.g., '2024-01-01T12:00:00')")
        return v
    
    def to_event(self) -> Event:
        """Convert to Event model."""
        return Event(
            event_id=self.event_id,
            event_type=EventType(self.event_type),
            timestamp=datetime.fromisoformat(self.timestamp.replace('Z', '+00:00')),
            store_id=self.store_id,
            track_id=self.track_id,
            metadata=self.metadata
        )


# ============================================================================
# Event Ingestion Endpoint
# ============================================================================

@app.post(
    "/events/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["events"],
    summary="Ingest events",
    description="Ingest single or multiple events with idempotent behavior"
)
async def ingest_events(
    events: Union[EventIngestion, List[EventIngestion]],
    request: Request
) -> IngestResponse:
    """Ingest one or more events into the event store.
    
    This endpoint accepts either a single event or a list of events.
    All insertions are idempotent - duplicate event_ids are silently ignored.
    
    Args:
        events: Single event or list of events to ingest
        request: FastAPI request object (for correlation_id)
    
    Returns:
        IngestResponse with success status and count of processed events
    
    Raises:
        400: Validation error (invalid event data)
        500: Server error (database failure)
    """
    event_store = get_event_store()
    logger = get_logger()
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    # Convert to list if single event
    if not isinstance(events, list):
        events = [events]
    
    logger.info(
        "Event ingestion request received",
        event_count=len(events),
        correlation_id=correlation_id
    )
    
    try:
        # Convert Pydantic models to Event objects
        event_objects = [e.to_event() for e in events]
        
        # Use batch insertion for efficiency
        if len(event_objects) == 1:
            # Single event insertion
            success = event_store.insert_event(event_objects[0])
            
            if success:
                logger.info(
                    "Event ingested successfully",
                    event_id=event_objects[0].event_id,
                    correlation_id=correlation_id
                )
                
                return IngestResponse(
                    success=True,
                    events_processed=1,
                    errors=[]
                )
        else:
            # Batch insertion
            result = event_store.insert_events_batch(event_objects)
            
            logger.info(
                "Batch ingestion completed",
                total_events=len(event_objects),
                successful=result.success_count,
                failed=len(result.errors),
                correlation_id=correlation_id
            )
            
            # Determine response status
            if result.success_count == len(event_objects):
                # All succeeded
                return IngestResponse(
                    success=True,
                    events_processed=result.success_count,
                    errors=[]
                )
            elif result.success_count > 0:
                # Partial success
                return IngestResponse(
                    success=True,
                    events_processed=result.success_count,
                    errors=result.errors
                )
            else:
                # All failed
                return IngestResponse(
                    success=False,
                    events_processed=0,
                    errors=result.errors
                )
    
    except Exception as e:
        logger.error(
            "Event ingestion failed",
            error=str(e),
            error_type=e.__class__.__name__,
            correlation_id=correlation_id
        )
        raise


# ============================================================================
# Analytics Endpoints
# ============================================================================

@app.get(
    "/stores/{store_id}/metrics",
    response_model=None,  # Will return StoreMetrics but avoid double validation
    tags=["analytics"],
    summary="Get store metrics",
    description="Retrieve aggregated metrics for a store with optional time range filtering"
)
async def get_store_metrics(
    store_id: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    request: Request = None
) -> dict:
    """Get aggregated metrics for a store.
    
    Args:
        store_id: Store identifier
        start_time: Optional start time in ISO 8601 format
        end_time: Optional end time in ISO 8601 format
        request: FastAPI request object
    
    Returns:
        StoreMetrics with total entries, exits, occupancy, and average visit duration
    
    Raises:
        400: Invalid time format
        404: Store not found (no events for store)
        500: Server error
    """
    event_store = get_event_store()
    logger = get_logger()
    correlation_id = getattr(request.state, "correlation_id", "unknown") if request else "unknown"
    
    try:
        # Parse time parameters if provided
        start_dt = None
        end_dt = None
        
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "detail": "Invalid start_time format. Must be ISO 8601 (e.g., '2024-01-01T12:00:00')",
                        "correlation_id": correlation_id
                    }
                )
        
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "detail": "Invalid end_time format. Must be ISO 8601 (e.g., '2024-01-01T12:00:00')",
                        "correlation_id": correlation_id
                    }
                )
        
        # Get metrics from event store
        metrics = event_store.get_store_metrics(
            store_id=store_id,
            start_time=start_dt,
            end_time=end_dt
        )
        
        logger.info(
            "Store metrics retrieved",
            store_id=store_id,
            total_entries=metrics.total_entries,
            correlation_id=correlation_id
        )
        
        # Check if store has any events
        if metrics.total_entries == 0 and metrics.total_exits == 0:
            return JSONResponse(
                status_code=404,
                content={
                    "detail": f"Store '{store_id}' not found or has no events",
                    "correlation_id": correlation_id
                }
            )
        
        # Convert to dict for response
        return metrics.model_dump(mode='json')
    
    except Exception as e:
        logger.error(
            "Failed to retrieve store metrics",
            store_id=store_id,
            error=str(e),
            correlation_id=correlation_id
        )
        raise


@app.get(
    "/stores/{store_id}/funnel",
    response_model=None,
    tags=["analytics"],
    summary="Get conversion funnel",
    description="Retrieve customer journey conversion funnel with optional zone filtering"
)
async def get_conversion_funnel(
    store_id: str,
    zone_id: Optional[str] = None,
    request: Request = None
) -> dict:
    """Get customer journey conversion funnel.
    
    Args:
        store_id: Store identifier
        zone_id: Optional zone filter
        request: FastAPI request object
    
    Returns:
        ConversionFunnel with stages and conversion rates
    
    Raises:
        500: Server error
    """
    event_store = get_event_store()
    logger = get_logger()
    correlation_id = getattr(request.state, "correlation_id", "unknown") if request else "unknown"
    
    try:
        funnel = event_store.get_conversion_funnel(
            store_id=store_id,
            zone_id=zone_id
        )
        
        logger.info(
            "Conversion funnel retrieved",
            store_id=store_id,
            zone_id=zone_id,
            correlation_id=correlation_id
        )
        
        return funnel.model_dump(mode='json')
    
    except Exception as e:
        logger.error(
            "Failed to retrieve conversion funnel",
            store_id=store_id,
            error=str(e),
            correlation_id=correlation_id
        )
        raise


@app.get(
    "/stores/{store_id}/heatmap",
    response_model=None,
    tags=["analytics"],
    summary="Get movement heatmap",
    description="Generate spatial density heatmap of customer movement"
)
async def get_heatmap(
    store_id: str,
    resolution: int = 50,
    request: Request = None
) -> dict:
    """Get spatial density heatmap of customer movement.
    
    Args:
        store_id: Store identifier
        resolution: Grid cell size in pixels (default 50)
        request: FastAPI request object
    
    Returns:
        Heatmap with normalized density grid
    
    Raises:
        400: Invalid resolution
        500: Server error
    """
    event_store = get_event_store()
    logger = get_logger()
    correlation_id = getattr(request.state, "correlation_id", "unknown") if request else "unknown"
    
    if resolution <= 0:
        return JSONResponse(
            status_code=400,
            content={
                "detail": "Resolution must be greater than 0",
                "correlation_id": correlation_id
            }
        )
    
    try:
        heatmap = event_store.get_heatmap(
            store_id=store_id,
            resolution=resolution
        )
        
        logger.info(
            "Heatmap generated",
            store_id=store_id,
            resolution=resolution,
            correlation_id=correlation_id
        )
        
        return heatmap.model_dump(mode='json')
    
    except Exception as e:
        logger.error(
            "Failed to generate heatmap",
            store_id=store_id,
            error=str(e),
            correlation_id=correlation_id
        )
        raise


@app.get(
    "/stores/{store_id}/anomalies",
    response_model=None,
    tags=["analytics"],
    summary="Detect anomalies",
    description="Detect anomalies in store metrics over a time window"
)
async def detect_anomalies(
    store_id: str,
    time_window: int = 24,
    request: Request = None
) -> dict:
    """Detect anomalies in store metrics.
    
    Args:
        store_id: Store identifier
        time_window: Time window in hours (default 24)
        request: FastAPI request object
    
    Returns:
        List of detected anomalies with severity levels
    
    Raises:
        400: Invalid time_window
        500: Server error
    """
    event_store = get_event_store()
    logger = get_logger()
    correlation_id = getattr(request.state, "correlation_id", "unknown") if request else "unknown"
    
    if time_window <= 0:
        return JSONResponse(
            status_code=400,
            content={
                "detail": "Time window must be greater than 0",
                "correlation_id": correlation_id
            }
        )
    
    try:
        anomalies = event_store.detect_anomalies(
            store_id=store_id,
            time_window_hours=time_window
        )
        
        logger.info(
            "Anomaly detection completed",
            store_id=store_id,
            time_window_hours=time_window,
            anomalies_found=len(anomalies),
            correlation_id=correlation_id
        )
        
        return {"anomalies": [a.model_dump(mode='json') for a in anomalies]}
    
    except Exception as e:
        logger.error(
            "Failed to detect anomalies",
            store_id=store_id,
            error=str(e),
            correlation_id=correlation_id
        )
        raise


@app.get(
    "/health",
    response_model=None,
    tags=["system"],
    summary="Health check",
    description="Check system health and database connectivity"
)
async def health_check(request: Request = None) -> dict:
    """Check system health.
    
    Args:
        request: FastAPI request object
    
    Returns:
        HealthStatus with system status and response time
    
    Raises:
        503: Service unavailable (unhealthy)
    """
    event_store = get_event_store()
    logger = get_logger()
    correlation_id = getattr(request.state, "correlation_id", "unknown") if request else "unknown"
    
    start_time = time.time()
    
    try:
        # Check database connectivity
        db_healthy = event_store.health_check()
        
        response_time_ms = (time.time() - start_time) * 1000
        
        checks = {
            "database": "ok" if db_healthy else "failed"
        }
        
        # Determine overall status
        if db_healthy:
            status = "healthy"
            status_code = 200
        else:
            status = "unhealthy"
            status_code = 503
        
        logger.info(
            "Health check performed",
            status=status,
            response_time_ms=round(response_time_ms, 2),
            correlation_id=correlation_id
        )
        
        health_response = {
            "status": status,
            "checks": checks,
            "response_time_ms": round(response_time_ms, 2),
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }
        
        return JSONResponse(
            status_code=status_code,
            content=health_response
        )
    
    except Exception as e:
        logger.error(
            "Health check failed",
            error=str(e),
            correlation_id=correlation_id
        )
        
        response_time_ms = (time.time() - start_time) * 1000
        
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "checks": {"database": "failed"},
                "response_time_ms": round(response_time_ms, 2),
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "error": "Health check exception"
            }
        )

"""Unit tests for API Server analytics endpoints (Task 17).

Tests GET /stores/{id}/metrics, /funnel, /heatmap, /anomalies, and /health endpoints.
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import Mock

from src.api_server import app, app_state
from src.models import (
    StoreMetrics, TimeRange, ConversionFunnel, FunnelStage,
    Heatmap, GridDimensions, Anomaly, AnomalyMetrics
)


@pytest.fixture
def client():
    """Create TestClient for API testing."""
    return TestClient(app)


@pytest.fixture
def mock_event_store():
    """Create mock EventStore."""
    mock = Mock()
    mock.health_check.return_value = True
    return mock


@pytest.fixture
def mock_logger():
    """Create mock Logger."""
    return Mock()


@pytest.fixture(autouse=True)
def setup_app_state(mock_event_store, mock_logger):
    """Set up application state with mocks for testing."""
    app_state.event_store = mock_event_store
    app_state.logger = mock_logger
    yield
    app_state.event_store = None
    app_state.logger = None


# ============================================================================
# Test 17.1: GET /stores/{id}/metrics Endpoint
# ============================================================================

def test_get_metrics_success(client, mock_event_store):
    """Test successful metrics retrieval."""
    mock_event_store.get_store_metrics.return_value = StoreMetrics(
        store_id="store_001",
        total_entries=100,
        total_exits=80,
        current_occupancy=20,
        average_visit_duration_seconds=1200.0,
        time_range=None
    )
    
    response = client.get("/stores/store_001/metrics")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["store_id"] == "store_001"
    assert data["total_entries"] == 100
    assert data["total_exits"] == 80
    assert data["current_occupancy"] == 20
    assert data["average_visit_duration_seconds"] == 1200.0


def test_get_metrics_with_time_range(client, mock_event_store):
    """Test metrics retrieval with time range filtering."""
    mock_event_store.get_store_metrics.return_value = StoreMetrics(
        store_id="store_001",
        total_entries=50,
        total_exits=40,
        current_occupancy=10,
        average_visit_duration_seconds=900.0,
        time_range=TimeRange(
            start=datetime(2024, 1, 1, 9, 0, 0),
            end=datetime(2024, 1, 1, 18, 0, 0)
        )
    )
    
    response = client.get(
        "/stores/store_001/metrics",
        params={
            "start_time": "2024-01-01T09:00:00",
            "end_time": "2024-01-01T18:00:00"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_entries"] == 50
    assert "time_range" in data


def test_get_metrics_returns_404_for_missing_store(client, mock_event_store):
    """Test that missing store returns HTTP 404."""
    mock_event_store.get_store_metrics.return_value = StoreMetrics(
        store_id="store_999",
        total_entries=0,
        total_exits=0,
        current_occupancy=0,
        average_visit_duration_seconds=0.0,
        time_range=None
    )
    
    response = client.get("/stores/store_999/metrics")
    
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_get_metrics_returns_400_for_invalid_start_time(client):
    """Test validation error for invalid start_time format."""
    response = client.get(
        "/stores/store_001/metrics",
        params={"start_time": "invalid-date"}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "Invalid start_time format" in data["detail"]


def test_get_metrics_returns_400_for_invalid_end_time(client):
    """Test validation error for invalid end_time format."""
    response = client.get(
        "/stores/store_001/metrics",
        params={"end_time": "not-a-date"}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "Invalid end_time format" in data["detail"]


def test_get_metrics_returns_500_on_database_error(client, mock_event_store):
    """Test server error handling when database fails."""
    mock_event_store.get_store_metrics.side_effect = Exception("Database error")
    
    client_no_raise = TestClient(app, raise_server_exceptions=False)
    response = client_no_raise.get("/stores/store_001/metrics")
    
    assert response.status_code == 500


# ============================================================================
# Test 17.2: GET /stores/{id}/funnel Endpoint
# ============================================================================

def test_get_funnel_success(client, mock_event_store):
    """Test successful funnel retrieval."""
    mock_event_store.get_conversion_funnel.return_value = ConversionFunnel(
        store_id="store_001",
        stages=[
            FunnelStage(stage="entries", count=100, conversion_rate=1.0),
            FunnelStage(stage="zone_visits", count=80, conversion_rate=0.8),
            FunnelStage(stage="billing_queue_joins", count=60, conversion_rate=0.75),
            FunnelStage(stage="completed_purchases", count=50, conversion_rate=0.833)
        ],
        zone_id=None
    )
    
    response = client.get("/stores/store_001/funnel")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["store_id"] == "store_001"
    assert len(data["stages"]) == 4
    assert data["stages"][0]["stage"] == "entries"
    assert data["stages"][0]["count"] == 100
    assert data["stages"][0]["conversion_rate"] == 1.0


def test_get_funnel_with_zone_filter(client, mock_event_store):
    """Test funnel retrieval with zone filtering."""
    mock_event_store.get_conversion_funnel.return_value = ConversionFunnel(
        store_id="store_001",
        stages=[
            FunnelStage(stage="entries", count=100, conversion_rate=1.0),
            FunnelStage(stage="zone_visits", count=40, conversion_rate=0.4),
            FunnelStage(stage="billing_queue_joins", count=30, conversion_rate=0.75),
            FunnelStage(stage="completed_purchases", count=25, conversion_rate=0.833)
        ],
        zone_id="zone_cosmetics"
    )
    
    response = client.get(
        "/stores/store_001/funnel",
        params={"zone_id": "zone_cosmetics"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["zone_id"] == "zone_cosmetics"
    assert len(data["stages"]) == 4


def test_get_funnel_returns_500_on_database_error(client, mock_event_store):
    """Test server error handling for funnel endpoint."""
    mock_event_store.get_conversion_funnel.side_effect = Exception("Database error")
    
    client_no_raise = TestClient(app, raise_server_exceptions=False)
    response = client_no_raise.get("/stores/store_001/funnel")
    
    assert response.status_code == 500


# ============================================================================
# Test 17.3: GET /stores/{id}/heatmap Endpoint
# ============================================================================

def test_get_heatmap_success(client, mock_event_store):
    """Test successful heatmap generation."""
    mock_event_store.get_heatmap.return_value = Heatmap(
        store_id="store_001",
        resolution=50,
        grid=GridDimensions(width=39, height=22),
        density=[[0.0] * 39 for _ in range(22)]
    )
    
    response = client.get("/stores/store_001/heatmap")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["store_id"] == "store_001"
    assert data["resolution"] == 50
    assert data["grid"]["width"] == 39
    assert data["grid"]["height"] == 22
    assert len(data["density"]) == 22
    assert len(data["density"][0]) == 39


def test_get_heatmap_with_custom_resolution(client, mock_event_store):
    """Test heatmap with custom resolution."""
    mock_event_store.get_heatmap.return_value = Heatmap(
        store_id="store_001",
        resolution=100,
        grid=GridDimensions(width=20, height=11),
        density=[[0.0] * 20 for _ in range(11)]
    )
    
    response = client.get(
        "/stores/store_001/heatmap",
        params={"resolution": 100}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["resolution"] == 100


def test_get_heatmap_returns_400_for_invalid_resolution(client):
    """Test validation error for invalid resolution."""
    response = client.get(
        "/stores/store_001/heatmap",
        params={"resolution": 0}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "Resolution must be greater than 0" in data["detail"]


def test_get_heatmap_returns_400_for_negative_resolution(client):
    """Test validation error for negative resolution."""
    response = client.get(
        "/stores/store_001/heatmap",
        params={"resolution": -10}
    )
    
    assert response.status_code == 400


def test_get_heatmap_returns_500_on_database_error(client, mock_event_store):
    """Test server error handling for heatmap endpoint."""
    mock_event_store.get_heatmap.side_effect = Exception("Database error")
    
    client_no_raise = TestClient(app, raise_server_exceptions=False)
    response = client_no_raise.get("/stores/store_001/heatmap")
    
    assert response.status_code == 500


# ============================================================================
# Test 17.4: GET /stores/{id}/anomalies Endpoint
# ============================================================================

def test_get_anomalies_success(client, mock_event_store):
    """Test successful anomaly detection."""
    mock_event_store.detect_anomalies.return_value = [
        Anomaly(
            type="sudden_crowd_surge",
            severity="high",
            timestamp=datetime(2024, 1, 1, 15, 30, 0),
            description="Sudden increase in occupancy detected",
            metrics=AnomalyMetrics(baseline=50.0, observed=120.0, threshold=90.0)
        ),
        Anomaly(
            type="high_queue_abandonment",
            severity="medium",
            timestamp=datetime(2024, 1, 1, 16, 0, 0),
            description="High queue abandonment rate",
            metrics=AnomalyMetrics(baseline=0.1, observed=0.35, threshold=0.3)
        )
    ]
    
    response = client.get("/stores/store_001/anomalies")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "anomalies" in data
    assert len(data["anomalies"]) == 2
    assert data["anomalies"][0]["type"] == "sudden_crowd_surge"
    assert data["anomalies"][0]["severity"] == "high"
    assert data["anomalies"][1]["type"] == "high_queue_abandonment"


def test_get_anomalies_with_custom_time_window(client, mock_event_store):
    """Test anomaly detection with custom time window."""
    mock_event_store.detect_anomalies.return_value = []
    
    response = client.get(
        "/stores/store_001/anomalies",
        params={"time_window": 48}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "anomalies" in data
    # Verify time_window was passed to event_store
    call_args = mock_event_store.detect_anomalies.call_args
    assert call_args[1]["time_window_hours"] == 48


def test_get_anomalies_returns_empty_list_when_none_found(client, mock_event_store):
    """Test that empty list is returned when no anomalies found."""
    mock_event_store.detect_anomalies.return_value = []
    
    response = client.get("/stores/store_001/anomalies")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "anomalies" in data
    assert len(data["anomalies"]) == 0


def test_get_anomalies_returns_400_for_invalid_time_window(client):
    """Test validation error for invalid time_window."""
    response = client.get(
        "/stores/store_001/anomalies",
        params={"time_window": 0}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "Time window must be greater than 0" in data["detail"]


def test_get_anomalies_returns_400_for_negative_time_window(client):
    """Test validation error for negative time_window."""
    response = client.get(
        "/stores/store_001/anomalies",
        params={"time_window": -5}
    )
    
    assert response.status_code == 400


def test_get_anomalies_returns_500_on_database_error(client, mock_event_store):
    """Test server error handling for anomalies endpoint."""
    mock_event_store.detect_anomalies.side_effect = Exception("Database error")
    
    client_no_raise = TestClient(app, raise_server_exceptions=False)
    response = client_no_raise.get("/stores/store_001/anomalies")
    
    assert response.status_code == 500


# ============================================================================
# Test 17.5: GET /health Endpoint
# ============================================================================

def test_health_check_healthy(client, mock_event_store):
    """Test health check when system is healthy."""
    mock_event_store.health_check.return_value = True
    
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert data["checks"]["database"] == "ok"
    assert "response_time_ms" in data
    assert data["response_time_ms"] > 0
    assert "timestamp" in data


def test_health_check_unhealthy(client, mock_event_store):
    """Test health check when database is unhealthy."""
    mock_event_store.health_check.return_value = False
    
    response = client.get("/health")
    
    assert response.status_code == 503
    data = response.json()
    
    assert data["status"] == "unhealthy"
    assert data["checks"]["database"] == "failed"
    assert "response_time_ms" in data


def test_health_check_includes_response_time(client, mock_event_store):
    """Test that health check includes response time."""
    mock_event_store.health_check.return_value = True
    
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "response_time_ms" in data
    assert isinstance(data["response_time_ms"], (int, float))
    assert data["response_time_ms"] >= 0


def test_health_check_includes_timestamp(client, mock_event_store):
    """Test that health check includes timestamp."""
    mock_event_store.health_check.return_value = True
    
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "timestamp" in data
    # Verify it's a valid ISO 8601 timestamp
    timestamp = data["timestamp"]
    assert 'T' in timestamp
    assert timestamp.endswith('Z')


def test_health_check_returns_503_on_exception(client, mock_event_store):
    """Test health check when exception occurs."""
    mock_event_store.health_check.side_effect = Exception("Database connection failed")
    
    response = client.get("/health")
    
    assert response.status_code == 503
    data = response.json()
    
    assert data["status"] == "unhealthy"
    assert data["checks"]["database"] == "failed"


# ============================================================================
# Test Response Headers and Logging
# ============================================================================

def test_metrics_returns_correlation_id_header(client, mock_event_store):
    """Test that metrics response includes correlation_id header."""
    mock_event_store.get_store_metrics.return_value = StoreMetrics(
        store_id="store_001",
        total_entries=10,
        total_exits=5,
        current_occupancy=5,
        average_visit_duration_seconds=600.0,
        time_range=None
    )
    
    response = client.get("/stores/store_001/metrics")
    
    assert response.status_code == 200
    assert "X-Correlation-ID" in response.headers


def test_analytics_endpoints_log_requests(client, mock_logger, mock_event_store):
    """Test that analytics endpoints log requests."""
    mock_event_store.get_store_metrics.return_value = StoreMetrics(
        store_id="store_001",
        total_entries=10,
        total_exits=5,
        current_occupancy=5,
        average_visit_duration_seconds=600.0,
        time_range=None
    )
    
    response = client.get("/stores/store_001/metrics")
    
    assert response.status_code == 200
    # Verify logging was called
    assert mock_logger.info.called


def test_health_endpoint_logs_checks(client, mock_logger, mock_event_store):
    """Test that health endpoint logs check results."""
    mock_event_store.health_check.return_value = True
    
    response = client.get("/health")
    
    assert response.status_code == 200
    # Verify logging was called
    assert mock_logger.info.called


# ============================================================================
# Test Content Type
# ============================================================================

def test_analytics_responses_are_json(client, mock_event_store):
    """Test that all analytics endpoints return JSON."""
    mock_event_store.get_store_metrics.return_value = StoreMetrics(
        store_id="store_001",
        total_entries=10,
        total_exits=5,
        current_occupancy=5,
        average_visit_duration_seconds=600.0,
        time_range=None
    )
    
    response = client.get("/stores/store_001/metrics")
    
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


# ============================================================================
# Test Edge Cases
# ============================================================================

def test_metrics_with_zero_values(client, mock_event_store):
    """Test metrics with all zero values (empty store) returns 404."""
    mock_event_store.get_store_metrics.return_value = StoreMetrics(
        store_id="store_001",
        total_entries=0,
        total_exits=0,
        current_occupancy=0,
        average_visit_duration_seconds=0.0,
        time_range=None
    )
    
    response = client.get("/stores/store_001/metrics")
    
    assert response.status_code == 404


def test_funnel_with_zero_entries(client, mock_event_store):
    """Test funnel with zero entries."""
    mock_event_store.get_conversion_funnel.return_value = ConversionFunnel(
        store_id="store_001",
        stages=[
            FunnelStage(stage="entries", count=0, conversion_rate=1.0),
            FunnelStage(stage="zone_visits", count=0, conversion_rate=0.0),
            FunnelStage(stage="billing_queue_joins", count=0, conversion_rate=0.0),
            FunnelStage(stage="completed_purchases", count=0, conversion_rate=0.0)
        ],
        zone_id=None
    )
    
    response = client.get("/stores/store_001/funnel")
    
    assert response.status_code == 200
    data = response.json()
    assert data["stages"][0]["count"] == 0


def test_heatmap_default_resolution(client, mock_event_store):
    """Test that heatmap uses default resolution when not specified."""
    mock_event_store.get_heatmap.return_value = Heatmap(
        store_id="store_001",
        resolution=50,
        grid=GridDimensions(width=39, height=22),
        density=[[0.0] * 39 for _ in range(22)]
    )
    
    response = client.get("/stores/store_001/heatmap")
    
    assert response.status_code == 200
    # Verify default resolution was used
    call_args = mock_event_store.get_heatmap.call_args
    assert call_args[1]["resolution"] == 50


def test_anomalies_default_time_window(client, mock_event_store):
    """Test that anomalies uses default time window when not specified."""
    mock_event_store.detect_anomalies.return_value = []
    
    response = client.get("/stores/store_001/anomalies")
    
    assert response.status_code == 200
    # Verify default time window was used
    call_args = mock_event_store.detect_anomalies.call_args
    assert call_args[1]["time_window_hours"] == 24

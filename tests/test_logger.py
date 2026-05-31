"""Unit tests for Logger class."""

import json
import logging
import pytest
from io import StringIO
from src.logger import Logger, JSONFormatter


class TestJSONFormatter:
    """Test suite for JSONFormatter class."""
    
    def test_format_basic_log_record(self):
        """Test formatting a basic log record without extras."""
        formatter = JSONFormatter("TestComponent")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        result = formatter.format(record)
        log_data = json.loads(result)
        
        assert log_data["level"] == "INFO"
        assert log_data["component"] == "TestComponent"
        assert log_data["message"] == "Test message"
        assert "timestamp" in log_data
    
    def test_format_with_correlation_id(self):
        """Test formatting log record with correlation_id."""
        formatter = JSONFormatter("TestComponent")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.correlation_id = "req-12345"
        
        result = formatter.format(record)
        log_data = json.loads(result)
        
        assert log_data["correlation_id"] == "req-12345"
    
    def test_format_with_context(self):
        """Test formatting log record with context."""
        formatter = JSONFormatter("TestComponent")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.context = {"frame_number": 42, "count": 5}
        
        result = formatter.format(record)
        log_data = json.loads(result)
        
        assert log_data["context"] == {"frame_number": 42, "count": 5}
    
    def test_format_with_exception(self):
        """Test formatting log record with exception info."""
        formatter = JSONFormatter("TestComponent")
        
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
            
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="",
                lineno=0,
                msg="Error occurred",
                args=(),
                exc_info=exc_info
            )
            
            result = formatter.format(record)
            log_data = json.loads(result)
            
            assert "exception" in log_data
            assert "ValueError: Test error" in log_data["exception"]


class TestLogger:
    """Test suite for Logger class."""
    
    def test_init_with_default_level(self):
        """Test Logger initialization with default INFO level."""
        logger = Logger("TestComponent")
        
        assert logger.component == "TestComponent"
        assert logger._logger.level == logging.INFO
        assert logger.correlation_id is None
    
    def test_init_with_custom_level(self):
        """Test Logger initialization with custom log level."""
        logger = Logger("TestComponent", "DEBUG")
        assert logger._logger.level == logging.DEBUG
        
        logger = Logger("TestComponent", "WARNING")
        assert logger._logger.level == logging.WARNING
        
        logger = Logger("TestComponent", "ERROR")
        assert logger._logger.level == logging.ERROR
        
        logger = Logger("TestComponent", "CRITICAL")
        assert logger._logger.level == logging.CRITICAL
    
    def test_init_with_lowercase_level(self):
        """Test Logger initialization with lowercase log level."""
        logger = Logger("TestComponent", "debug")
        assert logger._logger.level == logging.DEBUG
    
    def test_init_with_invalid_level(self):
        """Test Logger initialization fails with invalid log level."""
        with pytest.raises(ValueError) as exc_info:
            Logger("TestComponent", "INVALID")
        
        error_message = str(exc_info.value)
        assert "Invalid log level" in error_message
        assert "INVALID" in error_message
    
    def test_set_correlation_id(self):
        """Test setting correlation ID."""
        logger = Logger("TestComponent")
        
        logger.set_correlation_id("req-12345")
        assert logger.correlation_id == "req-12345"
        
        logger.set_correlation_id("req-67890")
        assert logger.correlation_id == "req-67890"
    
    def test_clear_correlation_id(self):
        """Test clearing correlation ID."""
        logger = Logger("TestComponent")
        
        logger.set_correlation_id("req-12345")
        assert logger.correlation_id == "req-12345"
        
        logger.clear_correlation_id()
        assert logger.correlation_id is None
    
    def test_debug_log(self, capfd):
        """Test debug logging."""
        logger = Logger("TestComponent", "DEBUG")
        logger.debug("Debug message")
        
        captured = capfd.readouterr()
        log_data = json.loads(captured.out.strip())
        
        assert log_data["level"] == "DEBUG"
        assert log_data["component"] == "TestComponent"
        assert log_data["message"] == "Debug message"
    
    def test_info_log(self, capfd):
        """Test info logging."""
        logger = Logger("TestComponent", "INFO")
        logger.info("Info message")
        
        captured = capfd.readouterr()
        log_data = json.loads(captured.out.strip())
        
        assert log_data["level"] == "INFO"
        assert log_data["component"] == "TestComponent"
        assert log_data["message"] == "Info message"
    
    def test_warning_log(self, capfd):
        """Test warning logging."""
        logger = Logger("TestComponent", "WARNING")
        logger.warning("Warning message")
        
        captured = capfd.readouterr()
        log_data = json.loads(captured.out.strip())
        
        assert log_data["level"] == "WARNING"
        assert log_data["component"] == "TestComponent"
        assert log_data["message"] == "Warning message"
    
    def test_error_log(self, capfd):
        """Test error logging."""
        logger = Logger("TestComponent", "ERROR")
        logger.error("Error message")
        
        captured = capfd.readouterr()
        log_data = json.loads(captured.out.strip())
        
        assert log_data["level"] == "ERROR"
        assert log_data["component"] == "TestComponent"
        assert log_data["message"] == "Error message"
    
    def test_critical_log(self, capfd):
        """Test critical logging."""
        logger = Logger("TestComponent", "CRITICAL")
        logger.critical("Critical message")
        
        captured = capfd.readouterr()
        log_data = json.loads(captured.out.strip())
        
        assert log_data["level"] == "CRITICAL"
        assert log_data["component"] == "TestComponent"
        assert log_data["message"] == "Critical message"
    
    def test_log_with_context(self, capfd):
        """Test logging with context kwargs."""
        logger = Logger("TestComponent", "INFO")
        logger.info("Processing frame", frame_number=42, fps=30.5, status="ok")
        
        captured = capfd.readouterr()
        log_data = json.loads(captured.out.strip())
        
        assert log_data["message"] == "Processing frame"
        assert log_data["context"]["frame_number"] == 42
        assert log_data["context"]["fps"] == 30.5
        assert log_data["context"]["status"] == "ok"
    
    def test_log_with_correlation_id(self, capfd):
        """Test logging with correlation ID."""
        logger = Logger("TestComponent", "INFO")
        logger.set_correlation_id("req-12345")
        logger.info("Request received")
        
        captured = capfd.readouterr()
        log_data = json.loads(captured.out.strip())
        
        assert log_data["correlation_id"] == "req-12345"
        assert log_data["message"] == "Request received"
    
    def test_log_with_correlation_id_and_context(self, capfd):
        """Test logging with both correlation ID and context."""
        logger = Logger("TestComponent", "INFO")
        logger.set_correlation_id("req-12345")
        logger.info("Processing request", user_id=100, action="create")
        
        captured = capfd.readouterr()
        log_data = json.loads(captured.out.strip())
        
        assert log_data["correlation_id"] == "req-12345"
        assert log_data["message"] == "Processing request"
        assert log_data["context"]["user_id"] == 100
        assert log_data["context"]["action"] == "create"
    
    def test_log_level_filtering(self, capfd):
        """Test that log level filtering works correctly."""
        logger = Logger("TestComponent", "WARNING")
        
        # These should not appear (below WARNING level)
        logger.debug("Debug message")
        logger.info("Info message")
        
        # These should appear
        logger.warning("Warning message")
        logger.error("Error message")
        
        captured = capfd.readouterr()
        output_lines = captured.out.strip().split('\n')
        
        # Should only have 2 log entries (warning and error)
        assert len(output_lines) == 2
        
        log1 = json.loads(output_lines[0])
        log2 = json.loads(output_lines[1])
        
        assert log1["level"] == "WARNING"
        assert log2["level"] == "ERROR"
    
    def test_timestamp_format(self, capfd):
        """Test that timestamp is in ISO 8601 format."""
        logger = Logger("TestComponent", "INFO")
        logger.info("Test message")
        
        captured = capfd.readouterr()
        log_data = json.loads(captured.out.strip())
        
        # Verify timestamp exists and is a string
        assert "timestamp" in log_data
        assert isinstance(log_data["timestamp"], str)
        
        # Verify ISO 8601 format (basic check)
        timestamp = log_data["timestamp"]
        assert "T" in timestamp  # Date-time separator
        assert timestamp.endswith("Z") or "+" in timestamp or "-" in timestamp[-6:]  # Timezone
    
    def test_multiple_loggers_independent(self, capfd):
        """Test that multiple logger instances are independent."""
        logger1 = Logger("Component1", "INFO")
        logger2 = Logger("Component2", "DEBUG")
        
        logger1.set_correlation_id("req-111")
        logger2.set_correlation_id("req-222")
        
        logger1.info("Message from component 1")
        logger2.info("Message from component 2")
        
        captured = capfd.readouterr()
        output_lines = captured.out.strip().split('\n')
        
        log1 = json.loads(output_lines[0])
        log2 = json.loads(output_lines[1])
        
        assert log1["component"] == "Component1"
        assert log1["correlation_id"] == "req-111"
        
        assert log2["component"] == "Component2"
        assert log2["correlation_id"] == "req-222"
    
    def test_log_without_correlation_id(self, capfd):
        """Test that logs work correctly without correlation ID."""
        logger = Logger("TestComponent", "INFO")
        logger.info("Message without correlation ID")
        
        captured = capfd.readouterr()
        log_data = json.loads(captured.out.strip())
        
        assert "correlation_id" not in log_data
        assert log_data["message"] == "Message without correlation ID"
    
    def test_log_without_context(self, capfd):
        """Test that logs work correctly without context."""
        logger = Logger("TestComponent", "INFO")
        logger.info("Message without context")
        
        captured = capfd.readouterr()
        log_data = json.loads(captured.out.strip())
        
        assert "context" not in log_data
        assert log_data["message"] == "Message without context"
    
    def test_json_output_is_valid(self, capfd):
        """Test that all log output is valid JSON."""
        logger = Logger("TestComponent", "DEBUG")
        
        logger.debug("Debug message", value=1)
        logger.info("Info message", value=2)
        logger.warning("Warning message", value=3)
        logger.error("Error message", value=4)
        logger.critical("Critical message", value=5)
        
        captured = capfd.readouterr()
        output_lines = captured.out.strip().split('\n')
        
        # All lines should be valid JSON
        for line in output_lines:
            log_data = json.loads(line)  # Should not raise exception
            assert isinstance(log_data, dict)
            assert "timestamp" in log_data
            assert "level" in log_data
            assert "component" in log_data
            assert "message" in log_data
    
    def test_correlation_id_propagation(self, capfd):
        """Test that correlation ID is propagated across multiple log calls."""
        logger = Logger("TestComponent", "INFO")
        logger.set_correlation_id("req-12345")
        
        logger.info("First message")
        logger.info("Second message")
        logger.info("Third message")
        
        captured = capfd.readouterr()
        output_lines = captured.out.strip().split('\n')
        
        # All three logs should have the same correlation ID
        for line in output_lines:
            log_data = json.loads(line)
            assert log_data["correlation_id"] == "req-12345"
    
    def test_correlation_id_cleared_after_clear(self, capfd):
        """Test that correlation ID is not present after clearing."""
        logger = Logger("TestComponent", "INFO")
        logger.set_correlation_id("req-12345")
        logger.info("With correlation ID")
        
        logger.clear_correlation_id()
        logger.info("Without correlation ID")
        
        captured = capfd.readouterr()
        output_lines = captured.out.strip().split('\n')
        
        log1 = json.loads(output_lines[0])
        log2 = json.loads(output_lines[1])
        
        assert log1["correlation_id"] == "req-12345"
        assert "correlation_id" not in log2

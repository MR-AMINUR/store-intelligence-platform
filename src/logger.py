"""Logging module for Store Intelligence Platform.

This module provides the Logger class for structured JSON logging with
correlation ID support for tracing operations across components.
"""

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional


# Thread-local storage for correlation IDs
_correlation_context = threading.local()


class CorrelationContext:
    """Manages correlation IDs using thread-local storage.
    
    This class provides a context manager and utility methods for setting
    and retrieving correlation IDs that are automatically propagated through
    all log calls within the same thread/context.
    
    Example:
        >>> with CorrelationContext.use("req-123"):
        ...     logger.info("Processing request")  # Will include correlation_id: req-123
    """
    
    @staticmethod
    def set(correlation_id: str) -> None:
        """Set the correlation ID for the current thread.
        
        Args:
            correlation_id: Unique identifier for the current operation
        """
        _correlation_context.correlation_id = correlation_id
    
    @staticmethod
    def get() -> Optional[str]:
        """Get the correlation ID for the current thread.
        
        Returns:
            The current correlation ID, or None if not set
        """
        return getattr(_correlation_context, 'correlation_id', None)
    
    @staticmethod
    def clear() -> None:
        """Clear the correlation ID for the current thread."""
        if hasattr(_correlation_context, 'correlation_id'):
            delattr(_correlation_context, 'correlation_id')
    
    @staticmethod
    def generate() -> str:
        """Generate a new unique correlation ID.
        
        Returns:
            A new UUID-based correlation ID string
        """
        return f"corr-{uuid.uuid4().hex[:16]}"
    
    @classmethod
    def use(cls, correlation_id: Optional[str] = None) -> '_CorrelationContextManager':
        """Context manager for setting correlation ID within a scope.
        
        Args:
            correlation_id: Correlation ID to use, or None to generate a new one
        
        Returns:
            Context manager that sets and clears the correlation ID
        
        Example:
            >>> with CorrelationContext.use("req-123"):
            ...     logger.info("Processing")  # correlation_id: req-123
            >>> with CorrelationContext.use():  # Auto-generates ID
            ...     logger.info("Processing")  # correlation_id: corr-abc123...
        """
        return _CorrelationContextManager(correlation_id)


class _CorrelationContextManager:
    """Internal context manager for correlation IDs."""
    
    def __init__(self, correlation_id: Optional[str] = None) -> None:
        self.correlation_id = correlation_id or CorrelationContext.generate()
        self.previous_id: Optional[str] = None
    
    def __enter__(self) -> str:
        self.previous_id = CorrelationContext.get()
        CorrelationContext.set(self.correlation_id)
        return self.correlation_id
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        if self.previous_id is not None:
            CorrelationContext.set(self.previous_id)
        else:
            CorrelationContext.clear()
        return False


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs as structured JSON.
    
    This formatter converts log records into JSON format with fields:
    - timestamp: ISO 8601 formatted timestamp
    - level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - component: Component name that generated the log
    - correlation_id: Correlation ID from thread-local context or record
    - message: Log message
    - context: Additional context data passed via extra parameter
    """
    
    def __init__(self, component: str):
        """Initialize JSON formatter with component name.
        
        Args:
            component: Name of the component generating logs
        """
        super().__init__()
        self.component = component
    
    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON.
        
        Args:
            record: The log record to format
        
        Returns:
            JSON-formatted log string
        """
        # Build the base log structure
        log_data: Dict[str, Any] = {
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'level': record.levelname,
            'component': getattr(record, 'component', self.component),
            'message': record.getMessage(),
        }
        
        # Add correlation_id only if present and not None
        correlation_id = getattr(record, 'correlation_id', CorrelationContext.get())
        if correlation_id is not None:
            log_data['correlation_id'] = correlation_id
        
        # Add context data only if present and not None
        if hasattr(record, 'context') and record.context:
            log_data['context'] = record.context
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class Logger:
    """Structured JSON logger with correlation ID support.
    
    The Logger class provides a simple interface for logging with automatic
    JSON formatting and correlation ID propagation. Each logger is associated
    with a component name that is included in all log entries.
    
    Log entries are formatted as JSON with the following structure:
    {
        "timestamp": "2024-01-15T10:30:00.123Z",
        "level": "INFO",
        "component": "ComponentName",
        "correlation_id": "corr-abc123...",
        "message": "Log message",
        "context": {"key": "value"}
    }
    
    Example:
        >>> logger = Logger("VideoProcessor", "INFO")
        >>> logger.set_correlation_id("job-123")
        >>> logger.info("Processing started", frame_number=1)
        >>> logger.error("Processing failed", error="File not found")
    """
    
    def __init__(self, component: str, level: str = "INFO"):
        """Initialize logger for a specific component.
        
        Args:
            component: Name of the component (e.g., "VideoProcessor", "PersonDetector")
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Defaults to INFO.
        
        Raises:
            ValueError: If an invalid log level is provided
        """
        import sys
        
        self.component = component
        self.correlation_id: Optional[str] = None
        
        # Validate log level
        level_upper = level.upper()
        if level_upper not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            raise ValueError(f"Invalid log level: {level}. Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")
        
        self._logger = logging.getLogger(component)
        
        # Set log level
        self._logger.setLevel(getattr(logging, level_upper))
        
        # Remove existing handlers to avoid duplicates
        self._logger.handlers.clear()
        
        # Create console handler with JSON formatter - explicitly use sys.stdout for pytest compatibility
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter(component))
        self._logger.addHandler(handler)
        
        # Prevent propagation to root logger
        self._logger.propagate = False
    
    def set_correlation_id(self, correlation_id: str) -> None:
        """Set the correlation ID for this logger instance.
        
        Args:
            correlation_id: Unique identifier for the current operation
        """
        self.correlation_id = correlation_id
    
    def clear_correlation_id(self) -> None:
        """Clear the correlation ID for this logger instance."""
        self.correlation_id = None
    
    def _log(self, level: int, message: str, **kwargs: Any) -> None:
        """Internal method to log with context.
        
        Args:
            level: Logging level constant (e.g., logging.INFO)
            message: Log message
            **kwargs: Additional context data to include in the log
        """
        extra = {
            'component': self.component,
            'context': kwargs if kwargs else None
        }
        # Only set correlation_id in extra if logger instance has one
        # Otherwise, JSONFormatter will check CorrelationContext
        if self.correlation_id is not None:
            extra['correlation_id'] = self.correlation_id
        self._logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message.
        
        Args:
            message: Log message
            **kwargs: Additional context data (e.g., frame_number=42)
        """
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message.
        
        Args:
            message: Log message
            **kwargs: Additional context data (e.g., event_count=10)
        """
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message.
        
        Args:
            message: Log message
            **kwargs: Additional context data (e.g., retry_count=3)
        """
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message.
        
        Args:
            message: Log message
            **kwargs: Additional context data (e.g., error_code="E001")
        """
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log a critical message.
        
        Args:
            message: Log message
            **kwargs: Additional context data (e.g., system_state="shutdown")
        """
        self._log(logging.CRITICAL, message, **kwargs)

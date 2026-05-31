"""Configuration management module for Store Intelligence Platform.

This module provides the ConfigManager class for loading and accessing
configuration parameters from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from typing import Any, Optional


class ConfigManager:
    """Manages system configuration loaded from environment variables.
    
    The ConfigManager loads configuration parameters from environment variables
    and provides default values for all parameters. It exposes a simple get()
    interface for accessing configuration values throughout the application.
    
    Configuration Parameters:
        DB_PATH: Path to SQLite database file (default: ./data/events.db)
        API_HOST: API server bind address (default: 0.0.0.0)
        API_PORT: API server port (default: 8000)
        LOG_LEVEL: Logging level (default: INFO)
        YOLO_MODEL_PATH: Path to YOLOv8 model file (default: ./models/yolov8n.pt)
        CONFIDENCE_THRESHOLD: Detection confidence threshold (default: 0.5)
        TRACKER_MAX_AGE: Maximum frames to keep track alive (default: 30)
        ZONE_CONFIG_PATH: Path to zone configuration JSON (default: ./config/zones.json)
        STORE_ID: Default store ID for video processing (default: store_001)
    
    Example:
        >>> config = ConfigManager()
        >>> db_path = config.get('DB_PATH')
        >>> api_port = config.get('API_PORT')
    """
    
    # Default configuration values
    _DEFAULTS = {
        'DB_PATH': './data/events.db',
        'API_HOST': '0.0.0.0',
        'API_PORT': '8000',
        'LOG_LEVEL': 'INFO',
        'YOLO_MODEL_PATH': './models/yolov8n.pt',
        'CONFIDENCE_THRESHOLD': '0.5',
        'TRACKER_MAX_AGE': '30',
        'ZONE_CONFIG_PATH': './config/zones.json',
        'STORE_ID': 'store_001',
    }
    
    def __init__(self, validate_on_init: bool = False):
        """Initialize ConfigManager by loading configuration from environment variables.
        
        Loads all configuration parameters from os.environ, falling back to
        default values when environment variables are not set.
        
        Args:
            validate_on_init: If True, automatically validate configuration after loading.
                            Raises ValueError if validation fails.
        """
        self._config = {}
        
        # Load configuration from environment variables with defaults
        for key, default_value in self._DEFAULTS.items():
            self._config[key] = os.environ.get(key, default_value)
        
        # Optionally validate configuration on initialization
        if validate_on_init:
            self.validate()
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get configuration value by key.
        
        Retrieves the configuration value for the specified key. If the key
        is not found in the loaded configuration, returns the provided default
        value or None if no default is specified.
        
        Args:
            key: Configuration parameter name (e.g., 'DB_PATH', 'API_PORT')
            default: Default value to return if key is not found (optional)
        
        Returns:
            Configuration value as string, or the default value if key not found
        
        Example:
            >>> config = ConfigManager()
            >>> db_path = config.get('DB_PATH')
            >>> custom_value = config.get('CUSTOM_KEY', 'default_value')
        """
        return self._config.get(key, default)
    
    def validate(self) -> None:
        """Validate all configuration parameters.
        
        Validates that:
        - File paths exist (YOLO_MODEL_PATH, ZONE_CONFIG_PATH)
        - Numeric ranges are valid (CONFIDENCE_THRESHOLD 0-1, API_PORT 1-65535)
        - Required parameters are present
        
        Raises:
            ValueError: If any configuration parameter is invalid, with a descriptive
                       message indicating which parameter failed validation and why.
        
        Example:
            >>> config = ConfigManager()
            >>> config.validate()  # Raises ValueError if invalid
        """
        errors = []
        
        # Validate YOLO_MODEL_PATH exists
        yolo_model_path = self.get('YOLO_MODEL_PATH')
        if yolo_model_path:
            model_path = Path(yolo_model_path)
            if not model_path.exists():
                errors.append(
                    f"YOLO_MODEL_PATH '{yolo_model_path}' does not exist. "
                    f"Please ensure the model file is present at the specified path."
                )
        
        # Validate ZONE_CONFIG_PATH exists
        zone_config_path = self.get('ZONE_CONFIG_PATH')
        if zone_config_path:
            config_path = Path(zone_config_path)
            if not config_path.exists():
                errors.append(
                    f"ZONE_CONFIG_PATH '{zone_config_path}' does not exist. "
                    f"Please ensure the zone configuration file is present at the specified path."
                )
        
        # Validate CONFIDENCE_THRESHOLD is in range [0, 1]
        confidence_threshold = self.get('CONFIDENCE_THRESHOLD')
        if confidence_threshold:
            try:
                threshold_value = float(confidence_threshold)
                if not (0.0 <= threshold_value <= 1.0):
                    errors.append(
                        f"CONFIDENCE_THRESHOLD must be between 0 and 1, got '{confidence_threshold}'. "
                        f"Please provide a valid confidence threshold value."
                    )
            except ValueError:
                errors.append(
                    f"CONFIDENCE_THRESHOLD must be a valid number, got '{confidence_threshold}'. "
                    f"Please provide a numeric value between 0 and 1."
                )
        
        # Validate API_PORT is in range [1, 65535]
        api_port = self.get('API_PORT')
        if api_port:
            try:
                port_value = int(api_port)
                if not (1 <= port_value <= 65535):
                    errors.append(
                        f"API_PORT must be between 1 and 65535, got '{api_port}'. "
                        f"Please provide a valid port number."
                    )
            except ValueError:
                errors.append(
                    f"API_PORT must be a valid integer, got '{api_port}'. "
                    f"Please provide a numeric port value between 1 and 65535."
                )
        
        # Validate TRACKER_MAX_AGE is a positive integer
        tracker_max_age = self.get('TRACKER_MAX_AGE')
        if tracker_max_age:
            try:
                max_age_value = int(tracker_max_age)
                if max_age_value <= 0:
                    errors.append(
                        f"TRACKER_MAX_AGE must be a positive integer, got '{tracker_max_age}'. "
                        f"Please provide a positive value."
                    )
            except ValueError:
                errors.append(
                    f"TRACKER_MAX_AGE must be a valid integer, got '{tracker_max_age}'. "
                    f"Please provide a numeric value."
                )
        
        # If there are any validation errors, raise ValueError with all error messages
        if errors:
            error_message = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
            raise ValueError(error_message)

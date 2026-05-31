"""Unit tests for ConfigManager class."""

import os
import pytest
from pathlib import Path
from src.config import ConfigManager


class TestConfigManager:
    """Test suite for ConfigManager class."""
    
    def test_init_loads_defaults(self, monkeypatch):
        """Test that ConfigManager initializes with default values."""
        # Clear any environment variables that might interfere
        for key in ['DB_PATH', 'API_PORT', 'LOG_LEVEL', 'CONFIDENCE_THRESHOLD']:
            monkeypatch.delenv(key, raising=False)
        
        config = ConfigManager()
        
        # Verify all default values are loaded
        assert config.get('DB_PATH') == './data/events.db'
        assert config.get('API_HOST') == '0.0.0.0'
        assert config.get('API_PORT') == '8000'
        assert config.get('LOG_LEVEL') == 'INFO'
        assert config.get('YOLO_MODEL_PATH') == './models/yolov8n.pt'
        assert config.get('CONFIDENCE_THRESHOLD') == '0.5'
        assert config.get('TRACKER_MAX_AGE') == '30'
        assert config.get('ZONE_CONFIG_PATH') == './config/zones.json'
        assert config.get('STORE_ID') == 'store_001'
    
    def test_init_loads_from_environment(self, monkeypatch):
        """Test that ConfigManager loads values from environment variables."""
        # Set environment variables
        monkeypatch.setenv('DB_PATH', '/custom/path/db.sqlite')
        monkeypatch.setenv('API_PORT', '9000')
        monkeypatch.setenv('LOG_LEVEL', 'DEBUG')
        monkeypatch.setenv('CONFIDENCE_THRESHOLD', '0.7')
        
        config = ConfigManager()
        
        # Verify environment variables override defaults
        assert config.get('DB_PATH') == '/custom/path/db.sqlite'
        assert config.get('API_PORT') == '9000'
        assert config.get('LOG_LEVEL') == 'DEBUG'
        assert config.get('CONFIDENCE_THRESHOLD') == '0.7'
        
        # Verify non-overridden values still use defaults
        assert config.get('API_HOST') == '0.0.0.0'
        assert config.get('TRACKER_MAX_AGE') == '30'
    
    def test_get_with_default(self):
        """Test that get() returns provided default for unknown keys."""
        config = ConfigManager()
        
        # Test with custom default
        assert config.get('UNKNOWN_KEY', 'custom_default') == 'custom_default'
        
        # Test with None default (implicit)
        assert config.get('ANOTHER_UNKNOWN_KEY') is None
    
    def test_get_returns_configured_value(self, monkeypatch):
        """Test that get() returns configured values for known keys."""
        # Clear any environment variables that might interfere
        for key in ['DB_PATH', 'API_PORT']:
            monkeypatch.delenv(key, raising=False)
        
        config = ConfigManager()
        
        # Test retrieving known configuration values
        db_path = config.get('DB_PATH')
        assert db_path is not None
        assert isinstance(db_path, str)
        
        api_port = config.get('API_PORT')
        assert api_port == '8000'
    
    def test_all_parameters_defined(self):
        """Test that all required configuration parameters are defined."""
        config = ConfigManager()
        
        required_params = [
            'DB_PATH',
            'API_HOST',
            'API_PORT',
            'LOG_LEVEL',
            'YOLO_MODEL_PATH',
            'CONFIDENCE_THRESHOLD',
            'TRACKER_MAX_AGE',
            'ZONE_CONFIG_PATH',
        ]
        
        for param in required_params:
            value = config.get(param)
            assert value is not None, f"Parameter {param} should have a value"
            assert isinstance(value, str), f"Parameter {param} should be a string"


class TestConfigValidation:
    """Test suite for ConfigManager validation functionality."""
    
    def test_validate_with_missing_model_path(self, monkeypatch):
        """Test validation fails when YOLO_MODEL_PATH does not exist."""
        monkeypatch.setenv('YOLO_MODEL_PATH', '/nonexistent/model.pt')
        config = ConfigManager()
        
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        
        error_message = str(exc_info.value)
        assert "YOLO_MODEL_PATH" in error_message
        assert "/nonexistent/model.pt" in error_message
        assert "does not exist" in error_message
    
    def test_validate_with_missing_zone_config(self, monkeypatch):
        """Test validation fails when ZONE_CONFIG_PATH does not exist."""
        monkeypatch.setenv('ZONE_CONFIG_PATH', '/nonexistent/zones.json')
        config = ConfigManager()
        
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        
        error_message = str(exc_info.value)
        assert "ZONE_CONFIG_PATH" in error_message
        assert "/nonexistent/zones.json" in error_message
        assert "does not exist" in error_message
    
    def test_validate_with_invalid_confidence_threshold_too_low(self, monkeypatch):
        """Test validation fails when CONFIDENCE_THRESHOLD is below 0."""
        monkeypatch.setenv('CONFIDENCE_THRESHOLD', '-0.1')
        config = ConfigManager()
        
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        
        error_message = str(exc_info.value)
        assert "CONFIDENCE_THRESHOLD" in error_message
        assert "between 0 and 1" in error_message
    
    def test_validate_with_invalid_confidence_threshold_too_high(self, monkeypatch):
        """Test validation fails when CONFIDENCE_THRESHOLD is above 1."""
        monkeypatch.setenv('CONFIDENCE_THRESHOLD', '1.5')
        config = ConfigManager()
        
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        
        error_message = str(exc_info.value)
        assert "CONFIDENCE_THRESHOLD" in error_message
        assert "between 0 and 1" in error_message
    
    def test_validate_with_non_numeric_confidence_threshold(self, monkeypatch):
        """Test validation fails when CONFIDENCE_THRESHOLD is not a number."""
        monkeypatch.setenv('CONFIDENCE_THRESHOLD', 'invalid')
        config = ConfigManager()
        
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        
        error_message = str(exc_info.value)
        assert "CONFIDENCE_THRESHOLD" in error_message
        assert "valid number" in error_message
    
    def test_validate_with_invalid_port_too_low(self, monkeypatch):
        """Test validation fails when API_PORT is below 1."""
        monkeypatch.setenv('API_PORT', '0')
        config = ConfigManager()
        
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        
        error_message = str(exc_info.value)
        assert "API_PORT" in error_message
        assert "between 1 and 65535" in error_message
    
    def test_validate_with_invalid_port_too_high(self, monkeypatch):
        """Test validation fails when API_PORT is above 65535."""
        monkeypatch.setenv('API_PORT', '70000')
        config = ConfigManager()
        
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        
        error_message = str(exc_info.value)
        assert "API_PORT" in error_message
        assert "between 1 and 65535" in error_message
    
    def test_validate_with_non_numeric_port(self, monkeypatch):
        """Test validation fails when API_PORT is not a number."""
        monkeypatch.setenv('API_PORT', 'invalid')
        config = ConfigManager()
        
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        
        error_message = str(exc_info.value)
        assert "API_PORT" in error_message
        assert "valid integer" in error_message
    
    def test_validate_with_negative_tracker_max_age(self, monkeypatch):
        """Test validation fails when TRACKER_MAX_AGE is negative."""
        monkeypatch.setenv('TRACKER_MAX_AGE', '-5')
        config = ConfigManager()
        
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        
        error_message = str(exc_info.value)
        assert "TRACKER_MAX_AGE" in error_message
        assert "positive integer" in error_message
    
    def test_validate_with_zero_tracker_max_age(self, monkeypatch):
        """Test validation fails when TRACKER_MAX_AGE is zero."""
        monkeypatch.setenv('TRACKER_MAX_AGE', '0')
        config = ConfigManager()
        
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        
        error_message = str(exc_info.value)
        assert "TRACKER_MAX_AGE" in error_message
        assert "positive integer" in error_message
    
    def test_validate_with_non_numeric_tracker_max_age(self, monkeypatch):
        """Test validation fails when TRACKER_MAX_AGE is not a number."""
        monkeypatch.setenv('TRACKER_MAX_AGE', 'invalid')
        config = ConfigManager()
        
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        
        error_message = str(exc_info.value)
        assert "TRACKER_MAX_AGE" in error_message
        assert "valid integer" in error_message
    
    def test_validate_with_multiple_errors(self, monkeypatch):
        """Test validation reports all errors when multiple parameters are invalid."""
        monkeypatch.setenv('CONFIDENCE_THRESHOLD', '2.0')
        monkeypatch.setenv('API_PORT', '100000')
        monkeypatch.setenv('TRACKER_MAX_AGE', '-1')
        config = ConfigManager()
        
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        
        error_message = str(exc_info.value)
        # All three errors should be reported
        assert "CONFIDENCE_THRESHOLD" in error_message
        assert "API_PORT" in error_message
        assert "TRACKER_MAX_AGE" in error_message
    
    def test_validate_with_valid_config_and_existing_files(self, tmp_path, monkeypatch):
        """Test validation passes when all parameters are valid and files exist."""
        # Create temporary files
        model_file = tmp_path / "model.pt"
        model_file.touch()
        zone_config_file = tmp_path / "zones.json"
        zone_config_file.touch()
        
        # Set valid configuration
        monkeypatch.setenv('YOLO_MODEL_PATH', str(model_file))
        monkeypatch.setenv('ZONE_CONFIG_PATH', str(zone_config_file))
        monkeypatch.setenv('CONFIDENCE_THRESHOLD', '0.7')
        monkeypatch.setenv('API_PORT', '8080')
        monkeypatch.setenv('TRACKER_MAX_AGE', '50')
        
        config = ConfigManager()
        
        # Should not raise any exception
        config.validate()
    
    def test_validate_with_boundary_values(self, tmp_path, monkeypatch):
        """Test validation passes with boundary values."""
        # Create temporary files
        model_file = tmp_path / "model.pt"
        model_file.touch()
        zone_config_file = tmp_path / "zones.json"
        zone_config_file.touch()
        
        # Set boundary values
        monkeypatch.setenv('YOLO_MODEL_PATH', str(model_file))
        monkeypatch.setenv('ZONE_CONFIG_PATH', str(zone_config_file))
        monkeypatch.setenv('CONFIDENCE_THRESHOLD', '0.0')  # Lower boundary
        monkeypatch.setenv('API_PORT', '1')  # Lower boundary
        monkeypatch.setenv('TRACKER_MAX_AGE', '1')  # Lower boundary
        
        config = ConfigManager()
        config.validate()
        
        # Test upper boundaries
        monkeypatch.setenv('CONFIDENCE_THRESHOLD', '1.0')  # Upper boundary
        monkeypatch.setenv('API_PORT', '65535')  # Upper boundary
        
        config = ConfigManager()
        config.validate()
    
    def test_init_with_validate_on_init_flag(self, tmp_path, monkeypatch):
        """Test that validate_on_init flag triggers validation during initialization."""
        # Create temporary files
        model_file = tmp_path / "model.pt"
        model_file.touch()
        zone_config_file = tmp_path / "zones.json"
        zone_config_file.touch()
        
        monkeypatch.setenv('YOLO_MODEL_PATH', str(model_file))
        monkeypatch.setenv('ZONE_CONFIG_PATH', str(zone_config_file))
        
        # Should not raise with valid config
        config = ConfigManager(validate_on_init=True)
        assert config is not None
    
    def test_init_with_validate_on_init_flag_invalid_config(self, monkeypatch):
        """Test that validate_on_init flag raises error for invalid config."""
        monkeypatch.setenv('API_PORT', 'invalid')
        
        with pytest.raises(ValueError) as exc_info:
            ConfigManager(validate_on_init=True)
        
        error_message = str(exc_info.value)
        assert "API_PORT" in error_message

"""Unit tests for CLI entry points.

Tests the command-line interface for video processing and API server.
"""

import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.cli import process_video, start_api_server


class TestProcessVideoCLI:
    """Tests for process_video CLI entry point."""
    
    def test_missing_video_argument(self):
        """Test that missing --video argument shows error."""
        with patch('sys.argv', ['store-intelligence-process']):
            with pytest.raises(SystemExit) as exc_info:
                process_video()
            
            assert exc_info.value.code == 2  # argparse error code
    
    def test_video_file_not_found(self):
        """Test that non-existent video file shows error."""
        with patch('sys.argv', ['store-intelligence-process', '--video', 'nonexistent.mp4']):
            with pytest.raises(SystemExit) as exc_info:
                process_video()
            
            assert exc_info.value.code == 1
    
    def test_unsupported_video_format(self, tmp_path):
        """Test that unsupported video format shows error."""
        # Create a dummy file with unsupported extension
        video_file = tmp_path / "test.txt"
        video_file.write_text("dummy content")
        
        with patch('sys.argv', ['store-intelligence-process', '--video', str(video_file)]):
            with pytest.raises(SystemExit) as exc_info:
                process_video()
            
            assert exc_info.value.code == 1
    
    def test_config_file_not_found(self, tmp_path):
        """Test that non-existent config file shows error."""
        # Create a valid video file
        video_file = tmp_path / "test.mp4"
        video_file.write_text("dummy video content")
        
        with patch('sys.argv', [
            'store-intelligence-process',
            '--video', str(video_file),
            '--config', 'nonexistent.env'
        ]):
            with pytest.raises(SystemExit) as exc_info:
                process_video()
            
            assert exc_info.value.code == 1
    
    @patch('src.cli.VideoPipeline')
    @patch('src.cli.Logger')
    @patch('src.cli.ConfigManager')
    def test_successful_video_processing(
        self,
        mock_config,
        mock_logger,
        mock_pipeline,
        tmp_path
    ):
        """Test successful video processing flow."""
        # Create a valid video file
        video_file = tmp_path / "test.mp4"
        video_file.write_text("dummy video content")
        
        # Mock pipeline result
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.total_frames = 100
        mock_result.frames_failed = 2
        mock_result.events_generated = 50
        mock_result.events_stored = 48
        mock_result.errors = []
        
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.process.return_value = mock_result
        mock_pipeline.return_value = mock_pipeline_instance
        
        # Mock logger
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        # Mock config
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance
        
        with patch('sys.argv', ['store-intelligence-process', '--video', str(video_file)]):
            with pytest.raises(SystemExit) as exc_info:
                process_video()
            
            # Should exit with 0 for success
            assert exc_info.value.code == 0
        
        # Verify pipeline was created and run
        mock_pipeline.assert_called_once()
        mock_pipeline_instance.process.assert_called_once()
        
        # Verify logger was initialized
        mock_logger.assert_called_once()
    
    @patch('src.cli.VideoPipeline')
    @patch('src.cli.Logger')
    @patch('src.cli.ConfigManager')
    def test_failed_video_processing(
        self,
        mock_config,
        mock_logger,
        mock_pipeline,
        tmp_path
    ):
        """Test failed video processing flow."""
        # Create a valid video file
        video_file = tmp_path / "test.mp4"
        video_file.write_text("dummy video content")
        
        # Mock pipeline result with failure
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.total_frames = 50
        mock_result.frames_failed = 50
        mock_result.events_generated = 0
        mock_result.events_stored = 0
        mock_result.errors = ["Frame decode error", "Detector initialization failed"]
        
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.process.return_value = mock_result
        mock_pipeline.return_value = mock_pipeline_instance
        
        with patch('sys.argv', ['store-intelligence-process', '--video', str(video_file)]):
            with pytest.raises(SystemExit) as exc_info:
                process_video()
            
            # Should exit with 1 for failure
            assert exc_info.value.code == 1
    
    @patch('src.cli.VideoPipeline')
    @patch('src.cli.Logger')
    @patch('src.cli.ConfigManager')
    @patch('src.cli.load_dotenv')
    def test_custom_config_file(
        self,
        mock_load_dotenv,
        mock_config,
        mock_logger,
        mock_pipeline,
        tmp_path
    ):
        """Test loading custom configuration file."""
        # Create valid files
        video_file = tmp_path / "test.mp4"
        video_file.write_text("dummy video content")
        
        config_file = tmp_path / ".env.custom"
        config_file.write_text("DB_PATH=custom.db")
        
        # Mock successful processing
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.total_frames = 10
        mock_result.frames_failed = 0
        mock_result.events_generated = 5
        mock_result.events_stored = 5
        mock_result.errors = []
        
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.process.return_value = mock_result
        mock_pipeline.return_value = mock_pipeline_instance
        
        with patch('sys.argv', [
            'store-intelligence-process',
            '--video', str(video_file),
            '--config', str(config_file)
        ]):
            with pytest.raises(SystemExit) as exc_info:
                process_video()
            
            assert exc_info.value.code == 0
        
        # Verify dotenv was loaded with config file
        mock_load_dotenv.assert_called_once_with(Path(str(config_file)))
    
    @patch('src.cli.VideoPipeline')
    @patch('src.cli.Logger')
    @patch('src.cli.ConfigManager')
    def test_log_level_override(
        self,
        mock_config,
        mock_logger,
        mock_pipeline,
        tmp_path
    ):
        """Test that --log-level argument overrides default."""
        video_file = tmp_path / "test.mp4"
        video_file.write_text("dummy video content")
        
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.total_frames = 10
        mock_result.frames_failed = 0
        mock_result.events_generated = 5
        mock_result.events_stored = 5
        mock_result.errors = []
        
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.process.return_value = mock_result
        mock_pipeline.return_value = mock_pipeline_instance
        
        with patch('sys.argv', [
            'store-intelligence-process',
            '--video', str(video_file),
            '--log-level', 'DEBUG'
        ]):
            with pytest.raises(SystemExit):
                process_video()
        
        # Verify logger was initialized with DEBUG level
        mock_logger.assert_called_once_with(component="CLI", log_level="DEBUG")
    
    @patch('src.cli.VideoPipeline')
    @patch('src.cli.Logger')
    @patch('src.cli.ConfigManager')
    def test_keyboard_interrupt_handling(
        self,
        mock_config,
        mock_logger,
        mock_pipeline,
        tmp_path
    ):
        """Test that KeyboardInterrupt is handled gracefully."""
        video_file = tmp_path / "test.mp4"
        video_file.write_text("dummy video content")
        
        # Mock pipeline to raise KeyboardInterrupt
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.process.side_effect = KeyboardInterrupt()
        mock_pipeline.return_value = mock_pipeline_instance
        
        with patch('sys.argv', ['store-intelligence-process', '--video', str(video_file)]):
            with pytest.raises(SystemExit) as exc_info:
                process_video()
            
            # Should exit with code 130 (standard for SIGINT)
            assert exc_info.value.code == 130


class TestAPIServerCLI:
    """Tests for start_api_server CLI entry point."""
    
    @patch('src.cli.uvicorn')
    @patch('src.cli.Logger')
    @patch('src.cli.ConfigManager')
    def test_default_api_server_startup(
        self,
        mock_config,
        mock_logger,
        mock_uvicorn
    ):
        """Test API server startup with default settings."""
        # Mock config to return defaults
        mock_config_instance = MagicMock()
        mock_config_instance.get.side_effect = lambda key, default: {
            "API_HOST": "0.0.0.0",
            "API_PORT": 8000,
            "DB_PATH": "data/events.db"
        }.get(key, default)
        mock_config.return_value = mock_config_instance
        
        # Mock logger
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        # Mock uvicorn to exit immediately
        mock_uvicorn.run.side_effect = KeyboardInterrupt()
        
        with patch('sys.argv', ['store-intelligence-api']):
            with pytest.raises(SystemExit) as exc_info:
                start_api_server()
            
            # Should exit with 0 for clean shutdown
            assert exc_info.value.code == 0
        
        # Verify uvicorn was called with correct defaults
        mock_uvicorn.run.assert_called_once_with(
            "src.api_server:app",
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False,
            workers=1,
            access_log=True
        )
    
    @patch('src.cli.uvicorn')
    @patch('src.cli.Logger')
    @patch('src.cli.ConfigManager')
    def test_custom_host_and_port(
        self,
        mock_config,
        mock_logger,
        mock_uvicorn
    ):
        """Test API server with custom host and port."""
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance
        
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        mock_uvicorn.run.side_effect = KeyboardInterrupt()
        
        with patch('sys.argv', [
            'store-intelligence-api',
            '--host', '127.0.0.1',
            '--port', '5000'
        ]):
            with pytest.raises(SystemExit) as exc_info:
                start_api_server()
            
            assert exc_info.value.code == 0
        
        # Verify custom host and port were used
        call_args = mock_uvicorn.run.call_args
        assert call_args[1]['host'] == '127.0.0.1'
        assert call_args[1]['port'] == 5000
    
    @patch('src.cli.uvicorn')
    @patch('src.cli.Logger')
    @patch('src.cli.ConfigManager')
    def test_invalid_port_number(
        self,
        mock_config,
        mock_logger,
        mock_uvicorn
    ):
        """Test that invalid port number shows error."""
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance
        
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        with patch('sys.argv', [
            'store-intelligence-api',
            '--port', '70000'  # Invalid: > 65535
        ]):
            with pytest.raises(SystemExit) as exc_info:
                start_api_server()
            
            assert exc_info.value.code == 1
        
        # Uvicorn should not be called
        mock_uvicorn.run.assert_not_called()
    
    @patch('src.cli.uvicorn')
    @patch('src.cli.Logger')
    @patch('src.cli.ConfigManager')
    @patch('src.cli.load_dotenv')
    def test_custom_config_file(
        self,
        mock_load_dotenv,
        mock_config,
        mock_logger,
        mock_uvicorn,
        tmp_path
    ):
        """Test loading custom configuration file for API server."""
        # Create config file
        config_file = tmp_path / ".env.custom"
        config_file.write_text("API_PORT=9000")
        
        mock_config_instance = MagicMock()
        mock_config_instance.get.side_effect = lambda key, default: {
            "API_HOST": "0.0.0.0",
            "API_PORT": 9000,
            "DB_PATH": "data/events.db"
        }.get(key, default)
        mock_config.return_value = mock_config_instance
        
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        mock_uvicorn.run.side_effect = KeyboardInterrupt()
        
        with patch('sys.argv', [
            'store-intelligence-api',
            '--config', str(config_file)
        ]):
            with pytest.raises(SystemExit):
                start_api_server()
        
        # Verify dotenv was loaded
        mock_load_dotenv.assert_called_once_with(Path(str(config_file)))
    
    @patch('src.cli.uvicorn')
    @patch('src.cli.Logger')
    @patch('src.cli.ConfigManager')
    def test_reload_mode(
        self,
        mock_config,
        mock_logger,
        mock_uvicorn
    ):
        """Test API server with reload mode enabled."""
        mock_config_instance = MagicMock()
        mock_config_instance.get.side_effect = lambda key, default: {
            "API_HOST": "0.0.0.0",
            "API_PORT": 8000,
            "DB_PATH": "data/events.db"
        }.get(key, default)
        mock_config.return_value = mock_config_instance
        
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        mock_uvicorn.run.side_effect = KeyboardInterrupt()
        
        with patch('sys.argv', ['store-intelligence-api', '--reload']):
            with pytest.raises(SystemExit):
                start_api_server()
        
        # Verify reload mode was enabled and workers set to 1
        call_args = mock_uvicorn.run.call_args
        assert call_args[1]['reload'] is True
        assert call_args[1]['workers'] == 1  # Must be 1 in reload mode
    
    @patch('src.cli.uvicorn')
    @patch('src.cli.Logger')
    @patch('src.cli.ConfigManager')
    def test_multiple_workers(
        self,
        mock_config,
        mock_logger,
        mock_uvicorn
    ):
        """Test API server with multiple workers."""
        mock_config_instance = MagicMock()
        mock_config_instance.get.side_effect = lambda key, default: {
            "API_HOST": "0.0.0.0",
            "API_PORT": 8000,
            "DB_PATH": "data/events.db"
        }.get(key, default)
        mock_config.return_value = mock_config_instance
        
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        mock_uvicorn.run.side_effect = KeyboardInterrupt()
        
        with patch('sys.argv', ['store-intelligence-api', '--workers', '4']):
            with pytest.raises(SystemExit):
                start_api_server()
        
        # Verify workers setting
        call_args = mock_uvicorn.run.call_args
        assert call_args[1]['workers'] == 4
    
    @patch('src.cli.uvicorn')
    @patch('src.cli.Logger')
    @patch('src.cli.ConfigManager')
    def test_config_file_not_found(
        self,
        mock_config,
        mock_logger,
        mock_uvicorn
    ):
        """Test that non-existent config file shows error."""
        with patch('sys.argv', [
            'store-intelligence-api',
            '--config', 'nonexistent.env'
        ]):
            with pytest.raises(SystemExit) as exc_info:
                start_api_server()
            
            assert exc_info.value.code == 1
        
        # Uvicorn should not be called
        mock_uvicorn.run.assert_not_called()
    
    @patch('src.cli.uvicorn')
    @patch('src.cli.Logger')
    @patch('src.cli.ConfigManager')
    def test_exception_handling(
        self,
        mock_config,
        mock_logger,
        mock_uvicorn
    ):
        """Test that exceptions during startup are handled."""
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance
        
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        # Mock uvicorn to raise exception
        mock_uvicorn.run.side_effect = Exception("Server startup failed")
        
        with patch('sys.argv', ['store-intelligence-api']):
            with pytest.raises(SystemExit) as exc_info:
                start_api_server()
            
            assert exc_info.value.code == 1


class TestCLIHelpText:
    """Tests for CLI help text and documentation."""
    
    def test_process_video_help(self):
        """Test that --help works for process_video."""
        with patch('sys.argv', ['store-intelligence-process', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                process_video()
            
            # argparse exits with 0 for --help
            assert exc_info.value.code == 0
    
    def test_api_server_help(self):
        """Test that --help works for start_api_server."""
        with patch('sys.argv', ['store-intelligence-api', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                start_api_server()
            
            # argparse exits with 0 for --help
            assert exc_info.value.code == 0

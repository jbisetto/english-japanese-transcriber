"""Tests for the DemoLogger class."""

import os
import json
import logging
import pytest
from pathlib import Path
from datetime import datetime
from demo.utils.logger import DemoLogger

@pytest.fixture
def temp_log_dir(tmp_path):
    """Create a temporary log directory."""
    log_dir = tmp_path / "test_logs"
    log_dir.mkdir()
    return str(log_dir)

@pytest.fixture
def demo_logger(temp_log_dir):
    """Create a DemoLogger instance with a temporary directory."""
    return DemoLogger(name="test_logger", level="DEBUG", log_dir=temp_log_dir)

def test_init_creates_directory(temp_log_dir):
    """Test that initialization creates the log directory."""
    logger = DemoLogger(log_dir=temp_log_dir)
    assert Path(temp_log_dir).exists()
    assert Path(temp_log_dir).is_dir()

def test_log_levels(demo_logger):
    """Test that all log levels work correctly."""
    demo_logger.debug("Debug message")
    demo_logger.info("Info message")
    demo_logger.warning("Warning message")
    demo_logger.error("Error message")
    demo_logger.critical("Critical message")
    
    # Check log file exists and contains messages
    log_files = list(Path(demo_logger.log_dir).glob("*.log"))
    assert len(log_files) == 1
    
    log_content = log_files[0].read_text()
    assert "Debug message" in log_content
    assert "Info message" in log_content
    assert "Warning message" in log_content
    assert "Error message" in log_content
    assert "Critical message" in log_content

def test_error_tracking(demo_logger):
    """Test error tracking functionality."""
    # Generate some errors
    test_exception = ValueError("Test error")
    demo_logger.error("Error 1")
    demo_logger.error("Error 2", exc_info=test_exception)
    demo_logger.critical("Critical error", exc_info=test_exception)
    
    # Check error history
    history = demo_logger.get_error_history()
    assert len(history) == 3
    
    # Check error entry structure
    error_entry = history[0]
    assert 'timestamp' in error_entry
    assert 'level' in error_entry
    assert 'message' in error_entry
    assert 'exception' in error_entry
    
    # Check exception info
    assert history[1]['exception'] == str(test_exception)
    assert history[1]['message'] == "Error 2"
    assert history[1]['level'] == "ERROR"

def test_error_history_limit(demo_logger):
    """Test that error history is limited to 100 entries."""
    # Generate 110 errors
    for i in range(110):
        demo_logger.error(f"Error {i}")
    
    history = demo_logger.get_error_history()
    assert len(history) == 100
    assert history[0]['message'] == "Error 10"
    assert history[-1]['message'] == "Error 109"

def test_get_error_history_with_limit(demo_logger):
    """Test getting limited error history."""
    for i in range(5):
        demo_logger.error(f"Error {i}")
    
    history = demo_logger.get_error_history(limit=3)
    assert len(history) == 3
    assert history[0]['message'] == "Error 2"
    assert history[-1]['message'] == "Error 4"

def test_export_error_history(demo_logger, temp_log_dir):
    """Test exporting error history to JSON."""
    # Generate some errors
    demo_logger.error("Test error 1")
    demo_logger.critical("Test error 2")
    
    # Export to file
    export_file = os.path.join(temp_log_dir, "error_history.json")
    result = demo_logger.export_error_history(export_file)
    
    assert result == export_file
    assert os.path.exists(export_file)
    
    # Check JSON content
    with open(export_file) as f:
        data = json.load(f)
    
    assert data['logger_name'] == "test_logger"
    assert 'export_time' in data
    assert len(data['errors']) == 2
    assert data['errors'][0]['message'] == "Test error 1"
    assert data['errors'][1]['message'] == "Test error 2"

def test_export_error_history_without_file(demo_logger):
    """Test exporting error history without file."""
    demo_logger.error("Test error")
    
    result = demo_logger.export_error_history()
    assert isinstance(result, dict)
    assert result['logger_name'] == "test_logger"
    assert len(result['errors']) == 1
    assert result['errors'][0]['message'] == "Test error"

def test_custom_format_string(temp_log_dir):
    """Test logger with custom format string."""
    format_string = "%(levelname)s: %(message)s"
    logger = DemoLogger(
        name="format_test",
        log_dir=temp_log_dir,
        format_string=format_string
    )
    
    logger.info("Test message")
    
    log_files = list(Path(logger.log_dir).glob("*.log"))
    log_content = log_files[0].read_text()
    
    assert "INFO: Test message" in log_content 
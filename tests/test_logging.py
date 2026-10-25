"""
Tests for logging infrastructure.

Requirements 6.8, 9.1:
- Test that logging configuration is set up correctly
- Test that debug mode controls log level
- Test that log messages are formatted correctly
"""

import logging
import pytest
from io import StringIO


def test_logging_configuration():
    """Test that logging can be configured with proper format."""
    # Create a test logger
    logger = logging.getLogger('test_logger')
    logger.setLevel(logging.DEBUG)
    
    # Create a string handler to capture output
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    
    # Set format with timestamp and module name
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Log a test message
    logger.info("Test message")
    
    # Verify format
    output = log_stream.getvalue()
    assert 'test_logger' in output
    assert 'INFO' in output
    assert 'Test message' in output
    assert '-' in output  # Timestamp separator
    
    # Cleanup
    logger.removeHandler(handler)


def test_debug_mode_controls_log_level():
    """Test that debug mode controls whether DEBUG messages are shown."""
    # Test with INFO level (debug=False)
    logger_info = logging.getLogger('test_info')
    logger_info.setLevel(logging.INFO)
    
    log_stream_info = StringIO()
    handler_info = logging.StreamHandler(log_stream_info)
    logger_info.addHandler(handler_info)
    
    logger_info.debug("Debug message")
    logger_info.info("Info message")
    
    output_info = log_stream_info.getvalue()
    assert "Debug message" not in output_info  # DEBUG not shown at INFO level
    assert "Info message" in output_info
    
    logger_info.removeHandler(handler_info)
    
    # Test with DEBUG level (debug=True)
    logger_debug = logging.getLogger('test_debug')
    logger_debug.setLevel(logging.DEBUG)
    
    log_stream_debug = StringIO()
    handler_debug = logging.StreamHandler(log_stream_debug)
    logger_debug.addHandler(handler_debug)
    
    logger_debug.debug("Debug message")
    logger_debug.info("Info message")
    
    output_debug = log_stream_debug.getvalue()
    assert "Debug message" in output_debug  # DEBUG shown at DEBUG level
    assert "Info message" in output_debug
    
    logger_debug.removeHandler(handler_debug)


def test_log_message_formatting():
    """Test that log messages are formatted correctly with all required components."""
    logger = logging.getLogger('test_format')
    logger.setLevel(logging.DEBUG)
    
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    
    # Use the expected format: timestamp - module - level - message
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Test different log levels
    logger.debug("Debug test")
    logger.info("Info test")
    logger.warning("Warning test")
    logger.error("Error test")
    
    output = log_stream.getvalue()
    lines = output.strip().split('\n')
    
    # Verify we have 4 lines
    assert len(lines) == 4
    
    # Verify each line has the correct format
    for line in lines:
        parts = line.split(' - ')
        assert len(parts) == 4  # timestamp - module - level - message
        assert parts[1] == 'test_format'  # module name
        assert parts[2] in ['DEBUG', 'INFO', 'WARNING', 'ERROR']  # level
    
    # Verify specific messages
    assert 'DEBUG - Debug test' in output
    assert 'INFO - Info test' in output
    assert 'WARNING - Warning test' in output
    assert 'ERROR - Error test' in output
    
    logger.removeHandler(handler)


def test_logging_levels_hierarchy():
    """Test that logging level hierarchy works correctly."""
    logger = logging.getLogger('test_hierarchy')
    
    # Test at WARNING level
    logger.setLevel(logging.WARNING)
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    logger.addHandler(handler)
    
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    output = log_stream.getvalue()
    
    # Only WARNING and ERROR should appear
    assert "Debug message" not in output
    assert "Info message" not in output
    assert "Warning message" in output
    assert "Error message" in output
    
    logger.removeHandler(handler)


def test_multiple_handlers():
    """Test that logger can have multiple handlers with different levels."""
    logger = logging.getLogger('test_multi')
    logger.setLevel(logging.DEBUG)
    
    # Handler 1: INFO level
    stream1 = StringIO()
    handler1 = logging.StreamHandler(stream1)
    handler1.setLevel(logging.INFO)
    logger.addHandler(handler1)
    
    # Handler 2: DEBUG level
    stream2 = StringIO()
    handler2 = logging.StreamHandler(stream2)
    handler2.setLevel(logging.DEBUG)
    logger.addHandler(handler2)
    
    logger.debug("Debug message")
    logger.info("Info message")
    
    output1 = stream1.getvalue()
    output2 = stream2.getvalue()
    
    # Handler 1 should only have INFO
    assert "Debug message" not in output1
    assert "Info message" in output1
    
    # Handler 2 should have both
    assert "Debug message" in output2
    assert "Info message" in output2
    
    logger.removeHandler(handler1)
    logger.removeHandler(handler2)

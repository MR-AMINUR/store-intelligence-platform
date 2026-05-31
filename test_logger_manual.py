"""Manual test script for Logger and CorrelationContext functionality."""

import json
import sys
from io import StringIO

# Add src to path
sys.path.insert(0, 'src')

from logger import Logger, CorrelationContext


def test_basic_logging():
    """Test basic logging functionality."""
    print("=" * 60)
    print("Test 1: Basic Logging")
    print("=" * 60)
    
    logger = Logger("TestComponent", "INFO")
    
    # Capture output
    old_stderr = sys.stderr
    sys.stderr = StringIO()
    
    logger.info("Test message", key1="value1", key2=42)
    
    output = sys.stderr.getvalue()
    sys.stderr = old_stderr
    
    print("Output:", output)
    
    # Parse JSON
    log_entry = json.loads(output.strip())
    print("Parsed JSON:")
    for key, value in log_entry.items():
        print(f"  {key}: {value}")
    
    # Verify structure
    assert 'timestamp' in log_entry
    assert log_entry['level'] == 'INFO'
    assert log_entry['component'] == 'TestComponent'
    assert log_entry['message'] == 'Test message'
    assert log_entry['context']['key1'] == 'value1'
    assert log_entry['context']['key2'] == 42
    
    print("✓ Basic logging test passed\n")


def test_correlation_id_manual():
    """Test correlation ID with manual set/get."""
    print("=" * 60)
    print("Test 2: Correlation ID - Manual Set/Get")
    print("=" * 60)
    
    logger = Logger("TestComponent", "INFO")
    
    # Set correlation ID manually
    CorrelationContext.set("manual-corr-123")
    
    # Capture output
    old_stderr = sys.stderr
    sys.stderr = StringIO()
    
    logger.info("Message with manual correlation ID")
    
    output = sys.stderr.getvalue()
    sys.stderr = old_stderr
    
    print("Output:", output)
    
    # Parse JSON
    log_entry = json.loads(output.strip())
    print("Parsed JSON:")
    for key, value in log_entry.items():
        print(f"  {key}: {value}")
    
    # Verify correlation ID
    assert log_entry['correlation_id'] == 'manual-corr-123'
    
    # Clear correlation ID
    CorrelationContext.clear()
    
    print("✓ Manual correlation ID test passed\n")


def test_correlation_id_context_manager():
    """Test correlation ID with context manager."""
    print("=" * 60)
    print("Test 3: Correlation ID - Context Manager")
    print("=" * 60)
    
    logger = Logger("TestComponent", "INFO")
    
    # Capture output
    old_stderr = sys.stderr
    sys.stderr = StringIO()
    
    # Use context manager with explicit ID
    with CorrelationContext.use("ctx-456"):
        logger.info("Message inside context")
    
    # Log outside context (should have no correlation ID)
    logger.info("Message outside context")
    
    output = sys.stderr.getvalue()
    sys.stderr = old_stderr
    
    lines = output.strip().split('\n')
    print(f"Output ({len(lines)} lines):")
    for i, line in enumerate(lines, 1):
        print(f"  Line {i}: {line}")
    
    # Parse both log entries
    log_entry_1 = json.loads(lines[0])
    log_entry_2 = json.loads(lines[1])
    
    print("\nParsed JSON 1 (inside context):")
    for key, value in log_entry_1.items():
        print(f"  {key}: {value}")
    
    print("\nParsed JSON 2 (outside context):")
    for key, value in log_entry_2.items():
        print(f"  {key}: {value}")
    
    # Verify correlation IDs
    assert log_entry_1['correlation_id'] == 'ctx-456'
    assert log_entry_2['correlation_id'] is None
    
    print("✓ Context manager test passed\n")


def test_correlation_id_auto_generate():
    """Test auto-generated correlation ID."""
    print("=" * 60)
    print("Test 4: Correlation ID - Auto-Generate")
    print("=" * 60)
    
    logger = Logger("TestComponent", "INFO")
    
    # Capture output
    old_stderr = sys.stderr
    sys.stderr = StringIO()
    
    # Use context manager without explicit ID (auto-generate)
    with CorrelationContext.use() as corr_id:
        print(f"Auto-generated correlation ID: {corr_id}")
        logger.info("Message with auto-generated ID")
    
    output = sys.stderr.getvalue()
    sys.stderr = old_stderr
    
    print("Output:", output)
    
    # Parse JSON
    log_entry = json.loads(output.strip())
    print("Parsed JSON:")
    for key, value in log_entry.items():
        print(f"  {key}: {value}")
    
    # Verify correlation ID exists and starts with 'corr-'
    assert log_entry['correlation_id'] is not None
    assert log_entry['correlation_id'].startswith('corr-')
    assert log_entry['correlation_id'] == corr_id
    
    print("✓ Auto-generate correlation ID test passed\n")


def test_nested_contexts():
    """Test nested correlation contexts."""
    print("=" * 60)
    print("Test 5: Nested Correlation Contexts")
    print("=" * 60)
    
    logger = Logger("TestComponent", "INFO")
    
    # Capture output
    old_stderr = sys.stderr
    sys.stderr = StringIO()
    
    with CorrelationContext.use("outer-ctx"):
        logger.info("Outer context")
        
        with CorrelationContext.use("inner-ctx"):
            logger.info("Inner context")
        
        logger.info("Back to outer context")
    
    output = sys.stderr.getvalue()
    sys.stderr = old_stderr
    
    lines = output.strip().split('\n')
    print(f"Output ({len(lines)} lines):")
    for i, line in enumerate(lines, 1):
        print(f"  Line {i}: {line}")
    
    # Parse log entries
    log_entries = [json.loads(line) for line in lines]
    
    for i, entry in enumerate(log_entries, 1):
        print(f"\nParsed JSON {i}:")
        for key, value in entry.items():
            print(f"  {key}: {value}")
    
    # Verify correlation IDs
    assert log_entries[0]['correlation_id'] == 'outer-ctx'
    assert log_entries[1]['correlation_id'] == 'inner-ctx'
    assert log_entries[2]['correlation_id'] == 'outer-ctx'
    
    print("✓ Nested contexts test passed\n")


def test_log_levels():
    """Test different log levels."""
    print("=" * 60)
    print("Test 6: Log Levels")
    print("=" * 60)
    
    logger = Logger("TestComponent", "DEBUG")
    
    # Capture output
    old_stderr = sys.stderr
    sys.stderr = StringIO()
    
    with CorrelationContext.use("level-test"):
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
    
    output = sys.stderr.getvalue()
    sys.stderr = old_stderr
    
    lines = output.strip().split('\n')
    print(f"Output ({len(lines)} lines):")
    
    expected_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    
    for i, (line, expected_level) in enumerate(zip(lines, expected_levels), 1):
        log_entry = json.loads(line)
        print(f"\n  Line {i} ({expected_level}):")
        print(f"    level: {log_entry['level']}")
        print(f"    message: {log_entry['message']}")
        print(f"    correlation_id: {log_entry['correlation_id']}")
        
        assert log_entry['level'] == expected_level
        assert log_entry['correlation_id'] == 'level-test'
    
    print("\n✓ Log levels test passed\n")


if __name__ == "__main__":
    try:
        test_basic_logging()
        test_correlation_id_manual()
        test_correlation_id_context_manager()
        test_correlation_id_auto_generate()
        test_nested_contexts()
        test_log_levels()
        
        print("=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

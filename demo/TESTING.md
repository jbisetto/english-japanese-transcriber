# Testing Guide

This document describes the testing setup for the English-Japanese Transcription Demo.

## Running Tests

To run all tests:
```bash
python -m pytest tests/ -v
```

To run specific test files:
```bash
python -m pytest tests/test_web_ui.py -v
python -m pytest tests/test_output_handler.py -v
```

To run tests with coverage:
```bash
python -m pytest tests/ --cov=demo --cov-report=term-missing
```

## Test Structure

The test suite is organized into several categories:

### Component Tests

1. **Audio Handler Tests** (`test_audio_handler.py`)
   - Audio format validation
   - Recording management
   - File upload processing
   - Audio information extraction
   - Cleanup functionality

2. **Output Handler Tests** (`test_output_handler.py`)
   - Format processing (TXT, JSON, SRT)
   - Language-specific formatting
   - Output preview generation
   - File saving and management
   - Error handling

3. **Web UI Tests** (`test_web_ui.py`)
   - Interface initialization
   - Event handling
   - Transcription processing
   - Error handling
   - Progress updates
   - Cleanup operations

4. **Configuration Tests** (`test_config.py`)
   - Cloud provider detection
   - Environment validation
   - Service status checks
   - Configuration loading
   - Error handling

5. **Logger Tests** (`test_logger.py`)
   - Log level management
   - Error tracking
   - History management
   - Export functionality
   - Format validation

6. **Resource Manager Tests** (`test_resource_manager.py`)
   - File cleanup
   - Resource monitoring
   - System health checks
   - Emergency cleanup
   - Error handling

### Integration Tests

Integration tests are included in each component test file and verify:
- Audio processing pipeline
- Transcription workflow
- Output generation chain
- Resource management lifecycle
- Error handling flow

### Test Fixtures

Common test fixtures are provided for:
- Temporary directories
- Sample audio files
- Mock handlers
- Configuration objects
- Logger instances

### Test Coverage

The test suite aims for high coverage of critical components:
- Core functionality: 100%
- Error handling: 100%
- Edge cases: 90%+
- UI components: 90%+

## Adding New Tests

When adding new tests:

1. Follow the existing test structure
2. Use appropriate fixtures
3. Test both success and failure cases
4. Include docstrings explaining test purpose
5. Verify error handling
6. Check resource cleanup

## Test Dependencies

Required packages for testing:
- pytest
- pytest-asyncio
- pytest-cov
- pytest-mock

Install with:
```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

## Common Issues

1. **Async Test Failures**
   - Ensure `@pytest.mark.asyncio` is used for async tests
   - Check for proper async/await usage
   - Verify event loop handling

2. **Resource Cleanup**
   - Use `tmp_path` fixture for temporary files
   - Implement proper cleanup in teardown
   - Check for resource leaks

3. **Mock Objects**
   - Use appropriate mock types (Mock, AsyncMock)
   - Set necessary return values
   - Verify call counts and arguments

## CI/CD Integration

Tests are run automatically on:
- Pull requests
- Main branch commits
- Release tags

Failed tests block merges and deployments. 
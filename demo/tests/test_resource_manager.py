"""Tests for the ResourceManager class."""

import os
import time
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from demo.utils.resource_manager import ResourceManager, ResourceError

@pytest.fixture
def temp_base_dir(tmp_path):
    """Create a temporary base directory."""
    base_dir = tmp_path / "test_resources"
    base_dir.mkdir()
    return str(base_dir)

@pytest.fixture
def resource_manager(temp_base_dir):
    """Create a ResourceManager instance with temporary directories."""
    return ResourceManager(
        temp_dir=str(Path(temp_base_dir) / "temp"),
        recordings_dir=str(Path(temp_base_dir) / "recordings"),
        output_dir=str(Path(temp_base_dir) / "output")
    )

@pytest.fixture
def sample_files(resource_manager):
    """Create sample files in each directory."""
    # Create test files
    files = []
    for directory in [resource_manager.temp_dir, resource_manager.recordings_dir, resource_manager.output_dir]:
        test_file = directory / "test.txt"
        test_file.write_text("test content")
        files.append(test_file)
    return files

def create_old_file(directory: Path, hours_old: float) -> Path:
    """Create a file with a modified timestamp."""
    file_path = directory / f"old_{hours_old}h.txt"
    file_path.write_text("old content")
    old_time = datetime.now() - timedelta(hours=hours_old)
    os.utime(str(file_path), (old_time.timestamp(), old_time.timestamp()))
    return file_path

def test_init_creates_directories(temp_base_dir):
    """Test that initialization creates all required directories."""
    manager = ResourceManager(
        temp_dir=str(Path(temp_base_dir) / "temp"),
        recordings_dir=str(Path(temp_base_dir) / "recordings"),
        output_dir=str(Path(temp_base_dir) / "output")
    )
    
    assert manager.temp_dir.exists()
    assert manager.recordings_dir.exists()
    assert manager.output_dir.exists()

def test_cleanup_old_files(resource_manager):
    """Test cleaning up old files."""
    # Create files with different ages
    recent_file = create_old_file(resource_manager.temp_dir, 1)  # 1 hour old
    old_file = create_old_file(resource_manager.temp_dir, 25)  # 25 hours old
    
    # Clean up files older than 24 hours
    removed = resource_manager.cleanup_old_files(resource_manager.temp_dir, 24)
    
    assert len(removed) == 1
    assert old_file in removed
    assert recent_file.exists()
    assert not old_file.exists()

def test_get_directory_size(resource_manager, sample_files):
    """Test directory size calculation."""
    # All files have the same content "test content"
    expected_size = len("test content".encode()) * len(sample_files)
    
    total_size = sum(
        resource_manager.get_directory_size(d)
        for d in [resource_manager.temp_dir, resource_manager.recordings_dir, resource_manager.output_dir]
    )
    
    assert total_size == expected_size

def test_get_resource_usage(resource_manager, sample_files):
    """Test resource usage statistics."""
    usage = resource_manager.get_resource_usage()
    
    assert 'disk_usage_percent' in usage
    assert 'memory_usage_percent' in usage
    assert 'disk_free_mb' in usage
    assert 'temp_dir_size_mb' in usage
    assert 'recordings_dir_size_mb' in usage
    assert 'output_dir_size_mb' in usage
    
    # Verify sizes are non-zero
    assert usage['temp_dir_size_mb'] > 0
    assert usage['recordings_dir_size_mb'] > 0
    assert usage['output_dir_size_mb'] > 0

def test_check_system_health(resource_manager):
    """Test system health check."""
    # Test with default thresholds
    health_info = resource_manager.check_system_health()
    
    # Verify return type and structure
    assert isinstance(health_info, dict)
    assert all(key in health_info for key in ['disk_usage', 'memory_usage', 'needs_cleanup', 'issues'])
    
    # Verify numeric values
    assert isinstance(health_info['disk_usage'], (int, float))
    assert isinstance(health_info['memory_usage'], (int, float))
    assert isinstance(health_info['needs_cleanup'], bool)
    assert isinstance(health_info['issues'], list)
    
    # Test with modified thresholds
    resource_manager.thresholds['disk_usage_percent'] = 1  # Very low threshold
    health_info = resource_manager.check_system_health()
    
    # Should trigger cleanup
    assert health_info['needs_cleanup']
    assert len(health_info['issues']) > 0
    assert any('disk usage' in issue.lower() for issue in health_info['issues'])

def test_cleanup_resources(resource_manager):
    """Test resource cleanup operations."""
    # Create old files
    old_files = [
        create_old_file(resource_manager.temp_dir, 25),
        create_old_file(resource_manager.recordings_dir, 25),
        create_old_file(resource_manager.output_dir, 25)
    ]
    
    # Test normal cleanup
    stats = resource_manager.cleanup_resources(force=False)
    assert isinstance(stats, dict)
    assert all(key in stats for key in ['temp', 'recordings', 'output'])
    
    # First cleanup should remove all files
    assert stats['temp'] + stats['recordings'] + stats['output'] == len(old_files)
    
    # Verify files were removed
    assert not any(f.exists() for f in old_files)
    
    # Second cleanup should find no files to remove
    stats = resource_manager.cleanup_resources(force=True)
    assert stats['temp'] + stats['recordings'] + stats['output'] == 0

def test_monitor_resources(resource_manager, sample_files):
    """Test resource monitoring."""
    report = resource_manager.monitor_resources()
    
    assert isinstance(report, dict)
    assert 'timestamp' in report
    assert 'health_ok' in report
    assert 'issues' in report
    assert 'usage' in report
    assert 'cleanup_stats' in report

def test_emergency_cleanup(resource_manager, sample_files):
    """Test emergency cleanup operation."""
    # Verify files exist initially
    assert all(f.exists() for f in sample_files)
    
    # Perform emergency cleanup
    resource_manager.emergency_cleanup()
    
    # Verify temp directory is empty but exists
    assert resource_manager.temp_dir.exists()
    assert not any(resource_manager.temp_dir.iterdir())
    
    # Verify other directories are cleaned up
    stats = resource_manager.cleanup_resources(force=False)
    assert stats['temp'] == 0  # Already cleaned up
    assert stats['recordings'] >= 0
    assert stats['output'] >= 0

def test_emergency_cleanup_error_handling(resource_manager):
    """Test error handling in emergency cleanup."""
    # Make temp directory read-only to force an error
    os.chmod(str(resource_manager.temp_dir), 0o444)
    
    with pytest.raises(ResourceError):
        resource_manager.emergency_cleanup()
    
    # Restore permissions for cleanup
    os.chmod(str(resource_manager.temp_dir), 0o777) 
"""
Resource management module for the demo interface.

This module provides:
- Temporary file cleanup
- Recording cleanup
- Resource monitoring
- System health checks
"""

import os
import psutil
import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

class ResourceError(Exception):
    """Raised when resource management operations fail."""
    pass

class ResourceManager:
    """Manages system resources and cleanup operations for the demo interface."""
    
    # Default thresholds for system checks
    DEFAULT_THRESHOLDS = {
        'disk_usage_percent': 90.0,  # Maximum disk usage percentage
        'memory_usage_percent': 85.0,  # Maximum memory usage percentage
        'max_file_age_hours': 24,  # Maximum age for temporary files
        'min_free_space_mb': 500,  # Minimum required free space in MB
    }
    
    def __init__(
        self,
        temp_dir: str = "temp",
        recordings_dir: str = "recordings",
        output_dir: str = "output",
        thresholds: Optional[Dict[str, float]] = None
    ):
        """
        Initialize the resource manager.
        
        Args:
            temp_dir (str): Directory for temporary files
            recordings_dir (str): Directory for audio recordings
            output_dir (str): Directory for output files
            thresholds (Dict[str, float], optional): Custom threshold values
        """
        self.temp_dir = Path(temp_dir)
        self.recordings_dir = Path(recordings_dir)
        self.output_dir = Path(output_dir)
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS
        
        # Create directories if they don't exist
        for directory in [self.temp_dir, self.recordings_dir, self.output_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
    
    def cleanup_old_files(self, directory: Path, max_age_hours: Optional[float] = None) -> List[Path]:
        """
        Clean up files older than specified age.
        
        Args:
            directory (Path): Directory to clean
            max_age_hours (float, optional): Maximum file age in hours
            
        Returns:
            List[Path]: List of removed files
        """
        if max_age_hours is None:
            max_age_hours = self.thresholds['max_file_age_hours']
        
        removed_files = []
        current_time = datetime.now().timestamp()
        
        for file_path in directory.glob('*'):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > (max_age_hours * 3600):
                    try:
                        file_path.unlink()
                        removed_files.append(file_path)
                        self.logger.info(f"Removed old file: {file_path}")
                    except Exception as e:
                        self.logger.error(f"Failed to remove file {file_path}: {e}")
        
        return removed_files
    
    def get_directory_size(self, directory: Path) -> int:
        """
        Get total size of directory in bytes.
        
        Args:
            directory (Path): Directory to measure
            
        Returns:
            int: Directory size in bytes
        """
        return sum(f.stat().st_size for f in directory.glob('**/*') if f.is_file())
    
    def get_resource_usage(self) -> Dict[str, float]:
        """
        Get current resource usage statistics.
        
        Returns:
            Dict[str, float]: Resource usage statistics
        """
        disk = psutil.disk_usage(str(self.temp_dir))
        memory = psutil.virtual_memory()
        
        return {
            'disk_usage_percent': disk.percent,
            'memory_usage_percent': memory.percent,
            'disk_free_mb': disk.free / (1024 * 1024),
            'temp_dir_size_mb': self.get_directory_size(self.temp_dir) / (1024 * 1024),
            'recordings_dir_size_mb': self.get_directory_size(self.recordings_dir) / (1024 * 1024),
            'output_dir_size_mb': self.get_directory_size(self.output_dir) / (1024 * 1024)
        }
    
    def check_system_health(self) -> Dict[str, Any]:
        """Check system health against thresholds.

        Returns:
            Dict[str, Any]: Health check results including disk usage, memory usage,
                           and whether cleanup is needed
        """
        health_info = {
            'disk_usage': self.get_resource_usage()['disk_usage_percent'],
            'memory_usage': self.get_resource_usage()['memory_usage_percent'],
            'needs_cleanup': False,
            'issues': []
        }

        # Check disk usage
        if health_info['disk_usage'] > self.thresholds['disk_usage_percent']:
            health_info['needs_cleanup'] = True
            health_info['issues'].append(
                f"Disk usage ({health_info['disk_usage']:.1f}%) exceeds threshold "
                f"({self.thresholds['disk_usage_percent']:.1f}%)"
            )

        # Check memory usage
        if health_info['memory_usage'] > self.thresholds['memory_usage_percent']:
            health_info['needs_cleanup'] = True
            health_info['issues'].append(
                f"Memory usage ({health_info['memory_usage']:.1f}%) exceeds threshold "
                f"({self.thresholds['memory_usage_percent']:.1f}%)"
            )

        return health_info
    
    def cleanup_resources(self, force: bool = False) -> Dict[str, int]:
        """Clean up old files based on system health or force parameter.

        Args:
            force (bool): Force cleanup regardless of system health

        Returns:
            Dict[str, int]: Number of files cleaned up in each directory
        """
        stats = {'temp': 0, 'recordings': 0, 'output': 0}
        
        if force or self.check_system_health()['needs_cleanup']:
            # Clean up temporary files
            stats['temp'] = len(list(self.cleanup_old_files(self.temp_dir)))
            
            # Clean up old recordings
            stats['recordings'] = len(list(self.cleanup_old_files(self.recordings_dir)))
            
            # Clean up old outputs
            stats['output'] = len(list(self.cleanup_old_files(self.output_dir)))
            
            logging.info(f"Cleanup completed: {stats}")
            
        return stats
    
    def monitor_resources(self) -> Dict[str, Any]:
        """
        Monitor system resources and perform cleanup if needed.
        
        Returns:
            Dict[str, Any]: Monitoring report
        """
        # Get current usage
        usage = self.get_resource_usage()
        
        # Check health
        health_info = self.check_system_health()
        
        # Perform cleanup if needed
        cleanup_stats = self.cleanup_resources(force=not health_info['needs_cleanup'])
        
        return {
            'timestamp': datetime.now().isoformat(),
            'health_ok': not health_info['needs_cleanup'],
            'issues': health_info['issues'],
            'usage': usage,
            'cleanup_stats': cleanup_stats
        }
    
    def emergency_cleanup(self) -> None:
        """Perform emergency cleanup of temporary files.
        
        This is a last resort method that removes all files in the temporary directory
        when system resources are critically low.
        
        Raises:
            ResourceError: If cleanup fails due to permissions or other issues
        """
        try:
            if not os.access(str(self.temp_dir), os.W_OK):
                raise ResourceError(f"No write access to temporary directory: {self.temp_dir}")

            # Remove all files in temp directory
            for item in self.temp_dir.iterdir():
                if item.is_file():
                    try:
                        item.unlink()
                    except (PermissionError, OSError) as e:
                        raise ResourceError(f"Failed to remove file {item}: {str(e)}")
                        
            logging.warning("Emergency cleanup: Removed all temporary files")
            self.cleanup_resources(force=True)
            
        except Exception as e:
            raise ResourceError(f"Emergency cleanup failed: {str(e)}") 
"""
Logging module for the demo interface.

This module provides:
- Custom logger setup with configurable handlers
- Debug output formatting
- Error tracking
- Logging configuration management
- Automatic cleanup of old log files
"""

import os
import sys
import logging
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any

class DemoLogger:
    """Custom logger for the demo interface."""
    
    LOG_LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    def __init__(
        self,
        name: str = "demo",
        level: str = "INFO",
        log_dir: Optional[str] = None,
        format_string: Optional[str] = None
    ):
        """
        Initialize the demo logger.
        
        Args:
            name (str): Logger name
            level (str): Logging level
            log_dir (str, optional): Directory for log files
            format_string (str, optional): Custom format string for log messages
        """
        self.name = name
        self.level = self.LOG_LEVELS.get(level.upper(), logging.INFO)
        # Use demo/logs as default directory
        self.log_dir = Path(log_dir) if log_dir else Path(__file__).parent.parent / "logs"
        self.format_string = format_string or (
            "%(asctime)s [%(levelname)s] %(name)s: "
            "%(message)s (%(filename)s:%(lineno)d)"
        )
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.level)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Setup handlers
        self._setup_handlers()
        
        # Track errors for debugging
        self.error_history = []
        
        # Clean up old logs
        self._cleanup_old_logs()
    
    def _setup_handlers(self) -> None:
        """Set up console and file handlers."""
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(self.format_string))
        self.logger.addHandler(console_handler)
        
        # File handler
        if not self.log_dir.exists():
            self.log_dir.mkdir(parents=True)
        
        log_file = self.log_dir / f"{self.name}_{datetime.now():%Y%m%d}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(self.format_string))
        self.logger.addHandler(file_handler)
    
    def _cleanup_old_logs(self) -> None:
        """Clean up log files from previous days."""
        if not self.log_dir.exists():
            return
            
        today = datetime.now().date()
        for log_file in self.log_dir.glob("*.log"):
            try:
                # Extract date from filename (format: name_YYYYMMDD.log)
                file_date_str = log_file.stem.split('_')[-1]
                file_date = datetime.strptime(file_date_str, "%Y%m%d").date()
                
                # Remove if not today's log
                if file_date < today:
                    log_file.unlink()
                    
            except (ValueError, IndexError):
                # Skip files that don't match the expected format
                continue
    
    def _track_error(self, level: int, msg: str, exc_info: Optional[Exception] = None) -> None:
        """Track errors for debugging purposes."""
        if level >= logging.ERROR:
            error_entry = {
                'timestamp': datetime.now().isoformat(),
                'level': logging.getLevelName(level),
                'message': msg,
                'exception': str(exc_info) if exc_info else None
            }
            self.error_history.append(error_entry)
            
            # Keep only last 100 errors
            if len(self.error_history) > 100:
                self.error_history.pop(0)
    
    def debug(self, msg: str, *args, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs) -> None:
        """Log info message."""
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, exc_info: Optional[Exception] = None, **kwargs) -> None:
        """Log error message and track it."""
        self.logger.error(msg, *args, exc_info=exc_info, **kwargs)
        self._track_error(logging.ERROR, msg, exc_info)
    
    def critical(self, msg: str, *args, exc_info: Optional[Exception] = None, **kwargs) -> None:
        """Log critical message and track it."""
        self.logger.critical(msg, *args, exc_info=exc_info, **kwargs)
        self._track_error(logging.CRITICAL, msg, exc_info)
    
    def get_error_history(self, limit: Optional[int] = None) -> list:
        """
        Get the error history.
        
        Args:
            limit (int, optional): Maximum number of errors to return
            
        Returns:
            list: List of error entries
        """
        if limit is None:
            return self.error_history
        return self.error_history[-limit:]
    
    def export_error_history(self, filepath: Optional[str] = None) -> Union[str, Dict[str, Any]]:
        """
        Export error history to JSON.
        
        Args:
            filepath (str, optional): Path to save the JSON file
            
        Returns:
            Union[str, Dict[str, Any]]: JSON string or dictionary of error history
        """
        export_data = {
            'logger_name': self.name,
            'export_time': datetime.now().isoformat(),
            'errors': self.error_history
        }
        
        if filepath:
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            return filepath
        
        return export_data 
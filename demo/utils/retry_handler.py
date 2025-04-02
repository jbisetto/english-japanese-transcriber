"""Retry handler for managing retryable operations.

This module provides functionality for automatic retrying of operations
that may fail due to transient issues.
"""

import time
import logging
from typing import TypeVar, Callable, Any, Optional
from functools import wraps
from .errors import RetryableError, NetworkError, RateLimitError

T = TypeVar('T')

class RetryHandler:
    """Handles retrying of operations that may fail transiently."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 10.0,
        exponential_base: float = 2.0
    ):
        """
        Initialize the retry handler.
        
        Args:
            max_retries (int): Maximum number of retry attempts
            base_delay (float): Initial delay between retries in seconds
            max_delay (float): Maximum delay between retries in seconds
            exponential_base (float): Base for exponential backoff
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.logger = logging.getLogger(__name__)
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for the current retry attempt."""
        delay = min(
            self.base_delay * (self.exponential_base ** (attempt - 1)),
            self.max_delay
        )
        return delay
    
    def should_retry(self, error: Exception) -> bool:
        """Determine if an operation should be retried based on the error."""
        if isinstance(error, RetryableError):
            return True
        if isinstance(error, (NetworkError, RateLimitError)):
            return True
        return False
    
    def retry_operation(
        self,
        operation: Callable[..., T],
        *args: Any,
        **kwargs: Any
    ) -> T:
        """
        Retry an operation with exponential backoff.
        
        Args:
            operation: The function to retry
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            The result of the operation if successful
            
        Raises:
            The last error encountered if all retries fail
        """
        last_error: Optional[Exception] = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                last_error = e
                if not self.should_retry(e):
                    raise
                
                if attempt < self.max_retries:
                    delay = self.calculate_delay(attempt)
                    self.logger.warning(
                        f"Operation failed (attempt {attempt}/{self.max_retries}). "
                        f"Retrying in {delay:.1f}s... Error: {str(e)}"
                    )
                    time.sleep(delay)
                else:
                    self.logger.error(
                        f"Operation failed after {self.max_retries} attempts. "
                        f"Last error: {str(e)}"
                    )
        
        if last_error:
            raise last_error
        raise RuntimeError("Unexpected state in retry_operation")

def retry(
    max_retries: Optional[int] = None,
    base_delay: Optional[float] = None,
    max_delay: Optional[float] = None
) -> Callable:
    """
    Decorator for retrying operations.
    
    Args:
        max_retries: Override default max retries
        base_delay: Override default base delay
        max_delay: Override default max delay
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            handler = RetryHandler(
                max_retries=max_retries or 3,
                base_delay=base_delay or 1.0,
                max_delay=max_delay or 10.0
            )
            return handler.retry_operation(func, *args, **kwargs)
        return wrapper
    return decorator 
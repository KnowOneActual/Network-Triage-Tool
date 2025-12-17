"""Utility functions for Network Triage Tool.

Provides retry logic, timeout management, and common error handling patterns.
"""

import logging
import time
import functools
import subprocess
import shutil
from typing import Callable, Any, Optional, List
from .exceptions import (
    CommandNotFoundError,
    NetworkTimeoutError,
    NetworkCommandError,
)

# Configure logging
logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """Decorator to retry a function with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 1.0)
        backoff: Multiplier for exponential backoff (default: 2.0)
        exceptions: Tuple of exceptions to catch and retry on (default: all)
    
    Example:
        @retry(max_attempts=3, delay=1.0, exceptions=(ConnectionError,))
        def fetch_public_ip():
            return requests.get('https://ipinfo.io/json').json()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.debug(
                            f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {e}"
                        )
            
            # If we've exhausted all retries, raise the last exception
            raise last_exception
        
        return wrapper
    
    return decorator


def safe_subprocess_run(
    command: List[str],
    timeout: int = 10,
    check_command_exists: bool = True,
    shell: bool = False,
) -> str:
    """Safely run a subprocess command with timeout and error handling.
    
    Args:
        command: List of command arguments (e.g., ['ping', 'google.com'])
        timeout: Maximum seconds to wait for command completion (default: 10)
        check_command_exists: Verify command exists before running (default: True)
        shell: Run command through shell (default: False, not recommended)
    
    Returns:
        str: Command output (stdout)
    
    Raises:
        CommandNotFoundError: If command is not found
        NetworkTimeoutError: If command exceeds timeout
        NetworkCommandError: If command exits with error
    
    Example:
        output = safe_subprocess_run(['ifconfig'], timeout=5)
    """
    # Verify command exists (if first element is an executable)
    if check_command_exists and not shell:
        cmd_name = command[0]
        if not shutil.which(cmd_name):
            raise CommandNotFoundError(
                f"Command '{cmd_name}' not found. "
                f"Please install it or ensure it's in your PATH."
            )
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=shell,
            check=False,  # Don't raise on non-zero exit code
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            raise NetworkCommandError(
                f"Command '{' '.join(command)}' failed with exit code {result.returncode}: {error_msg}"
            )
        
        return result.stdout.strip()
    
    except subprocess.TimeoutExpired:
        raise NetworkTimeoutError(
            f"Command '{' '.join(command)}' exceeded {timeout}s timeout"
        )
    except CommandNotFoundError:
        raise  # Re-raise our custom exception
    except NetworkCommandError:
        raise  # Re-raise our custom exception
    except Exception as e:
        raise NetworkCommandError(f"Unexpected error running command: {e}")


def safe_socket_operation(
    operation: Callable,
    timeout: float = 5.0,
    operation_name: str = "Socket operation",
) -> Any:
    """Safely execute a socket operation with timeout.
    
    Args:
        operation: Callable that performs the socket operation
        timeout: Timeout in seconds (default: 5.0)
        operation_name: Name for error messages (default: "Socket operation")
    
    Returns:
        Result from operation callable
    
    Raises:
        NetworkTimeoutError: If operation times out
        NetworkCommandError: If operation fails
    
    Example:
        def get_ip():
            with socket.socket() as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        
        ip = safe_socket_operation(get_ip, timeout=3)
    """
    try:
        # Set a timeout context (requires signal on Unix, not available on Windows)
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"{operation_name} timed out after {timeout}s")
        
        # Only use signal on Unix systems
        import platform
        if platform.system() != "Windows":
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(timeout) + 1)  # +1 for safety
        
        try:
            return operation()
        finally:
            if platform.system() != "Windows":
                signal.alarm(0)  # Cancel alarm
                signal.signal(signal.SIGALRM, old_handler)
    
    except TimeoutError as e:
        raise NetworkTimeoutError(str(e))
    except Exception as e:
        raise NetworkCommandError(f"{operation_name} failed: {e}")


def safe_http_request(
    url: str,
    timeout: int = 5,
    retries: int = 2,
) -> dict:
    """Safely make an HTTP request with retry logic.
    
    Args:
        url: URL to request
        timeout: Request timeout in seconds (default: 5)
        retries: Number of retry attempts (default: 2)
    
    Returns:
        dict: Parsed JSON response
    
    Raises:
        NetworkConnectivityError: If request fails after retries
    
    Example:
        data = safe_http_request('https://ipinfo.io/json', timeout=3)
        print(data['ip'])
    """
    import requests
    from .exceptions import NetworkConnectivityError
    
    @retry(max_attempts=retries, delay=1.0, exceptions=(requests.RequestException,))
    def _request():
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    
    try:
        return _request()
    except Exception as e:
        raise NetworkConnectivityError(
            f"Failed to fetch {url} after {retries} attempts: {e}"
        )


def format_error_message(error: Exception, context: str = "") -> str:
    """Format exception into a user-friendly error message.
    
    Args:
        error: Exception to format
        context: Additional context to include (default: "")
    
    Returns:
        str: Formatted error message
    
    Example:
        try:
            result = some_function()
        except Exception as e:
            msg = format_error_message(e, context="While fetching IP")
            print(msg)  # "While fetching IP: Command 'ping' not found"
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    if context:
        return f"{context}: {error_msg}"
    return error_msg


def log_exception(error: Exception, context: str = "") -> None:
    """Log an exception with context.
    
    Args:
        error: Exception to log
        context: Additional context to include
    """
    error_type = type(error).__name__
    if context:
        logger.error(f"{context}: [{error_type}] {error}", exc_info=False)
    else:
        logger.error(f"[{error_type}] {error}", exc_info=False)

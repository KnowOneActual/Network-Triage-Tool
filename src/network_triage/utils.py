"""Utility functions for Network Triage Tool.

Provides retry logic, timeout management, and common error handling patterns.
"""

import functools
import shutil
import subprocess
import time
from collections.abc import Callable
from typing import Any, cast

from .exceptions import (
    CommandNotFoundError,
    NetworkCommandError,
    NetworkTimeoutError,
)
from .logging import get_logger

# Configure logging
logger = get_logger(__name__)


def retry[T](
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
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

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
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
                            f"Retrying in {current_delay}s...",
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}: {e}")

            # If all retries are exhausted, raise the last exception
            if last_exception:
                raise last_exception
            raise RuntimeError(f"Retry decorator failed for {func.__name__}")

        return wrapper

    return decorator


def safe_subprocess_run(
    command: list[str],
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
            raise CommandNotFoundError(f"Command '{cmd_name}' not found. Please install it or ensure it's in your PATH.")

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
            raise NetworkCommandError(f"Command '{' '.join(command)}' failed with exit code {result.returncode}: {error_msg}")

        return result.stdout.strip()

    except subprocess.TimeoutExpired:
        raise NetworkTimeoutError(f"Command '{' '.join(command)}' exceeded {timeout}s timeout")
    except CommandNotFoundError:
        raise  # Re-raise custom exception
    except NetworkCommandError:
        raise  # Re-raise custom exception
    except Exception as e:
        raise NetworkCommandError(f"Unexpected error running command: {e}")


def safe_socket_operation[T](
    operation: Callable[[], T],
    timeout: float = 5.0,
    operation_name: str = "Socket operation",
) -> T:
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
        import threading

        def timeout_handler(signum: int, frame: Any) -> None:
            raise TimeoutError(f"{operation_name} timed out after {timeout}s")

        # Only use signal on Unix systems and if we are in the main thread
        import platform

        is_main_thread = threading.current_thread() is threading.main_thread()
        use_signal = platform.system() != "Windows" and is_main_thread

        if use_signal:
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.setitimer(signal.ITIMER_REAL, float(timeout))

        try:
            return operation()
        finally:
            if use_signal:
                signal.setitimer(signal.ITIMER_REAL, 0)  # Cancel timer
                signal.signal(signal.SIGALRM, old_handler)

    except TimeoutError as e:
        raise NetworkTimeoutError(str(e))
    except Exception as e:
        raise NetworkCommandError(f"{operation_name} failed: {e}")


def safe_http_request(
    url: str,
    timeout: int = 5,
    retries: int = 2,
) -> dict[str, Any]:
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
    def _request() -> dict[str, Any]:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return cast("dict[str, Any]", response.json())

    try:
        return _request()
    except Exception as e:
        raise NetworkConnectivityError(f"Failed to fetch {url} after {retries} attempts: {e}")


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
    type(error).__name__
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


def ttl_cache(ttl_seconds: int = 60) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to cache function results with a Time-To-Live (TTL).

    Args:
        ttl_seconds: Cache duration in seconds (default: 60)

    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        cache: dict[tuple[Any, ...], tuple[float, Any]] = {}

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Create a hashable key from args and kwargs
            # Exclude non-hashable arguments safely by converting them to str for caching purposes
            try:
                key = (args, frozenset(kwargs.items()))
                hash(key)
            except TypeError:
                key = (str(args), str(kwargs))  # type: ignore

            now = time.time()
            if key in cache:
                timestamp, result = cache[key]
                if now - timestamp < ttl_seconds:
                    return result

            result = func(*args, **kwargs)
            cache[key] = (now, result)
            return result

        return wrapper

    return decorator


def track_performance(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to track basic performance metrics (execution time)."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            duration = time.perf_counter() - start_time
            logger.info(f"Performance: '{func.__name__}' completed in {duration:.4f}s")
            return result
        except Exception as e:
            duration = time.perf_counter() - start_time
            logger.error(f"Performance: '{func.__name__}' failed after {duration:.4f}s with {type(e).__name__}")
            raise

    return wrapper


def monitor_long_running(threshold_seconds: float = 5.0) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to monitor long-running tasks and log if they exceed a threshold."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                if duration > threshold_seconds:
                    logger.warning(
                        f"Long-running task: '{func.__name__}' took {duration:.2f}s (threshold: {threshold_seconds}s)"
                    )
                return result
            except Exception as e:
                duration = time.perf_counter() - start_time
                if duration > threshold_seconds:
                    logger.warning(
                        f"Long-running task: '{func.__name__}' failed after {duration:.2f}s (threshold: {threshold_seconds}s) with {type(e).__name__}"
                    )
                raise

        return wrapper

    return decorator

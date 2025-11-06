"""
Retry logic and error handling utilities for the EIA API client.

Provides composable retry strategies with exponential backoff and
configurable error handling.
"""

import time
from typing import Any, Callable, TypeVar
from functools import wraps
from collections.abc import Iterator

import httpx

from eia.v2.exceptions import EIAAPIError

T = TypeVar("T")


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        retry_on_status: set[int] | None = None,
    ):
        """
        Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts (default: 3)
            base_delay: Initial delay in seconds (default: 1.0)
            max_delay: Maximum delay in seconds (default: 60.0)
            exponential_base: Base for exponential backoff (default: 2.0)
            retry_on_status: HTTP status codes to retry on (default: {429, 500, 502, 503, 504})
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retry_on_status = retry_on_status or {429, 500, 502, 503, 504}

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for a given attempt using exponential backoff.

        Args:
            attempt: The attempt number (0-indexed)

        Returns:
            Delay in seconds, capped at max_delay
        """
        delay = self.base_delay * (self.exponential_base**attempt)
        return min(delay, self.max_delay)

    def should_retry(self, error: Exception) -> bool:
        """
        Determine if an error should trigger a retry.

        Args:
            error: The exception that occurred

        Returns:
            True if the request should be retried
        """
        if isinstance(error, httpx.HTTPStatusError):
            return error.response.status_code in self.retry_on_status
        if isinstance(error, (httpx.ConnectError, httpx.TimeoutException)):
            return True
        return False


def with_retry(config: RetryConfig | None = None) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to add retry logic to a function.

    Args:
        config: Retry configuration (uses default if None)

    Returns:
        Decorated function with retry logic

    Example:
        >>> @with_retry(RetryConfig(max_attempts=5))
        ... def fetch_data():
        ...     return client.get("https://api.example.com")
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_error: Exception | None = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if not config.should_retry(e):
                        raise

                    if attempt < config.max_attempts - 1:
                        delay = config.calculate_delay(attempt)
                        time.sleep(delay)

            # If we've exhausted all retries, raise the last error
            if last_error:
                raise last_error
            raise RuntimeError("Retry logic failed unexpectedly")

        return wrapper

    return decorator


async def async_with_retry(
    config: RetryConfig | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to add retry logic to an async function.

    Args:
        config: Retry configuration (uses default if None)

    Returns:
        Decorated async function with retry logic
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            import asyncio

            last_error: Exception | None = None

            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if not config.should_retry(e):
                        raise

                    if attempt < config.max_attempts - 1:
                        delay = config.calculate_delay(attempt)
                        await asyncio.sleep(delay)

            if last_error:
                raise last_error
            raise RuntimeError("Retry logic failed unexpectedly")

        return wrapper

    return decorator


def paginate_data(
    fetch_page: Callable[[int, int], dict[str, Any]],
    page_size: int = 5000,
    max_rows: int | None = None,
    max_pages: int | None = None,
) -> Iterator[dict[str, Any]]:
    """
    Paginate through API results using a composable iterator pattern.

    This replaces while True loops with explicit iteration bounds.

    Args:
        fetch_page: Function that takes (offset, length) and returns a response
        page_size: Number of rows per page (default: 5000)
        max_rows: Maximum total rows to fetch (None for unlimited)
        max_pages: Maximum number of pages to fetch (None for unlimited)

    Yields:
        Individual data records

    Example:
        >>> def fetch(offset, length):
        ...     return client.get_data(route="test", offset=offset, length=length)
        >>> for record in paginate_data(fetch, max_rows=10000):
        ...     process(record)
    """
    offset = 0
    total_fetched = 0
    pages_fetched = 0

    while True:
        # Check page limit
        if max_pages and pages_fetched >= max_pages:
            break

        # Adjust page size if we're near max_rows
        current_page_size = page_size
        if max_rows:
            remaining = max_rows - total_fetched
            if remaining <= 0:
                break
            current_page_size = min(page_size, remaining)

        # Fetch the page
        response = fetch_page(offset, current_page_size)
        data = response["response"]["data"]

        # No more data available
        if not data:
            break

        # Yield records
        for record in data:
            yield record
            total_fetched += 1
            if max_rows and total_fetched >= max_rows:
                return

        # Check if we've fetched all available data
        total_available = response["response"].get("total", 0)
        if offset + len(data) >= total_available:
            break

        offset += len(data)
        pages_fetched += 1


def batch_iterator(
    items: Iterator[T],
    batch_size: int,
) -> Iterator[list[T]]:
    """
    Batch items from an iterator into fixed-size chunks.

    Args:
        items: Iterator of items to batch
        batch_size: Size of each batch

    Yields:
        Lists of items, each containing up to batch_size items

    Example:
        >>> for batch in batch_iterator(paginate_data(fetch), batch_size=1000):
        ...     insert_to_database(batch)
    """
    batch: list[T] = []
    for item in items:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []

    if batch:
        yield batch

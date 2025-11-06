"""Tests for retry logic and composability features."""

import pytest
from unittest.mock import Mock
import httpx

from eia.v2.retry import (
    RetryConfig,
    with_retry,
    paginate_data,
    batch_iterator,
)
from eia.v2.exceptions import EIAAPIError


class TestRetryConfig:
    """Tests for RetryConfig class."""

    def test_default_config(self):
        """Test default retry configuration."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert 429 in config.retry_on_status

    def test_custom_config(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=2.0,
            max_delay=120.0,
            retry_on_status={500, 502},
        )
        assert config.max_attempts == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 120.0
        assert config.retry_on_status == {500, 502}

    def test_calculate_delay(self):
        """Test exponential backoff calculation."""
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, max_delay=10.0)

        assert config.calculate_delay(0) == 1.0  # 1 * 2^0
        assert config.calculate_delay(1) == 2.0  # 1 * 2^1
        assert config.calculate_delay(2) == 4.0  # 1 * 2^2
        assert config.calculate_delay(3) == 8.0  # 1 * 2^3
        assert config.calculate_delay(4) == 10.0  # Capped at max_delay

    def test_should_retry_http_status(self):
        """Test retry decision for HTTP status errors."""
        config = RetryConfig(retry_on_status={429, 500})

        # Create mock response
        response_429 = Mock(status_code=429)
        response_400 = Mock(status_code=400)

        error_429 = httpx.HTTPStatusError(
            "Too Many Requests", request=Mock(), response=response_429
        )
        error_400 = httpx.HTTPStatusError(
            "Bad Request", request=Mock(), response=response_400
        )

        assert config.should_retry(error_429) is True
        assert config.should_retry(error_400) is False

    def test_should_retry_network_errors(self):
        """Test retry decision for network errors."""
        config = RetryConfig()

        connect_error = httpx.ConnectError("Connection failed")
        timeout_error = httpx.TimeoutException("Request timed out")

        assert config.should_retry(connect_error) is True
        assert config.should_retry(timeout_error) is True

    def test_should_not_retry_other_errors(self):
        """Test that other errors are not retried."""
        config = RetryConfig()

        value_error = ValueError("Invalid value")
        assert config.should_retry(value_error) is False


class TestWithRetry:
    """Tests for with_retry decorator."""

    def test_successful_call(self):
        """Test that successful calls work without retry."""
        config = RetryConfig(max_attempts=3)
        call_count = 0

        @with_retry(config)
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_on_retriable_error(self):
        """Test that retriable errors trigger retries."""
        config = RetryConfig(max_attempts=3, base_delay=0.01)  # Fast retries for testing
        call_count = 0

        @with_retry(config)
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.ConnectError("Connection failed")
            return "success"

        result = flaky_func()
        assert result == "success"
        assert call_count == 3

    def test_no_retry_on_non_retriable_error(self):
        """Test that non-retriable errors are not retried."""
        config = RetryConfig(max_attempts=3)
        call_count = 0

        @with_retry(config)
        def failing_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Non-retriable error")

        with pytest.raises(ValueError):
            failing_func()

        assert call_count == 1  # No retries

    def test_max_attempts_reached(self):
        """Test that errors are raised after max attempts."""
        config = RetryConfig(max_attempts=2, base_delay=0.01)
        call_count = 0

        @with_retry(config)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise httpx.ConnectError("Always fails")

        with pytest.raises(httpx.ConnectError):
            always_fails()

        assert call_count == 2  # Tried max_attempts times


class TestPaginateData:
    """Tests for paginate_data iterator."""

    def test_single_page(self):
        """Test pagination with data that fits in one page."""
        data = [{"id": i} for i in range(10)]

        def fetch_page(offset, length):
            return {
                "response": {
                    "data": data[offset : offset + length],
                    "total": len(data),
                }
            }

        result = list(paginate_data(fetch_page, page_size=100))
        assert len(result) == 10
        assert result[0]["id"] == 0

    def test_multiple_pages(self):
        """Test pagination with data spanning multiple pages."""
        data = [{"id": i} for i in range(25)]

        def fetch_page(offset, length):
            return {
                "response": {
                    "data": data[offset : offset + length],
                    "total": len(data),
                }
            }

        result = list(paginate_data(fetch_page, page_size=10))
        assert len(result) == 25
        assert result[0]["id"] == 0
        assert result[24]["id"] == 24

    def test_max_rows_limit(self):
        """Test max_rows parameter limits results."""
        data = [{"id": i} for i in range(100)]

        def fetch_page(offset, length):
            return {
                "response": {
                    "data": data[offset : offset + length],
                    "total": len(data),
                }
            }

        result = list(paginate_data(fetch_page, page_size=10, max_rows=25))
        assert len(result) == 25

    def test_max_pages_limit(self):
        """Test max_pages parameter limits number of requests."""
        data = [{"id": i} for i in range(100)]
        pages_fetched = 0

        def fetch_page(offset, length):
            nonlocal pages_fetched
            pages_fetched += 1
            return {
                "response": {
                    "data": data[offset : offset + length],
                    "total": len(data),
                }
            }

        result = list(paginate_data(fetch_page, page_size=10, max_pages=3))
        assert pages_fetched == 3
        assert len(result) == 30

    def test_empty_result(self):
        """Test handling of empty results."""

        def fetch_page(offset, length):
            return {"response": {"data": [], "total": 0}}

        result = list(paginate_data(fetch_page, page_size=10))
        assert len(result) == 0


class TestBatchIterator:
    """Tests for batch_iterator function."""

    def test_exact_batches(self):
        """Test batching with data that divides evenly."""
        items = range(10)
        batches = list(batch_iterator(iter(items), batch_size=5))

        assert len(batches) == 2
        assert batches[0] == [0, 1, 2, 3, 4]
        assert batches[1] == [5, 6, 7, 8, 9]

    def test_partial_last_batch(self):
        """Test batching with partial last batch."""
        items = range(12)
        batches = list(batch_iterator(iter(items), batch_size=5))

        assert len(batches) == 3
        assert batches[0] == [0, 1, 2, 3, 4]
        assert batches[1] == [5, 6, 7, 8, 9]
        assert batches[2] == [10, 11]

    def test_single_batch(self):
        """Test data smaller than batch size."""
        items = range(3)
        batches = list(batch_iterator(iter(items), batch_size=10))

        assert len(batches) == 1
        assert batches[0] == [0, 1, 2]

    def test_empty_iterator(self):
        """Test empty iterator."""
        batches = list(batch_iterator(iter([]), batch_size=5))
        assert len(batches) == 0

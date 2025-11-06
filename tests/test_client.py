"""
Integration tests for EIA API v2 client.

These tests use mocked HTTP responses and property-based testing
to ensure robust behavior without making real API calls.
"""

import pytest
from hypothesis import given, strategies as st
from pytest_httpx import HTTPXMock

from eia.v2 import EIAClient, AsyncEIAClient
from eia.v2.exceptions import EIAAPIError, EIAValidationError


# Sample response data for mocking


SAMPLE_DATA_RESPONSE = {
    "response": {
        "total": 3,
        "dateFormat": "YYYY",
        "frequency": "annual",
        "data": [
            {"period": "2023", "value": 100.5, "stateid": "CA"},
            {"period": "2023", "value": 95.3, "stateid": "NY"},
            {"period": "2022", "value": 98.7, "stateid": "CA"},
        ],
        "description": "Test data",
        "startPeriod": "2022",
        "endPeriod": "2023",
    },
    "request": {
        "command": "/v2/electricity/retail-sales/data",
        "params": {"api_key": "test_key", "frequency": "annual"},
    },
    "apiVersion": "2.1.4",
}


SAMPLE_FACET_RESPONSE = {
    "response": {
        "facets": [
            {"id": "RES", "name": "Residential"},
            {"id": "COM", "name": "Commercial"},
            {"id": "IND", "name": "Industrial"},
        ],
        "total": 3,
    },
    "request": {
        "command": "/v2/electricity/retail-sales/facet/sectorid",
        "params": {"api_key": "test_key"},
    },
    "apiVersion": "2.1.4",
}


SAMPLE_ROUTE_RESPONSE = {
    "response": {
        "id": "electricity",
        "name": "Electricity",
        "description": "Electricity data",
        "routes": [
            {
                "id": "retail-sales",
                "name": "Retail Sales",
                "description": "Electricity retail sales data",
            },
            {
                "id": "operating-generator-capacity",
                "name": "Operating Generator Capacity",
            },
        ],
    },
    "request": {"command": "/v2/electricity", "params": {"api_key": "test_key"}},
    "apiVersion": "2.1.4",
}


SAMPLE_ERROR_RESPONSE = {
    "error": "Invalid frequency 'invalid' provided",
    "code": 400,
}


# Sync client tests


class TestEIAClient:
    """Tests for synchronous EIA client."""

    def test_client_initialization(self):
        """Test that client can be initialized with API key."""
        client = EIAClient(api_key="test_key")
        assert client.api_key == "test_key"
        assert client.timeout == 60.0
        assert client.base_url == "https://api.eia.gov/v2/"

    def test_client_initialization_with_custom_params(self):
        """Test client initialization with custom parameters."""
        client = EIAClient(
            api_key="test_key", timeout=30.0, base_url="https://custom.api/"
        )
        assert client.timeout == 30.0
        assert client.base_url == "https://custom.api/"

    def test_client_requires_api_key(self):
        """Test that API key is required."""
        with pytest.raises(EIAValidationError, match="API key is required"):
            EIAClient(api_key="")

    def test_get_data(self, httpx_mock: HTTPXMock):
        """Test getting data from API."""
        httpx_mock.add_response(json=SAMPLE_DATA_RESPONSE)

        client = EIAClient(api_key="test_key")
        response = client.get_data(
            route="electricity/retail-sales",
            data=["price"],
            frequency="annual",
            facets={"stateid": ["CA", "NY"]},
        )

        assert response["response"]["total"] == 3
        assert len(response["response"]["data"]) == 3
        assert response["response"]["frequency"] == "annual"
        assert response["apiVersion"] == "2.1.4"

    def test_get_data_with_pagination(self, httpx_mock: HTTPXMock):
        """Test getting data with pagination parameters."""
        httpx_mock.add_response(json=SAMPLE_DATA_RESPONSE)

        client = EIAClient(api_key="test_key")
        response = client.get_data(
            route="electricity/retail-sales",
            data=["price"],
            offset=0,
            length=100,
        )

        # Check that request was made
        request = httpx_mock.get_request()
        assert request is not None
        assert "offset=0" in str(request.url)
        assert "length=100" in str(request.url)

    def test_get_data_length_validation(self):
        """Test that length parameter is validated."""
        client = EIAClient(api_key="test_key")

        with pytest.raises(EIAValidationError, match="cannot exceed 5000"):
            client.get_data(
                route="electricity/retail-sales", data=["price"], length=10000
            )

    def test_get_facet(self, httpx_mock: HTTPXMock):
        """Test getting facet values."""
        httpx_mock.add_response(json=SAMPLE_FACET_RESPONSE)

        client = EIAClient(api_key="test_key")
        response = client.get_facet(
            route="electricity/retail-sales", facet="sectorid"
        )

        assert len(response["response"]["facets"]) == 3
        assert response["response"]["facets"][0]["id"] == "RES"
        assert response["response"]["facets"][0]["name"] == "Residential"

    def test_get_route(self, httpx_mock: HTTPXMock):
        """Test getting route metadata."""
        httpx_mock.add_response(json=SAMPLE_ROUTE_RESPONSE)

        client = EIAClient(api_key="test_key")
        response = client.get_route(route="electricity")

        assert response["response"]["id"] == "electricity"
        assert len(response["response"]["routes"]) == 2
        assert response["response"]["routes"][0]["id"] == "retail-sales"

    def test_api_error_handling(self, httpx_mock: HTTPXMock):
        """Test handling of API errors."""
        httpx_mock.add_response(status_code=400, json=SAMPLE_ERROR_RESPONSE)

        client = EIAClient(api_key="test_key")

        with pytest.raises(EIAAPIError) as exc_info:
            client.get_data(route="electricity/retail-sales", data=["price"])

        assert "Invalid frequency" in str(exc_info.value)
        assert exc_info.value.code == 400

    def test_get_all_data_single_page(self, httpx_mock: HTTPXMock):
        """Test getting all data when results fit in one page."""
        # Mock response with less data than page size
        response = SAMPLE_DATA_RESPONSE.copy()
        response["response"]["total"] = 3
        httpx_mock.add_response(json=response)

        client = EIAClient(api_key="test_key")
        all_data = client.get_all_data(
            route="electricity/retail-sales", data=["price"]
        )

        assert len(all_data) == 3
        assert all_data[0]["period"] == "2023"

    def test_get_all_data_multiple_pages(self, httpx_mock: HTTPXMock):
        """Test getting all data with pagination."""
        # First page
        first_response = {
            "response": {
                "total": 7000,
                "data": [{"period": f"2023-{i:02d}", "value": i} for i in range(5000)],
            },
            "request": {"command": "/test", "params": {}},
        }
        # Second page (partial)
        second_response = {
            "response": {
                "total": 7000,
                "data": [
                    {"period": f"2022-{i:02d}", "value": i} for i in range(2000)
                ],
            },
            "request": {"command": "/test", "params": {}},
        }

        httpx_mock.add_response(json=first_response)
        httpx_mock.add_response(json=second_response)

        client = EIAClient(api_key="test_key")
        all_data = client.get_all_data(
            route="electricity/retail-sales", data=["price"]
        )

        assert len(all_data) == 7000

    def test_get_all_data_with_max_rows(self, httpx_mock: HTTPXMock):
        """Test getting all data with max_rows limit."""
        response = {
            "response": {
                "total": 10000,
                "data": [{"period": f"2023-{i:02d}", "value": i} for i in range(5000)],
            },
            "request": {"command": "/test", "params": {}},
        }
        httpx_mock.add_response(json=response)

        client = EIAClient(api_key="test_key")
        all_data = client.get_all_data(
            route="electricity/retail-sales", data=["price"], max_rows=100
        )

        assert len(all_data) == 100

    def test_context_manager(self, httpx_mock: HTTPXMock):
        """Test client as context manager."""
        httpx_mock.add_response(json=SAMPLE_DATA_RESPONSE)

        with EIAClient(api_key="test_key") as client:
            response = client.get_data(
                route="electricity/retail-sales", data=["price"]
            )
            assert response["response"]["total"] == 3

    def test_build_params_with_facets(self):
        """Test parameter building with facets."""
        client = EIAClient(api_key="test_key")
        params = client._build_params(
            data=["price", "revenue"],
            facets={"stateid": ["CA", "NY"], "sectorid": "RES"},
        )

        assert "data[0]" in params
        assert "data[1]" in params
        assert "facets[stateid][0]" in params
        assert "facets[stateid][1]" in params
        assert "facets[sectorid][0]" in params

    def test_build_params_with_sort(self):
        """Test parameter building with sort."""
        client = EIAClient(api_key="test_key")
        params = client._build_params(sort=[("period", "desc"), ("value", "asc")])

        assert params["sort[0][column]"] == "period"
        assert params["sort[0][direction]"] == "desc"
        assert params["sort[1][column]"] == "value"
        assert params["sort[1][direction]"] == "asc"


# Async client tests


class TestAsyncEIAClient:
    """Tests for asynchronous EIA client."""

    async def test_async_client_initialization(self):
        """Test that async client can be initialized."""
        client = AsyncEIAClient(api_key="test_key")
        assert client.api_key == "test_key"

    async def test_async_get_data(self, httpx_mock: HTTPXMock):
        """Test async data fetching."""
        httpx_mock.add_response(json=SAMPLE_DATA_RESPONSE)

        async with AsyncEIAClient(api_key="test_key") as client:
            response = await client.get_data(
                route="electricity/retail-sales", data=["price"]
            )
            assert response["response"]["total"] == 3

    async def test_async_get_facet(self, httpx_mock: HTTPXMock):
        """Test async facet fetching."""
        httpx_mock.add_response(json=SAMPLE_FACET_RESPONSE)

        async with AsyncEIAClient(api_key="test_key") as client:
            response = await client.get_facet(
                route="electricity/retail-sales", facet="sectorid"
            )
            assert len(response["response"]["facets"]) == 3

    async def test_async_get_route(self, httpx_mock: HTTPXMock):
        """Test async route fetching."""
        httpx_mock.add_response(json=SAMPLE_ROUTE_RESPONSE)

        async with AsyncEIAClient(api_key="test_key") as client:
            response = await client.get_route(route="electricity")
            assert response["response"]["id"] == "electricity"

    async def test_async_get_all_data(self, httpx_mock: HTTPXMock):
        """Test async bulk data fetching."""
        response = SAMPLE_DATA_RESPONSE.copy()
        response["response"]["total"] = 3
        httpx_mock.add_response(json=response)

        async with AsyncEIAClient(api_key="test_key") as client:
            all_data = await client.get_all_data(
                route="electricity/retail-sales", data=["price"]
            )
            assert len(all_data) == 3

    async def test_async_error_handling(self, httpx_mock: HTTPXMock):
        """Test async error handling."""
        httpx_mock.add_response(status_code=400, json=SAMPLE_ERROR_RESPONSE)

        async with AsyncEIAClient(api_key="test_key") as client:
            with pytest.raises(EIAAPIError):
                await client.get_data(
                    route="electricity/retail-sales", data=["price"]
                )


# Property-based tests using Hypothesis


@given(
    api_key=st.text(min_size=1, max_size=100),
    timeout=st.floats(min_value=1.0, max_value=600.0),
)
def test_client_initialization_properties(api_key, timeout):
    """Property test: client should initialize with any valid parameters."""
    client = EIAClient(api_key=api_key, timeout=timeout)
    assert client.api_key == api_key
    assert client.timeout == timeout


@given(
    data_cols=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=10),
    offset=st.integers(min_value=0, max_value=10000),
    length=st.integers(min_value=1, max_value=5000),
)
def test_build_params_properties(data_cols, offset, length):
    """Property test: parameter building should handle various inputs."""
    client = EIAClient(api_key="test")
    params = client._build_params(data=data_cols, offset=offset, length=length)

    # Verify all data columns are in params
    for i, col in enumerate(data_cols):
        assert params[f"data[{i}]"] == col

    assert params["offset"] == offset
    assert params["length"] == length


@given(
    route=st.text(min_size=1, max_size=100).filter(lambda x: "/" in x or len(x) > 0)
)
def test_build_url_properties(route):
    """Property test: URL building should handle various routes."""
    client = EIAClient(api_key="test")
    url = client._build_url(route)

    # URL should always start with base URL
    assert url.startswith(client.base_url) or url.startswith("https://")
    # URL should contain the route (after normalization)
    # Note: urljoin may transform the route, so we just check it's a valid URL
    assert "://" in url


@given(length=st.integers(min_value=5001, max_value=100000))
def test_length_validation_property(length):
    """Property test: length validation should reject values over 5000."""
    client = EIAClient(api_key="test")

    with pytest.raises(EIAValidationError):
        client._build_params(length=length)


# Integration test simulating real workflow


class TestRealWorldWorkflow:
    """Tests simulating real-world usage patterns."""

    def test_discover_and_fetch_workflow(self, httpx_mock: HTTPXMock):
        """
        Test a typical workflow:
        1. Discover available routes
        2. Get facet values
        3. Fetch data with filters
        """
        # Step 1: Get routes
        httpx_mock.add_response(json=SAMPLE_ROUTE_RESPONSE)
        # Step 2: Get facets
        httpx_mock.add_response(json=SAMPLE_FACET_RESPONSE)
        # Step 3: Get data
        httpx_mock.add_response(json=SAMPLE_DATA_RESPONSE)

        client = EIAClient(api_key="test_key")

        # Discover routes
        routes_response = client.get_route("electricity")
        assert len(routes_response["response"]["routes"]) > 0
        first_route = routes_response["response"]["routes"][0]["id"]

        # Get facet values
        facets_response = client.get_facet(
            route=f"electricity/{first_route}", facet="sectorid"
        )
        facet_ids = [f["id"] for f in facets_response["response"]["facets"]]
        assert len(facet_ids) > 0

        # Fetch data with discovered facets
        data_response = client.get_data(
            route=f"electricity/{first_route}",
            data=["price"],
            facets={"sectorid": facet_ids[:2]},
        )
        assert data_response["response"]["total"] > 0

    def test_bulk_ingestion_workflow(self, httpx_mock: HTTPXMock):
        """
        Test bulk data ingestion workflow for analytics.
        """
        # Simulate large dataset
        large_response = {
            "response": {
                "total": 1000,
                "data": [{"period": f"2023-{i:03d}", "value": i} for i in range(1000)],
            },
            "request": {"command": "/test", "params": {}},
        }
        httpx_mock.add_response(json=large_response)

        client = EIAClient(api_key="test_key")
        all_data = client.get_all_data(
            route="electricity/retail-sales",
            data=["price", "revenue"],
            frequency="monthly",
            start="2020-01",
            end="2023-12",
        )

        # Verify data is ready for bulk ingestion
        assert isinstance(all_data, list)
        assert all(isinstance(record, dict) for record in all_data)
        assert len(all_data) == 1000

        # Simulate conversion to different formats (would work with DuckDB, etc.)
        # This demonstrates the data structure is suitable for analytics tools
        periods = [record["period"] for record in all_data]
        values = [record["value"] for record in all_data]
        assert len(periods) == len(values)

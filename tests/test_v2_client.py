"""Tests for EIA API v2 client."""

from __future__ import annotations

import respx
from httpx import Response

from eia import EIAConfig
from eia.v2 import EIAClient


@respx.mock
def test_v2_get_routes() -> None:
    """Test getting available routes."""
    config = EIAConfig(api_key="test-key")
    client = EIAClient(config)

    mock_response = {
        "response": {
            "routes": [
                {
                    "id": "retail-sales",
                    "name": "Retail Sales of Electricity",
                    "description": "Sales to ultimate customers",
                    "frequency": ["monthly", "annual"],
                    "facets": ["stateid", "sectorid"],
                },
                {
                    "id": "operating-generator-capacity",
                    "name": "Electric Power Operational Data",
                },
            ]
        }
    }

    respx.get("https://api.eia.gov/v2/electricity").mock(
        return_value=Response(200, json=mock_response)
    )

    routes = client.get_routes("electricity")

    assert len(routes) == 2
    assert routes[0].id == "retail-sales"
    assert routes[0].name == "Retail Sales of Electricity"
    assert routes[0].frequency == ["monthly", "annual"]
    assert routes[1].id == "operating-generator-capacity"


@respx.mock
async def test_v2_get_routes_async() -> None:
    """Test async route fetching."""
    config = EIAConfig(api_key="test-key")
    client = EIAClient(config)

    mock_response = {
        "response": {
            "routes": [
                {"id": "test-route", "name": "Test Route"},
            ]
        }
    }

    respx.get("https://api.eia.gov/v2/").mock(
        return_value=Response(200, json=mock_response)
    )

    routes = await client.get_routes_async()

    assert len(routes) == 1
    assert routes[0].id == "test-route"


@respx.mock
def test_v2_get_data_with_facets() -> None:
    """Test data query with facet filtering."""
    config = EIAConfig(api_key="test-key")
    client = EIAClient(config)

    mock_response = {
        "response": {
            "total": 12,
            "dateFormat": "YYYY-MM",
            "frequency": "monthly",
            "data": [
                {"period": "2024-01", "stateid": "CA", "sectorid": "RES", "value": 123.45},
                {"period": "2023-12", "stateid": "CA", "sectorid": "RES", "value": 120.50},
            ],
        }
    }

    respx.get("https://api.eia.gov/v2/electricity/retail-sales/data/").mock(
        return_value=Response(200, json=mock_response)
    )

    response = client.get_data(
        route="electricity/retail-sales",
        facets={"stateid": ["CA"], "sectorid": ["RES"]},
        frequency="monthly",
    )

    assert response.total == 12
    assert response.frequency == "monthly"
    assert response.date_format == "YYYY-MM"
    assert len(response.data) == 2
    assert response.data[0]["value"] == 123.45
    assert response.data[0]["stateid"] == "CA"


@respx.mock
async def test_v2_get_data_async() -> None:
    """Test async data query."""
    config = EIAConfig(api_key="test-key")
    client = EIAClient(config)

    mock_response = {
        "response": {
            "total": 2,
            "frequency": "annual",
            "data": [
                {"period": "2024", "value": 100.0},
                {"period": "2023", "value": 95.0},
            ],
        }
    }

    respx.get("https://api.eia.gov/v2/electricity/retail-sales/data/").mock(
        return_value=Response(200, json=mock_response)
    )

    response = await client.get_data_async(
        route="electricity/retail-sales",
        frequency="annual",
    )

    assert response.total == 2
    assert len(response.data) == 2


@respx.mock
def test_v2_get_dataframe() -> None:
    """Test getting data as DataFrame."""
    config = EIAConfig(api_key="test-key")
    client = EIAClient(config)

    mock_response = {
        "response": {
            "total": 3,
            "frequency": "monthly",
            "data": [
                {"period": "2024-01", "stateid": "CA", "value": 123.45},
                {"period": "2023-12", "stateid": "CA", "value": 120.50},
                {"period": "2023-11", "stateid": "CA", "value": "NA"},
            ],
        }
    }

    respx.get("https://api.eia.gov/v2/electricity/retail-sales/data/").mock(
        return_value=Response(200, json=mock_response)
    )

    df = client.get_dataframe(
        route="electricity/retail-sales",
        facets={"stateid": ["CA"]},
        frequency="monthly",
        auto_paginate=False,
    )

    assert len(df) == 3
    assert "period" in df.columns
    assert "value" in df.columns
    assert "stateid" in df.columns
    # Check NA handling
    assert df.iloc[2]["value"] != "NA"  # Should be converted


@respx.mock
async def test_v2_get_dataframe_async() -> None:
    """Test async DataFrame query."""
    config = EIAConfig(api_key="test-key")
    client = EIAClient(config)

    mock_response = {
        "response": {
            "total": 2,
            "data": [
                {"period": "2024", "value": 100.0},
                {"period": "2023", "value": 95.0},
            ],
        }
    }

    respx.get("https://api.eia.gov/v2/electricity/retail-sales/data/").mock(
        return_value=Response(200, json=mock_response)
    )

    df = await client.get_dataframe_async(
        route="electricity/retail-sales",
        frequency="annual",
    )

    assert len(df) == 2
    assert "value" in df.columns


@respx.mock
def test_v2_auto_pagination() -> None:
    """Test automatic pagination for large datasets."""
    config = EIAConfig(api_key="test-key")
    client = EIAClient(config)

    # Mock first page (5000 rows)
    first_page_data = [{"period": f"2024-{i:02d}", "value": float(i)} for i in range(1, 5001)]
    mock_response_1 = {
        "response": {
            "total": 7500,
            "frequency": "monthly",
            "data": first_page_data,
        }
    }

    # Mock second page (2500 rows)
    second_page_data = [{"period": f"2020-{i:02d}", "value": float(i)} for i in range(1, 2501)]
    mock_response_2 = {
        "response": {
            "total": 7500,
            "frequency": "monthly",
            "data": second_page_data,
        }
    }

    respx.get("https://api.eia.gov/v2/electricity/retail-sales/data/").mock(
        side_effect=[
            Response(200, json=mock_response_1),
            Response(200, json=mock_response_2),
        ]
    )

    paginated = client.get_all_data(
        route="electricity/retail-sales",
        frequency="monthly",
    )

    assert paginated.total == 7500
    assert len(paginated.data) == 7500  # 5000 + 2500
    assert paginated.pages_fetched == 2
    assert paginated.frequency == "monthly"


@respx.mock
def test_v2_multiple_facet_values() -> None:
    """Test query with multiple values for a facet."""
    config = EIAConfig(api_key="test-key")
    client = EIAClient(config)

    mock_response = {
        "response": {
            "total": 4,
            "data": [
                {"period": "2024", "stateid": "CA", "value": 100.0},
                {"period": "2024", "stateid": "TX", "value": 200.0},
                {"period": "2023", "stateid": "CA", "value": 95.0},
                {"period": "2023", "stateid": "TX", "value": 190.0},
            ],
        }
    }

    respx.get("https://api.eia.gov/v2/electricity/retail-sales/data/").mock(
        return_value=Response(200, json=mock_response)
    )

    response = client.get_data(
        route="electricity/retail-sales",
        facets={"stateid": ["CA", "TX"]},
        frequency="annual",
    )

    assert response.total == 4
    assert len(response.data) == 4


@respx.mock
def test_v2_date_range_filtering() -> None:
    """Test filtering by date range."""
    config = EIAConfig(api_key="test-key")
    client = EIAClient(config)

    mock_response = {
        "response": {
            "total": 3,
            "data": [
                {"period": "2024-03", "value": 30.0},
                {"period": "2024-02", "value": 20.0},
                {"period": "2024-01", "value": 10.0},
            ],
        }
    }

    respx.get("https://api.eia.gov/v2/electricity/retail-sales/data/").mock(
        return_value=Response(200, json=mock_response)
    )

    response = client.get_data(
        route="electricity/retail-sales",
        frequency="monthly",
        start="2024-01",
        end="2024-03",
    )

    assert len(response.data) == 3


@respx.mock
def test_v2_custom_data_fields() -> None:
    """Test requesting custom data fields."""
    config = EIAConfig(api_key="test-key")
    client = EIAClient(config)

    mock_response = {
        "response": {
            "total": 2,
            "data": [
                {"period": "2024", "value": 100.0, "price": 0.15},
                {"period": "2023", "value": 95.0, "price": 0.14},
            ],
        }
    }

    respx.get("https://api.eia.gov/v2/electricity/retail-sales/data/").mock(
        return_value=Response(200, json=mock_response)
    )

    response = client.get_data(
        route="electricity/retail-sales",
        data_fields=["value", "price"],
        frequency="annual",
    )

    assert "value" in response.data[0]
    assert "price" in response.data[0]


@respx.mock
def test_v2_empty_response() -> None:
    """Test handling of empty data response."""
    config = EIAConfig(api_key="test-key")
    client = EIAClient(config)

    mock_response = {
        "response": {
            "total": 0,
            "data": [],
        }
    }

    respx.get("https://api.eia.gov/v2/electricity/retail-sales/data/").mock(
        return_value=Response(200, json=mock_response)
    )

    df = client.get_dataframe(
        route="electricity/retail-sales",
        frequency="annual",
        auto_paginate=False,
    )

    assert len(df) == 0

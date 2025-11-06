"""Integration tests for Series endpoint."""

from __future__ import annotations

import respx
from httpx import Response

from eia import EIA, SeriesData


@respx.mock
def test_series_get_sync(client: EIA, mock_series_response: dict) -> None:
    """Test synchronous series retrieval."""
    respx.post("https://api.eia.gov/series/").mock(
        return_value=Response(200, json=mock_series_response)
    )

    series_data = client.series.get_series("test.series.1")

    assert len(series_data) == 1
    assert isinstance(series_data[0], SeriesData)
    assert series_data[0].series_id == "test.series.1"
    assert series_data[0].name == "Test Series 1"
    assert series_data[0].units == "billion cubic feet"
    assert len(series_data[0].data) == 3
    assert series_data[0].data[0] == ("202012", 100.5)


@respx.mock
async def test_series_get_async(client: EIA, mock_series_response: dict) -> None:
    """Test asynchronous series retrieval."""
    respx.post("https://api.eia.gov/series/").mock(
        return_value=Response(200, json=mock_series_response)
    )

    series_data = await client.series.get_series_async("test.series.1")

    assert len(series_data) == 1
    assert isinstance(series_data[0], SeriesData)
    assert series_data[0].series_id == "test.series.1"


@respx.mock
def test_series_get_dataframe_sync(client: EIA, mock_series_response: dict) -> None:
    """Test synchronous DataFrame retrieval."""
    respx.post("https://api.eia.gov/series/").mock(
        return_value=Response(200, json=mock_series_response)
    )

    df = client.series.get_dataframe("test.series.1")

    assert len(df) == 3
    assert "period" in df.columns
    assert "value" in df.columns
    assert "series_id" in df.columns
    assert df.iloc[0]["series_id"] == "test.series.1"
    assert df.iloc[0]["period"] == "202012"
    assert df.iloc[0]["value"] == 100.5


@respx.mock
async def test_series_get_dataframe_async(client: EIA, mock_series_response: dict) -> None:
    """Test asynchronous DataFrame retrieval."""
    respx.post("https://api.eia.gov/series/").mock(
        return_value=Response(200, json=mock_series_response)
    )

    df = await client.series.get_dataframe_async("test.series.1")

    assert len(df) == 3
    assert "period" in df.columns
    assert "value" in df.columns


@respx.mock
def test_series_get_dataframe_no_metadata(client: EIA, mock_series_response: dict) -> None:
    """Test DataFrame without metadata columns."""
    respx.post("https://api.eia.gov/series/").mock(
        return_value=Response(200, json=mock_series_response)
    )

    df = client.series.get_dataframe("test.series.1", include_metadata=False)

    assert len(df) == 3
    assert "period" in df.columns
    assert "value" in df.columns
    assert "series_id" not in df.columns


@respx.mock
def test_series_empty_input(client: EIA) -> None:
    """Test series endpoint with no series IDs."""
    result = client.series.get_series()
    assert result == []


@respx.mock
def test_series_multiple_batches(client: EIA) -> None:
    """Test series endpoint with multiple batches (>100 series)."""
    # Create a mock response for multiple series
    series_ids = [f"test.series.{i}" for i in range(150)]

    mock_response = {
        "request": {},
        "series": [
            {
                "series_id": sid,
                "name": f"Series {sid}",
                "units": "units",
                "f": "M",
                "data": [["202001", 100]],
            }
            for sid in series_ids[:100]
        ],
    }

    mock_response_2 = {
        "request": {},
        "series": [
            {
                "series_id": sid,
                "name": f"Series {sid}",
                "units": "units",
                "f": "M",
                "data": [["202001", 100]],
            }
            for sid in series_ids[100:]
        ],
    }

    # Mock both requests
    respx.post("https://api.eia.gov/series/").mock(
        side_effect=[
            Response(200, json=mock_response),
            Response(200, json=mock_response_2),
        ]
    )

    result = client.series.get_series(*series_ids)

    assert len(result) == 150

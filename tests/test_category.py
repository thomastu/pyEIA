"""Integration tests for Category endpoint."""

from __future__ import annotations

import respx
from httpx import Response

from eia import CategoryData, EIA


@respx.mock
def test_category_get_sync(client: EIA, mock_category_response: dict) -> None:
    """Test synchronous category retrieval."""
    respx.get("https://api.eia.gov/category/").mock(
        return_value=Response(200, json=mock_category_response)
    )

    category = client.category.get_category(371)

    assert isinstance(category, CategoryData)
    assert category.category_id == 371
    assert category.name == "Test Category"
    assert len(category.childcategories) == 2
    assert len(category.childseries) == 1


@respx.mock
async def test_category_get_async(client: EIA, mock_category_response: dict) -> None:
    """Test asynchronous category retrieval."""
    respx.get("https://api.eia.gov/category/").mock(
        return_value=Response(200, json=mock_category_response)
    )

    category = await client.category.get_category_async(371)

    assert isinstance(category, CategoryData)
    assert category.category_id == 371


@respx.mock
def test_category_child_categories_df(client: EIA, mock_category_response: dict) -> None:
    """Test child categories DataFrame."""
    respx.get("https://api.eia.gov/category/").mock(
        return_value=Response(200, json=mock_category_response)
    )

    df = client.category.get_child_categories_df(371)

    assert len(df) == 2
    assert "category_id" in df.columns
    assert "name" in df.columns
    assert "parent_category_id" in df.columns
    assert df.iloc[0]["parent_category_id"] == 371


@respx.mock
def test_category_child_series_df(client: EIA, mock_category_response: dict) -> None:
    """Test child series DataFrame."""
    respx.get("https://api.eia.gov/category/").mock(
        return_value=Response(200, json=mock_category_response)
    )

    df = client.category.get_child_series_df(371)

    assert len(df) == 1
    assert "series_id" in df.columns
    assert "name" in df.columns
    assert "category_id" in df.columns
    assert df.iloc[0]["category_id"] == 371


@respx.mock
def test_category_root(client: EIA) -> None:
    """Test getting root category (no category_id specified)."""
    mock_response = {
        "request": {},
        "category": {
            "category_id": 371,
            "name": "Root Category",
            "childcategories": [],
            "childseries": [],
        },
    }

    respx.get("https://api.eia.gov/category/").mock(return_value=Response(200, json=mock_response))

    category = client.category.get_category()

    assert category.category_id == 371
    assert category.parent_category_id is None


@respx.mock
def test_category_empty_children(client: EIA) -> None:
    """Test category with no children."""
    mock_response = {
        "request": {},
        "category": {
            "category_id": 999,
            "name": "Empty Category",
            "childcategories": [],
            "childseries": [],
        },
    }

    respx.get("https://api.eia.gov/category/").mock(return_value=Response(200, json=mock_response))

    df_categories = client.category.get_child_categories_df(999)
    df_series = client.category.get_child_series_df(999)

    assert len(df_categories) == 0
    assert len(df_series) == 0

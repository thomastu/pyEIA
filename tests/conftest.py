"""Test fixtures and configuration for pytest."""

from __future__ import annotations

import pytest

from eia import EIA, EIAConfig


@pytest.fixture
def api_key() -> str:
    """Provide a test API key."""
    return "test-api-key-12345"


@pytest.fixture
def config(api_key: str) -> EIAConfig:
    """Provide a test configuration."""
    return EIAConfig(api_key=api_key)


@pytest.fixture
def client(config: EIAConfig) -> EIA:
    """Provide a test EIA client."""
    return EIA.from_config(config)


@pytest.fixture
def mock_series_response() -> dict:
    """Provide mock series response data."""
    return {
        "request": {"series_id": "test.series.1", "api_key": "test"},
        "series": [
            {
                "series_id": "test.series.1",
                "name": "Test Series 1",
                "units": "billion cubic feet",
                "f": "M",
                "description": "Test description",
                "copyright": "None",
                "source": "EIA",
                "iso3166": "USA",
                "geography": "USA",
                "start": "202001",
                "end": "202012",
                "last_updated": "2024-01-01T00:00:00-05:00",
                "unitsshort": "Bcf",
                "data": [
                    ["202012", 100.5],
                    ["202011", 95.3],
                    ["202010", 90.1],
                ],
            }
        ],
    }


@pytest.fixture
def mock_category_response() -> dict:
    """Provide mock category response data."""
    return {
        "request": {"category_id": 371},
        "category": {
            "category_id": 371,
            "name": "Test Category",
            "parent_category_id": None,
            "notes": "Test notes",
            "childcategories": [
                {"category_id": 1, "name": "Child Category 1"},
                {"category_id": 2, "name": "Child Category 2"},
            ],
            "childseries": [
                {
                    "series_id": "test.series.1",
                    "name": "Test Series 1",
                    "f": "M",
                    "units": "Bcf",
                    "updated": "2024-01-01T00:00:00-05:00",
                    "unitsshort": "Bcf",
                }
            ],
        },
    }


@pytest.fixture
def mock_geoset_response() -> dict:
    """Provide mock geoset response data."""
    return {
        "request": {"geoset_id": "ELEC.GEN.ALL-99.A"},
        "geoset": [
            {
                "geoset_id": "ELEC.GEN.ALL-99.A",
                "region_id": "USA-CA",
                "name": "California",
                "f": "A",
                "units": "thousand megawatthours",
                "unitsshort": "thousand MWh",
                "data": [
                    ["2020", 285000],
                    ["2019", 280000],
                ],
            }
        ],
    }


@pytest.fixture
def mock_search_response() -> dict:
    """Provide mock search response data."""
    return {
        "request": {"search_term": "crude oil"},
        "response": {
            "numFound": 2,
            "docs": [
                {
                    "series_id": "PET.MCRFPUS1.M",
                    "name": "U.S. Crude Oil Production",
                    "f": "M",
                    "units": "Thousand Barrels per Day",
                    "last_updated": "2024-01-01T00:00:00-05:00",
                    "unitsshort": "Mb/d",
                    "description": "Test description",
                    "geography": "USA",
                    "start": "202001",
                    "end": "202012",
                },
                {
                    "series_id": "PET.MCRFPUS2.M",
                    "name": "U.S. Crude Oil Imports",
                    "f": "M",
                    "units": "Thousand Barrels per Day",
                    "last_updated": "2024-01-01T00:00:00-05:00",
                },
            ],
        },
    }


@pytest.fixture
def mock_updates_response() -> dict:
    """Provide mock updates response data."""
    return {
        "request": {"category_id": 371, "rows": 50},
        "updates": [
            {
                "series_id": "test.series.1",
                "name": "Test Series 1",
                "f": "M",
                "units": "Bcf",
                "updated": "2024-01-01T00:00:00-05:00",
                "unitsshort": "Bcf",
            }
        ],
    }


@pytest.fixture
def mock_series_category_response() -> dict:
    """Provide mock series category response data."""
    return {
        "request": {"series_id": "test.series.1"},
        "series_categories": [
            {"series_id": "test.series.1", "categories": [371, 1, 2]},
        ],
    }

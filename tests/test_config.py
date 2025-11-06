"""Tests for EIA configuration."""

from __future__ import annotations

import os

import pytest

from eia import EIA, EIAConfig


def test_config_creation() -> None:
    """Test basic configuration creation."""
    config = EIAConfig(api_key="test-key")

    assert config.api_key == "test-key"
    assert config.base_url == "https://api.eia.gov"
    assert config.timeout == 600.0


def test_config_custom_values() -> None:
    """Test configuration with custom values."""
    config = EIAConfig(api_key="test-key", base_url="https://custom.url", timeout=120.0)

    assert config.api_key == "test-key"
    assert config.base_url == "https://custom.url"
    assert config.timeout == 120.0


def test_config_missing_api_key() -> None:
    """Test that missing API key raises error."""
    with pytest.raises(ValueError, match="API key is required"):
        EIAConfig(api_key="")


def test_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test configuration from environment variable."""
    monkeypatch.setenv("EIA_API_KEY", "env-test-key")

    config = EIAConfig.from_env()

    assert config.api_key == "env-test-key"


def test_config_from_env_custom_var(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test configuration from custom environment variable."""
    monkeypatch.setenv("MY_CUSTOM_KEY", "custom-test-key")

    config = EIAConfig.from_env("MY_CUSTOM_KEY")

    assert config.api_key == "custom-test-key"


def test_config_from_env_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that missing environment variable raises error."""
    monkeypatch.delenv("EIA_API_KEY", raising=False)

    with pytest.raises(ValueError, match="Environment variable EIA_API_KEY is not set"):
        EIAConfig.from_env()


def test_client_from_config() -> None:
    """Test creating client from config object."""
    config = EIAConfig(api_key="test-key")
    client = EIA.from_config(config)

    assert client.config.api_key == "test-key"


def test_client_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test creating client from environment."""
    monkeypatch.setenv("EIA_API_KEY", "env-test-key")

    client = EIA.from_env()

    assert client.config.api_key == "env-test-key"


def test_client_direct_creation() -> None:
    """Test creating client directly."""
    client = EIA(api_key="test-key")

    assert client.config.api_key == "test-key"


def test_client_lazy_endpoint_creation() -> None:
    """Test that endpoints are created lazily."""
    client = EIA(api_key="test-key")

    # Endpoints should be None initially
    assert client._series is None
    assert client._category is None

    # Accessing properties should create them
    _ = client.series
    assert client._series is not None

    _ = client.category
    assert client._category is not None


def test_client_endpoint_reuse() -> None:
    """Test that endpoints are reused (not recreated)."""
    client = EIA(api_key="test-key")

    series1 = client.series
    series2 = client.series

    assert series1 is series2

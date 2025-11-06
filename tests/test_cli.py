"""Tests for CLI browser to ensure robustness."""

import pytest
from unittest.mock import Mock, patch
from eia.cli.browser import fetch_data_interactive


def test_fetch_data_with_list_format():
    """Test that browser handles data as list format."""
    client = Mock()
    route = "test/route"

    # API sometimes returns data as a list instead of dict
    route_info = {
        "data": ["column1", "column2", "column3"],
        "frequency": ["annual", "monthly"],
        "facets": ["stateid", "sectorid"],
    }

    # Mock the prompts and client call
    with patch("eia.cli.browser.Prompt") as mock_prompt:
        with patch("eia.cli.browser.Confirm") as mock_confirm:
            with patch("eia.cli.browser.console"):
                # Provide values for: data columns, frequency, max rows, and "press enter"
                mock_prompt.ask.side_effect = ["all", "annual", "100", ""]
                mock_confirm.ask.return_value = False  # Don't export to CSV

                mock_response = {
                    "response": {
                        "data": [{"column1": "value1"}],
                        "total": 1,
                    }
                }
                client.get_data.return_value = mock_response

                # Should not crash
                fetch_data_interactive(client, route, route_info)

                # Verify client was called
                assert client.get_data.called


def test_fetch_data_with_dict_format():
    """Test that browser handles data as dict format."""
    client = Mock()
    route = "test/route"

    # API sometimes returns data as a dict with metadata
    route_info = {
        "data": {
            "column1": {"alias": "Column 1", "units": "MW"},
            "column2": {"alias": "Column 2"},
        },
        "frequency": ["annual"],
    }

    with patch("eia.cli.browser.Prompt") as mock_prompt:
        with patch("eia.cli.browser.Confirm") as mock_confirm:
            with patch("eia.cli.browser.console"):
                # Provide values for all prompts
                mock_prompt.ask.side_effect = ["all", "annual", "100", ""]
                mock_confirm.ask.return_value = False

                mock_response = {
                    "response": {
                        "data": [{"column1": "value1"}],
                        "total": 1,
                    }
                }
                client.get_data.return_value = mock_response

                # Should not crash
                fetch_data_interactive(client, route, route_info)

                assert client.get_data.called


def test_fetch_data_with_mixed_format():
    """Test that browser handles data dict with non-dict values."""
    client = Mock()
    route = "test/route"

    # Edge case: dict with some non-dict values
    route_info = {
        "data": {
            "column1": {"alias": "Column 1"},
            "column2": "simple_value",  # Not a dict
        },
        "frequency": "annual",  # Not a list
    }

    with patch("eia.cli.browser.Prompt") as mock_prompt:
        with patch("eia.cli.browser.Confirm") as mock_confirm:
            with patch("eia.cli.browser.console"):
                # Provide values for all prompts
                mock_prompt.ask.side_effect = ["all", "annual", "100", ""]
                mock_confirm.ask.return_value = False

                mock_response = {
                    "response": {
                        "data": [{"column1": "value1"}],
                        "total": 1,
                    }
                }
                client.get_data.return_value = mock_response

                # Should not crash
                fetch_data_interactive(client, route, route_info)

                assert client.get_data.called

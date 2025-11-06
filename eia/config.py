"""Configuration for EIA API client using dependency injection."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class EIAConfig:
    """Configuration for EIA API client.

    Args:
        api_key: Your EIA API key. Register at www.eia.gov/opendata/register.cfm
        base_url: Base URL for the EIA API (default: https://api.eia.gov)
        timeout: Request timeout in seconds (default: 600)

    Examples:
        >>> # From environment variable
        >>> config = EIAConfig.from_env()

        >>> # Explicit configuration
        >>> config = EIAConfig(api_key="your-api-key-here")
    """

    api_key: str
    base_url: str = "https://api.eia.gov"
    timeout: float = 600.0

    def __post_init__(self) -> None:
        """Validate configuration."""
        if not self.api_key:
            msg = (
                "API key is required. Get one at www.eia.gov/opendata/register.cfm\n"
                "Set via environment variable EIA_API_KEY or pass directly to EIAConfig."
            )
            raise ValueError(msg)

    @classmethod
    def from_env(cls, env_var: str = "EIA_API_KEY") -> EIAConfig:
        """Create configuration from environment variable.

        Args:
            env_var: Name of environment variable containing API key

        Returns:
            EIAConfig instance

        Raises:
            ValueError: If environment variable is not set
        """
        api_key = os.getenv(env_var)
        if not api_key:
            msg = f"Environment variable {env_var} is not set"
            raise ValueError(msg)
        return cls(api_key=api_key)


# Constants
DEFAULT_OUTPUT_FORMAT: Final[str] = "json"
MAX_SERIES_PER_REQUEST: Final[int] = 100
DEFAULT_SEARCH_ROWS: Final[int] = 5000
MAX_UPDATES_ROWS: Final[int] = 10000

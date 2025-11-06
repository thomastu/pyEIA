"""Main EIA API client providing access to all endpoints."""

from __future__ import annotations

from eia.config import EIAConfig
from eia.endpoints import (
    CategoryEndpoint,
    GeosetEndpoint,
    SearchEndpoint,
    SeriesCategoryEndpoint,
    SeriesEndpoint,
    UpdatesEndpoint,
)


class EIA:
    """Main client for accessing the EIA API.

    Provides access to all EIA API endpoints with both async and sync support.

    Examples:
        >>> # Initialize with environment variable
        >>> from eia import EIA
        >>> client = EIA.from_env()

        >>> # Initialize with explicit API key
        >>> client = EIA(api_key="your-api-key")

        >>> # Use endpoints synchronously
        >>> series_data = client.series.get_series("series1", "series2")
        >>> df = client.series.get_dataframe("series1", "series2")

        >>> # Use endpoints asynchronously
        >>> series_data = await client.series.get_series_async("series1", "series2")
        >>> df = await client.series.get_dataframe_async("series1", "series2")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.eia.gov",
        timeout: float = 600.0,
    ) -> None:
        """Initialize the EIA client.

        Args:
            api_key: Your EIA API key (get one at www.eia.gov/opendata/register.cfm)
            base_url: Base URL for the API (default: https://api.eia.gov)
            timeout: Request timeout in seconds (default: 600)

        Examples:
            >>> client = EIA(api_key="your-api-key")
        """
        self.config = EIAConfig(api_key=api_key, base_url=base_url, timeout=timeout)
        self._series: SeriesEndpoint | None = None
        self._category: CategoryEndpoint | None = None
        self._geoset: GeosetEndpoint | None = None
        self._search: SearchEndpoint | None = None
        self._updates: UpdatesEndpoint | None = None
        self._series_category: SeriesCategoryEndpoint | None = None

    @classmethod
    def from_env(cls, env_var: str = "EIA_API_KEY") -> EIA:
        """Create client from environment variable.

        Args:
            env_var: Name of environment variable containing API key

        Returns:
            EIA client instance

        Examples:
            >>> # Uses EIA_API_KEY environment variable
            >>> client = EIA.from_env()
            >>> # Use custom environment variable
            >>> client = EIA.from_env("MY_EIA_KEY")
        """
        config = EIAConfig.from_env(env_var)
        return cls(api_key=config.api_key, base_url=config.base_url, timeout=config.timeout)

    @classmethod
    def from_config(cls, config: EIAConfig) -> EIA:
        """Create client from configuration object.

        Args:
            config: EIA configuration object

        Returns:
            EIA client instance

        Examples:
            >>> config = EIAConfig(api_key="your-key")
            >>> client = EIA.from_config(config)
        """
        return cls(api_key=config.api_key, base_url=config.base_url, timeout=config.timeout)

    @property
    def series(self) -> SeriesEndpoint:
        """Access the Series endpoint.

        Returns:
            SeriesEndpoint instance

        Examples:
            >>> data = client.series.get_series("series1", "series2")
            >>> df = client.series.get_dataframe("series1")
        """
        if self._series is None:
            self._series = SeriesEndpoint(self.config)
        return self._series

    @property
    def category(self) -> CategoryEndpoint:
        """Access the Category endpoint.

        Returns:
            CategoryEndpoint instance

        Examples:
            >>> category = client.category.get_category(371)
            >>> child_series_df = client.category.get_child_series_df(371)
        """
        if self._category is None:
            self._category = CategoryEndpoint(self.config)
        return self._category

    @property
    def geoset(self) -> GeosetEndpoint:
        """Access the Geoset endpoint.

        Returns:
            GeosetEndpoint instance

        Examples:
            >>> data = client.geoset.get_geoset("ELEC.GEN.ALL-99.A", "USA-CA", "USA-FL")
            >>> df = client.geoset.get_dataframe("ELEC.GEN.ALL-99.A", "USA-CA")
        """
        if self._geoset is None:
            self._geoset = GeosetEndpoint(self.config)
        return self._geoset

    @property
    def search(self) -> SearchEndpoint:
        """Access the Search endpoint.

        Returns:
            SearchEndpoint instance

        Examples:
            >>> results = client.search.search("name", "crude oil")
            >>> df = client.search.search_dataframe("series_id", "EMI_CO2*")
        """
        if self._search is None:
            self._search = SearchEndpoint(self.config)
        return self._search

    @property
    def updates(self) -> UpdatesEndpoint:
        """Access the Updates endpoint.

        Returns:
            UpdatesEndpoint instance

        Examples:
            >>> updates = client.updates.get_updates(category_id=371, rows=100)
            >>> df = client.updates.get_dataframe(category_id=371)
        """
        if self._updates is None:
            self._updates = UpdatesEndpoint(self.config)
        return self._updates

    @property
    def series_category(self) -> SeriesCategoryEndpoint:
        """Access the SeriesCategory endpoint.

        Returns:
            SeriesCategoryEndpoint instance

        Examples:
            >>> results = client.series_category.get_series_categories("series1", "series2")
            >>> df = client.series_category.get_dataframe("series1")
        """
        if self._series_category is None:
            self._series_category = SeriesCategoryEndpoint(self.config)
        return self._series_category

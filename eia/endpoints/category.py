"""Category endpoint implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd

from eia.client import BaseClient
from eia.models import CategoryData, ChildCategory, ChildSeries

if TYPE_CHECKING:
    from eia.config import EIAConfig


class CategoryEndpoint:
    """Endpoint for navigating the EIA category hierarchy.

    Categories organize the EIA data into a hierarchical structure.

    Examples:
        >>> from eia import EIAConfig, CategoryEndpoint
        >>> config = EIAConfig.from_env()
        >>> endpoint = CategoryEndpoint(config)
        >>> # Get root category
        >>> category = endpoint.get_category()
        >>> # Get specific category
        >>> category = endpoint.get_category(371)
    """

    def __init__(self, config: EIAConfig) -> None:
        """Initialize the category endpoint.

        Args:
            config: EIA API configuration
        """
        self._client = BaseClient(config, "category")

    async def get_category_async(self, category_id: int | None = None) -> CategoryData:
        """Retrieve category information asynchronously.

        Args:
            category_id: Category ID to retrieve (None for root category)

        Returns:
            CategoryData object

        Examples:
            >>> category = await endpoint.get_category_async(371)
        """
        params = {}
        if category_id is not None:
            params["category_id"] = category_id

        response = await self._client._get_async(params=params)
        return self._parse_category(response["category"])

    def get_category(self, category_id: int | None = None) -> CategoryData:
        """Retrieve category information synchronously.

        Args:
            category_id: Category ID to retrieve (None for root category)

        Returns:
            CategoryData object

        Examples:
            >>> category = endpoint.get_category(371)
        """
        params = {}
        if category_id is not None:
            params["category_id"] = category_id

        response = self._client._get_sync(params=params)
        return self._parse_category(response["category"])

    def _parse_category(self, raw: dict[str, Any]) -> CategoryData:
        """Parse raw category data into CategoryData model."""
        childcategories = [
            ChildCategory(
                category_id=c["category_id"],
                name=c["name"],
            )
            for c in raw.get("childcategories", [])
        ]

        childseries = [
            ChildSeries(
                series_id=s["series_id"],
                name=s["name"],
                f=s["f"],
                units=s["units"],
                updated=s["updated"],
                unitsshort=s.get("unitsshort"),
            )
            for s in raw.get("childseries", [])
        ]

        return CategoryData(
            category_id=raw["category_id"],
            name=raw["name"],
            parent_category_id=raw.get("parent_category_id"),
            childcategories=childcategories,
            childseries=childseries,
            notes=raw.get("notes"),
        )

    async def get_child_categories_df_async(self, category_id: int | None = None) -> pd.DataFrame:
        """Get child categories as DataFrame asynchronously.

        Args:
            category_id: Category ID to retrieve (None for root category)

        Returns:
            DataFrame with child category information

        Examples:
            >>> df = await endpoint.get_child_categories_df_async(371)
        """
        category = await self.get_category_async(category_id)
        return self._child_categories_to_df(category)

    def get_child_categories_df(self, category_id: int | None = None) -> pd.DataFrame:
        """Get child categories as DataFrame synchronously.

        Args:
            category_id: Category ID to retrieve (None for root category)

        Returns:
            DataFrame with child category information

        Examples:
            >>> df = endpoint.get_child_categories_df(371)
        """
        category = self.get_category(category_id)
        return self._child_categories_to_df(category)

    def _child_categories_to_df(self, category: CategoryData) -> pd.DataFrame:
        """Convert child categories to DataFrame."""
        if not category.childcategories:
            return pd.DataFrame()

        data = [
            {
                "category_id": c.category_id,
                "name": c.name,
                "parent_category_id": category.category_id,
                "parent_category_name": category.name,
            }
            for c in category.childcategories
        ]
        return pd.DataFrame(data)

    async def get_child_series_df_async(self, category_id: int | None = None) -> pd.DataFrame:
        """Get child series as DataFrame asynchronously.

        Args:
            category_id: Category ID to retrieve (None for root category)

        Returns:
            DataFrame with child series information

        Examples:
            >>> df = await endpoint.get_child_series_df_async(371)
        """
        category = await self.get_category_async(category_id)
        return self._child_series_to_df(category)

    def get_child_series_df(self, category_id: int | None = None) -> pd.DataFrame:
        """Get child series as DataFrame synchronously.

        Args:
            category_id: Category ID to retrieve (None for root category)

        Returns:
            DataFrame with child series information

        Examples:
            >>> df = endpoint.get_child_series_df(371)
        """
        category = self.get_category(category_id)
        return self._child_series_to_df(category)

    def _child_series_to_df(self, category: CategoryData) -> pd.DataFrame:
        """Convert child series to DataFrame."""
        if not category.childseries:
            return pd.DataFrame()

        data = [
            {
                "series_id": s.series_id,
                "name": s.name,
                "f": s.f,
                "units": s.units,
                "updated": s.updated,
                "unitsshort": s.unitsshort,
                "category_id": category.category_id,
                "parent_category_id": category.parent_category_id,
                "category_name": category.name,
            }
            for s in category.childseries
        ]
        return pd.DataFrame(data)

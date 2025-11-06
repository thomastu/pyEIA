"""Quickstart example for pyEIA - Modern fully-typed EIA API client.

This example demonstrates:
1. Basic client initialization
2. Fetching series data
3. Working with DataFrames
4. Async/sync operations
"""

import asyncio

from eia import EIA


def sync_example() -> None:
    """Synchronous usage example."""
    print("=== Synchronous Example ===\n")

    # Initialize client from environment variable (EIA_API_KEY)
    client = EIA.from_env()

    # Fetch a single series
    series_data = client.series.get_series(
        "AEO.2015.REF2015.CNSM_DEU_TOTD_NA_DEU_NA_ENC_QBTU.A"
    )

    # Print series information
    for series in series_data:
        print(f"Series: {series.name}")
        print(f"Units: {series.units}")
        print(f"Frequency: {series.f}")
        print(f"Data points: {len(series.data)}")
        print("\nFirst 5 data points:")
        for period, value in series.data[:5]:
            print(f"  {period}: {value}")

    print("\n" + "=" * 50 + "\n")

    # Fetch multiple series as DataFrame
    df = client.series.get_dataframe(
        "AEO.2015.REF2015.CNSM_DEU_TOTD_NA_DEU_NA_ENC_QBTU.A",
        "AEO.2015.REF2015.CNSM_ENU_ALLS_NA_DFO_DELV_ENC_QBTU.A",
    )

    print("DataFrame shape:", df.shape)
    print("\nDataFrame columns:", df.columns.tolist())
    print("\nFirst 5 rows:")
    print(df.head())


async def async_example() -> None:
    """Asynchronous usage example."""
    print("\n=== Asynchronous Example ===\n")

    client = EIA.from_env()

    # Fetch series data asynchronously
    series_data = await client.series.get_series_async(
        "AEO.2015.REF2015.CNSM_DEU_TOTD_NA_DEU_NA_ENC_QBTU.A"
    )

    print(f"Fetched {len(series_data)} series asynchronously")

    # Fetch DataFrame asynchronously
    df = await client.series.get_dataframe_async(
        "AEO.2015.REF2015.CNSM_DEU_TOTD_NA_DEU_NA_ENC_QBTU.A",
        "AEO.2015.REF2015.CNSM_ENU_ALLS_NA_DFO_DELV_ENC_QBTU.A",
    )

    print(f"DataFrame shape: {df.shape}")


def category_example() -> None:
    """Example of navigating categories."""
    print("\n=== Category Example ===\n")

    client = EIA.from_env()

    # Get root category
    root = client.category.get_category(371)

    print(f"Category: {root.name}")
    print(f"Number of child categories: {len(root.childcategories)}")
    print(f"Number of child series: {len(root.childseries)}")

    if root.childcategories:
        print("\nFirst 5 child categories:")
        for cat in root.childcategories[:5]:
            print(f"  [{cat.category_id}] {cat.name}")

    # Get child series as DataFrame
    if root.childseries:
        df = client.category.get_child_series_df(371)
        print(f"\nChild series DataFrame shape: {df.shape}")


def search_example() -> None:
    """Example of searching for data."""
    print("\n=== Search Example ===\n")

    client = EIA.from_env()

    # Search for crude oil series
    results = client.search.search("name", "crude oil", rows_per_page=10)

    print(f"Found {len(results)} results for 'crude oil'")
    print("\nFirst 3 results:")
    for result in results[:3]:
        print(f"  {result.series_id}: {result.name}")


def main() -> None:
    """Run all examples."""
    # Synchronous examples
    sync_example()
    category_example()
    search_example()

    # Asynchronous example
    asyncio.run(async_example())


if __name__ == "__main__":
    main()

# pyEIA - Fully Typed Python Client for the EIA API

A modern, fully-typed Python client for the [U.S. Energy Information Administration (EIA) API](https://www.eia.gov/opendata/). Built with type safety, developer experience, and performance in mind.

## Features

- **Fully Typed**: Complete type hints with mypy strict mode compliance
- **Async & Sync**: Native support for both asynchronous and synchronous operations
- **Modern Python**: Built for Python 3.9+ with modern language features
- **Clean API**: Intuitive, well-documented interface
- **Minimal Dependencies**: Only essential dependencies (httpx, pandas)
- **Type-Safe Models**: Immutable dataclasses for all API responses
- **Well Tested**: Comprehensive test suite with property-based testing
- **Zero Configuration**: Simple dependency injection, no config files needed

## Installation

```bash
# Using uv (recommended)
uv add pyeia

# Using pip
pip install pyeia
```

## Quick Start

### Basic Usage

```python
from eia import EIA

# Initialize client with API key from environment variable
client = EIA.from_env()  # Reads from EIA_API_KEY

# Or pass API key directly
client = EIA(api_key="your-api-key-here")

# Get series data synchronously
series_data = client.series.get_series(
    "AEO.2015.REF2015.CNSM_DEU_TOTD_NA_DEU_NA_ENC_QBTU.A"
)

# Get series data as a pandas DataFrame
df = client.series.get_dataframe(
    "AEO.2015.REF2015.CNSM_DEU_TOTD_NA_DEU_NA_ENC_QBTU.A",
    "AEO.2015.REF2015.CNSM_ENU_ALLS_NA_DFO_DELV_ENC_QBTU.A"
)
```

### Async Usage

```python
import asyncio
from eia import EIA

async def main():
    client = EIA.from_env()

    # Get series data asynchronously
    series_data = await client.series.get_series_async(
        "AEO.2015.REF2015.CNSM_DEU_TOTD_NA_DEU_NA_ENC_QBTU.A"
    )

    # Get DataFrame asynchronously
    df = await client.series.get_dataframe_async(
        "AEO.2015.REF2015.CNSM_DEU_TOTD_NA_DEU_NA_ENC_QBTU.A"
    )

    return df

# Run async code
df = asyncio.run(main())
```

## API Endpoints

### Series Endpoint

Retrieve time series data:

```python
# Get multiple series at once
series_data = client.series.get_series("series1", "series2", "series3")

# Each series is a fully typed SeriesData object
for series in series_data:
    print(f"{series.name}: {series.units}")
    for period, value in series.data:
        print(f"  {period}: {value}")

# Get as DataFrame with metadata
df = client.series.get_dataframe("series1", "series2", include_metadata=True)

# Get as DataFrame without metadata (just period and value)
df = client.series.get_dataframe("series1", include_metadata=False)
```

### Category Endpoint

Navigate the EIA category hierarchy:

```python
# Get root category
root = client.category.get_category()

# Get specific category
category = client.category.get_category(371)

# Get child categories as DataFrame
child_categories = client.category.get_child_categories_df(371)

# Get child series as DataFrame
child_series = client.category.get_child_series_df(371)
```

### Geoset Endpoint

Retrieve geographic series collections:

```python
# Get geoset data for specific regions
data = client.geoset.get_geoset(
    "ELEC.GEN.ALL-99.A",
    "USA-CA",
    "USA-FL",
    "USA-MN"
)

# Get as DataFrame
df = client.geoset.get_dataframe("ELEC.GEN.ALL-99.A", "USA-CA", "USA-FL")
```

### Search Endpoint

Search the EIA database:

```python
# Search by series ID
results = client.search.search("series_id", "EMI_CO2*")

# Search by name
results = client.search.search("name", "crude oil", rows_per_page=100)

# Search by date range
results = client.search.search(
    "last_updated",
    ("2020-01-01", "2020-12-31")
)

# Get search results as DataFrame
df = client.search.search_dataframe("name", "crude oil")
```

### Updates Endpoint

Get recently updated series:

```python
# Get recent updates for a category
updates = client.updates.get_updates(category_id=371, rows=100)

# Get all updates with pagination
all_updates = client.updates.get_all_updates(category_id=371, deep=True)

# Get updates as DataFrame
df = client.updates.get_dataframe(category_id=371)
```

### Series Category Endpoint

Find categories associated with series:

```python
# Get categories for series
results = client.series_category.get_series_categories("series1", "series2")

# Get as DataFrame
df = client.series_category.get_dataframe("series1", "series2")
```

## Configuration

### API Key

Get your free API key at [www.eia.gov/opendata/register.cfm](https://www.eia.gov/opendata/register.cfm)

Configure via:

1. **Environment variable** (recommended):
   ```bash
   export EIA_API_KEY="your-api-key"
   ```

2. **Direct configuration**:
   ```python
   from eia import EIA
   client = EIA(api_key="your-api-key")
   ```

3. **Custom environment variable**:
   ```python
   from eia import EIA
   client = EIA.from_env("MY_CUSTOM_EIA_KEY")
   ```

4. **Configuration object**:
   ```python
   from eia import EIAConfig, EIA
   config = EIAConfig(
       api_key="your-api-key",
       base_url="https://api.eia.gov",  # Optional
       timeout=600.0  # Optional, in seconds
   )
   client = EIA.from_config(config)
   ```

## Type Safety

All API responses are fully typed with immutable dataclasses:

```python
from eia import SeriesData, CategoryData

# Series data is fully typed
series: SeriesData = client.series.get_series("series1")[0]
print(series.series_id)  # Type: str
print(series.name)  # Type: str
print(series.units)  # Type: str
print(series.data)  # Type: list[tuple[str, float | int | str | None]]

# Category data is fully typed
category: CategoryData = client.category.get_category(371)
print(category.category_id)  # Type: int
print(category.childcategories)  # Type: list[ChildCategory]
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/thomastu/pyEIA.git
cd pyEIA

# Install dependencies with uv
uv sync --all-extras
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=eia --cov-report=html

# Run type checking
uv run mypy eia/ --strict

# Run linting
uv run ruff check eia/
```

### Code Quality

This project maintains high code quality standards:

- **Type checking**: Full mypy strict mode compliance
- **Linting**: Ruff for fast, modern Python linting
- **Testing**: pytest with hypothesis for property-based testing
- **No network calls in tests**: All tests use mocks via respx

## Use Cases

### Batch Data Download for Analysis

```python
from eia import EIA
import duckdb

# Initialize client
client = EIA.from_env()

# Download multiple series
series_ids = [
    "AEO.2015.REF2015.CNSM_DEU_TOTD_NA_DEU_NA_ENC_QBTU.A",
    "AEO.2015.REF2015.CNSM_ENU_ALLS_NA_DFO_DELV_ENC_QBTU.A",
    # ... more series
]

# Get as DataFrame
df = client.series.get_dataframe(*series_ids)

# Query with DuckDB
con = duckdb.connect()
result = con.execute("""
    SELECT period, series_id, value
    FROM df
    WHERE value > 100
    ORDER BY period DESC
""").fetchdf()

print(result)
```

### Async Batch Processing

```python
import asyncio
from eia import EIA

async def fetch_category_series(client: EIA, category_id: int):
    """Fetch all series for a category."""
    # Get category
    category = await client.category.get_category_async(category_id)

    # Get child series IDs
    series_ids = [s.series_id for s in category.childseries]

    # Fetch all series data
    if series_ids:
        return await client.series.get_dataframe_async(*series_ids)
    return None

async def main():
    client = EIA.from_env()

    # Fetch multiple categories in parallel
    categories = [371, 714755, 714804]
    tasks = [fetch_category_series(client, cat_id) for cat_id in categories]
    results = await asyncio.gather(*tasks)

    return results

# Run
results = asyncio.run(main())
```

## Migration from v0.x

The new v1.0 API is completely redesigned. Key changes:

### Old API (v0.x)
```python
from eia import api

series = api.Series(
    "series1",
    "series2",
    api_key="key"
)
data = series.to_dict()
df = series.to_dataframe()
```

### New API (v1.0)
```python
from eia import EIA

client = EIA(api_key="key")
data = client.series.get_series("series1", "series2")
df = client.series.get_dataframe("series1", "series2")
```

## License

BSD-3-Clause-LBNL

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Links

- **Repository**: https://github.com/thomastu/pyEIA
- **EIA API Documentation**: https://www.eia.gov/opendata/commands.php
- **Get API Key**: https://www.eia.gov/opendata/register.cfm

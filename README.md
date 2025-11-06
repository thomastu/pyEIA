# pyEIA

Modern, fully-typed Python client for the U.S. Energy Information Administration (EIA) API v2.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Type Hints](https://img.shields.io/badge/type%20hints-yes-brightgreen.svg)](https://www.python.org/dev/peps/pep-0484/)

## Features

- **Fully Typed**: Complete type safety using modern Python type hints (TypedDict)
- **Sync & Async**: Both synchronous and asynchronous interfaces
- **Zero Runtime Overhead**: Uses standard library types for maximum performance
- **Minimal Dependencies**: Only requires `httpx` for HTTP requests
- **Bulk Data Support**: Built-in pagination for large-scale data ingestion
- **Modern Python**: Leverages Python 3.10+ features for clean, expressive code
- **Well Tested**: Comprehensive test suite with property-based testing

## Installation

Install using `uv` (recommended):

```bash
uv pip install pyeia
```

Or with pip:

```bash
pip install pyeia
```

For development:

```bash
uv pip install -e ".[dev]"
```

## Quick Start

### Get Your API Key

Register for a free API key at [https://www.eia.gov/opendata/register.php](https://www.eia.gov/opendata/register.php)

### Basic Usage

```python
from eia import EIAClient

# Initialize the client
client = EIAClient(api_key="your_api_key_here")

# Get electricity retail sales data
response = client.get_data(
    route="electricity/retail-sales",
    data=["price", "revenue", "sales"],
    frequency="annual",
    facets={"sectorid": ["RES", "COM"]},  # Residential and Commercial
    start="2020",
    end="2023",
)

print(f"Retrieved {response['response']['total']} records")
for record in response['response']['data']:
    print(f"{record['period']}: ${record['price']:.2f}/MWh")
```

### Async Usage

```python
from eia import AsyncEIAClient
import asyncio

async def fetch_data():
    async with AsyncEIAClient(api_key="your_api_key_here") as client:
        response = await client.get_data(
            route="electricity/retail-sales",
            data=["price"],
            frequency="monthly",
            start="2023-01",
            end="2023-12",
        )
        return response['response']['data']

# Run async function
data = asyncio.run(fetch_data())
```

## Core Features

### 1. Discover Available Data

```python
from eia import EIAClient

client = EIAClient(api_key="your_api_key")

# Get all available routes
routes = client.get_route()
for route in routes['response']['routes']:
    print(f"{route['id']}: {route['name']}")

# Get details for a specific route
electricity = client.get_route("electricity")
print(electricity['response']['description'])
```

### 2. Explore Facets (Filters)

```python
# Get available sector types for retail sales
facets = client.get_facet(
    route="electricity/retail-sales",
    facet="sectorid"
)

for facet in facets['response']['facets']:
    print(f"{facet['id']}: {facet['name']}")
# Output:
# RES: Residential
# COM: Commercial
# IND: Industrial
# ...
```

### 3. Fetch Data with Filters

```python
# Get California and New York residential electricity prices
response = client.get_data(
    route="electricity/retail-sales",
    data=["price"],
    frequency="monthly",
    facets={
        "stateid": ["CA", "NY"],
        "sectorid": ["RES"]
    },
    start="2023-01",
    end="2023-12",
    sort=[("period", "desc")],
)

data = response['response']['data']
print(f"Found {len(data)} records")
```

### 4. Bulk Data Ingestion

For large datasets, use `get_all_data()` which automatically handles pagination:

```python
# Fetch all data (handles pagination automatically)
all_data = client.get_all_data(
    route="electricity/retail-sales",
    data=["price", "revenue", "sales"],
    frequency="monthly",
    facets={"sectorid": ["RES"]},
    start="2020-01",
    end="2023-12",
)

print(f"Downloaded {len(all_data)} total records")

# Data is ready for bulk ingestion into analytics tools
# Example with DuckDB:
import duckdb
duckdb.query("SELECT * FROM all_data WHERE price > 100").show()
```

### 5. Legacy Series ID Support

For backwards compatibility with API v1:

```python
# Lookup by series ID
response = client.get_series("ELEC.GEN.ALL-99.A")
print(response['response']['name'])
print(response['response']['units'])
```

## Advanced Usage

### Context Manager

```python
# Automatically manage HTTP client lifecycle
with EIAClient(api_key="your_api_key") as client:
    data = client.get_data(
        route="electricity/retail-sales",
        data=["price"]
    )
    # Client is automatically closed when exiting context
```

### Custom Timeout

```python
# Set custom timeout for slow connections
client = EIAClient(
    api_key="your_api_key",
    timeout=120.0  # 2 minutes
)
```

### Multiple Facet Values

```python
# Filter by multiple states and sectors
response = client.get_data(
    route="electricity/retail-sales",
    data=["sales"],
    facets={
        "stateid": ["CA", "TX", "FL", "NY"],
        "sectorid": ["RES", "COM", "IND"],
    },
    frequency="annual",
)
```

### Pagination Control

```python
# Manual pagination for custom processing
offset = 0
page_size = 1000

while True:
    response = client.get_data(
        route="electricity/retail-sales",
        data=["price"],
        offset=offset,
        length=page_size,
    )

    batch = response['response']['data']
    if not batch:
        break

    # Process batch
    process_batch(batch)

    offset += page_size
```

## Integration with Data Tools

### DuckDB

```python
import duckdb
from eia import EIAClient

client = EIAClient(api_key="your_api_key")
data = client.get_all_data(
    route="electricity/retail-sales",
    data=["price", "sales", "revenue"],
    frequency="monthly",
)

# Query directly with DuckDB
result = duckdb.query("""
    SELECT
        period,
        AVG(price) as avg_price,
        SUM(sales) as total_sales
    FROM data
    GROUP BY period
    ORDER BY period
""").fetchdf()

print(result)
```

### Apache Arrow / Parquet

```python
import pyarrow as pa
from eia import EIAClient

client = EIAClient(api_key="your_api_key")
data = client.get_all_data(
    route="electricity/retail-sales",
    data=["price", "sales"],
    frequency="annual",
)

# Convert to Arrow table
table = pa.Table.from_pylist(data)

# Write to Parquet for efficient storage
import pyarrow.parquet as pq
pq.write_table(table, "electricity_data.parquet")
```

## API Reference

### EIAClient

Main synchronous client for the EIA API.

**Methods:**

- `get_data()` - Fetch data from a specific route
- `get_facet()` - Get available values for a facet/filter
- `get_route()` - Get metadata and available child routes
- `get_series()` - Get data by legacy series ID
- `get_all_data()` - Fetch all data with automatic pagination
- `close()` - Close the HTTP client

### AsyncEIAClient

Asynchronous version with the same interface (all methods are async).

### Response Types

All responses are fully typed using TypedDict:

- `DataResponse` - Response from data endpoints
- `FacetResponse` - Response from facet endpoints
- `RouteResponse` - Response from route/metadata endpoints
- `SeriesIDResponse` - Response from series ID endpoint

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/thomastu/pyEIA.git
cd pyEIA

# Create virtual environment with uv
uv venv
source .venv/bin/activate

# Install in development mode
uv pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=eia --cov-report=html

# Run specific test file
pytest tests/test_client.py -v
```

### Code Quality

```bash
# Format code
ruff format .

# Lint
ruff check .

# Type check
mypy eia/
```

## Migration from v1

The v1 API is deprecated. Here's how to migrate:

### Old (v1):
```python
from eia import api

series = api.Series(
    "ELEC.GEN.ALL-99.A",
    api_key=myapikey
)
data = series.to_dict()
```

### New (v2):
```python
from eia import EIAClient

client = EIAClient(api_key=myapikey)
response = client.get_series("ELEC.GEN.ALL-99.A")
data = response['response']['data']
```

## Performance

pyEIA v2 is designed for performance:

- **Zero runtime overhead**: Uses TypedDict instead of Pydantic for validation
- **Minimal dependencies**: Only httpx required
- **Efficient pagination**: Automatic batching for bulk operations
- **Type safety**: Full static type checking with mypy

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass and code is typed
5. Submit a pull request

## License

BSD-3-Clause-LBNL

## Resources

- [EIA API Documentation](https://www.eia.gov/opendata/documentation.php)
- [EIA Open Data Portal](https://www.eia.gov/opendata/)
- [API v2 Technical Docs](https://www.eia.gov/opendata/documentation/APIv2.1.0.pdf)
- [Get API Key](https://www.eia.gov/opendata/register.php)

## Support

- Issues: [GitHub Issues](https://github.com/thomastu/pyEIA/issues)
- Discussions: [GitHub Discussions](https://github.com/thomastu/pyEIA/discussions)

---

**Note**: This package is not officially associated with the U.S. Energy Information Administration.

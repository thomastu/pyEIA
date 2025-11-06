"""
ETL utilities for exporting EIA data to modern formats.

This module provides utilities for exporting EIA API data to:
- Apache Parquet files
- Apache Iceberg tables
- Delta Lake tables (future)

Requires optional dependencies: pip install pyeia[etl]
"""

from eia.etl.export import (
    to_parquet,
    to_iceberg,
    DataExporter,
)

__all__ = ["to_parquet", "to_iceberg", "DataExporter"]

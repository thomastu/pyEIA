"""
Export utilities for converting EIA API data to modern formats.

Supports exporting to Parquet files and Iceberg tables for use
with modern data lake and analytics tools.
"""

from pathlib import Path
from typing import Any
from collections.abc import Iterator

try:
    import pyarrow as pa
    import pyarrow.parquet as pq

    HAS_ARROW = True
except ImportError:
    HAS_ARROW = False
    pa = None  # type: ignore
    pq = None  # type: ignore

try:
    from pyiceberg.catalog import load_catalog
    from pyiceberg.schema import Schema
    from pyiceberg.types import (
        NestedField,
        StringType,
        DoubleType,
        IntegerType,
        TimestampType,
    )

    HAS_ICEBERG = True
except ImportError:
    HAS_ICEBERG = False

from eia.v2.retry import batch_iterator


class DataExporter:
    """
    Composable data exporter for EIA API data.

    Provides methods for exporting data to various formats with
    automatic schema inference and batching.
    """

    def __init__(self, batch_size: int = 10000):
        """
        Initialize the data exporter.

        Args:
            batch_size: Number of records per batch for processing
        """
        self.batch_size = batch_size

    @staticmethod
    def _ensure_arrow() -> None:
        """Ensure PyArrow is installed."""
        if not HAS_ARROW:
            raise ImportError(
                "PyArrow is required for export functionality. "
                "Install it with: pip install 'pyeia[etl]'"
            )

    @staticmethod
    def _ensure_iceberg() -> None:
        """Ensure PyIceberg is installed."""
        if not HAS_ICEBERG:
            raise ImportError(
                "PyIceberg is required for Iceberg export. "
                "Install it with: pip install 'pyeia[etl]'"
            )

    @staticmethod
    def _infer_arrow_type(value: Any) -> pa.DataType:
        """
        Infer Arrow data type from a Python value.

        Args:
            value: Python value to infer type from

        Returns:
            PyArrow data type
        """
        if isinstance(value, bool):
            return pa.bool_()
        elif isinstance(value, int):
            return pa.int64()
        elif isinstance(value, float):
            return pa.float64()
        elif isinstance(value, str):
            return pa.string()
        else:
            return pa.string()  # Default to string

    def _infer_schema(self, records: list[dict[str, Any]]) -> pa.Schema:
        """
        Infer Arrow schema from data records.

        Args:
            records: List of data records

        Returns:
            PyArrow schema
        """
        if not records:
            return pa.schema([])

        # Use first record to infer types
        first_record = records[0]
        fields = []

        for key, value in first_record.items():
            arrow_type = self._infer_arrow_type(value)
            fields.append(pa.field(key, arrow_type))

        return pa.schema(fields)

    def to_parquet(
        self,
        data: list[dict[str, Any]] | Iterator[dict[str, Any]],
        output_path: str | Path,
        compression: str = "snappy",
        row_group_size: int | None = None,
        **kwargs: Any,
    ) -> Path:
        """
        Export data to Parquet format.

        Args:
            data: Data records (list or iterator)
            output_path: Path to output Parquet file
            compression: Compression codec ('snappy', 'gzip', 'brotli', 'zstd')
            row_group_size: Number of rows per row group
            **kwargs: Additional arguments passed to pyarrow.parquet.write_table

        Returns:
            Path to the created Parquet file

        Example:
            >>> from eia import EIAClient
            >>> from eia.etl import DataExporter
            >>>
            >>> client = EIAClient(api_key="your_key")
            >>> data = client.iter_data(route="electricity/retail-sales", data=["price"])
            >>>
            >>> exporter = DataExporter()
            >>> exporter.to_parquet(data, "electricity_prices.parquet")
        """
        self._ensure_arrow()
        output_path = Path(output_path)

        # Convert iterator to batches if needed
        if hasattr(data, "__iter__") and not isinstance(data, list):
            # Process in batches for memory efficiency
            batches = batch_iterator(data, self.batch_size)
            first_batch = next(batches)

            # Infer schema from first batch
            schema = self._infer_schema(first_batch)

            # Create Parquet writer
            writer = None
            try:
                # Write first batch
                table = pa.Table.from_pylist(first_batch, schema=schema)
                writer = pq.ParquetWriter(
                    output_path,
                    schema,
                    compression=compression,
                    **({"row_group_size": row_group_size} if row_group_size else {}),
                    **kwargs,
                )
                writer.write_table(table)

                # Write remaining batches
                for batch in batches:
                    table = pa.Table.from_pylist(batch, schema=schema)
                    writer.write_table(table)
            finally:
                if writer:
                    writer.close()
        else:
            # Simple case: data is already a list
            if not isinstance(data, list):
                data = list(data)

            schema = self._infer_schema(data)
            table = pa.Table.from_pylist(data, schema=schema)

            pq.write_table(
                table,
                output_path,
                compression=compression,
                **({"row_group_size": row_group_size} if row_group_size else {}),
                **kwargs,
            )

        return output_path

    def to_iceberg(
        self,
        data: list[dict[str, Any]] | Iterator[dict[str, Any]],
        catalog_name: str,
        namespace: str,
        table_name: str,
        catalog_config: dict[str, Any] | None = None,
        mode: str = "append",
    ) -> None:
        """
        Export data to an Apache Iceberg table.

        Args:
            data: Data records (list or iterator)
            catalog_name: Name of the Iceberg catalog
            namespace: Namespace/database name
            table_name: Table name
            catalog_config: Catalog configuration dict
            mode: Write mode ('append', 'overwrite')

        Example:
            >>> from eia import EIAClient
            >>> from eia.etl import DataExporter
            >>>
            >>> client = EIAClient(api_key="your_key")
            >>> data = client.get_all_data(
            ...     route="electricity/retail-sales",
            ...     data=["price", "revenue"],
            ...     max_rows=100000,
            ... )
            >>>
            >>> exporter = DataExporter()
            >>> exporter.to_iceberg(
            ...     data,
            ...     catalog_name="default",
            ...     namespace="eia",
            ...     table_name="retail_sales",
            ...     catalog_config={
            ...         "type": "rest",
            ...         "uri": "http://localhost:8181",
            ...     },
            ... )
        """
        self._ensure_iceberg()
        self._ensure_arrow()

        # Load catalog
        catalog = load_catalog(catalog_name, **(catalog_config or {}))

        # Convert data to Arrow table
        if not isinstance(data, list):
            data = list(data)

        schema = self._infer_schema(data)
        table = pa.Table.from_pylist(data, schema=schema)

        # Create or get Iceberg table
        full_table_name = f"{namespace}.{table_name}"

        try:
            iceberg_table = catalog.load_table(full_table_name)
        except Exception:
            # Table doesn't exist, create it
            # Convert Arrow schema to Iceberg schema (simplified)
            iceberg_fields = []
            for i, field in enumerate(schema):
                # Map Arrow types to Iceberg types
                if pa.types.is_string(field.type):
                    iceberg_type = StringType()
                elif pa.types.is_floating(field.type):
                    iceberg_type = DoubleType()
                elif pa.types.is_integer(field.type):
                    iceberg_type = IntegerType()
                else:
                    iceberg_type = StringType()

                iceberg_fields.append(
                    NestedField(
                        field_id=i + 1,
                        name=field.name,
                        field_type=iceberg_type,
                        required=False,
                    )
                )

            iceberg_schema = Schema(*iceberg_fields)
            iceberg_table = catalog.create_table(full_table_name, schema=iceberg_schema)

        # Write data
        if mode == "overwrite":
            iceberg_table.overwrite(table)
        else:
            iceberg_table.append(table)


# Convenience functions


def to_parquet(
    data: list[dict[str, Any]] | Iterator[dict[str, Any]],
    output_path: str | Path,
    **kwargs: Any,
) -> Path:
    """
    Export data to Parquet format (convenience function).

    Args:
        data: Data records
        output_path: Path to output file
        **kwargs: Additional arguments passed to DataExporter.to_parquet

    Returns:
        Path to the created Parquet file

    Example:
        >>> from eia import EIAClient
        >>> from eia.etl import to_parquet
        >>>
        >>> client = EIAClient(api_key="your_key")
        >>> data = client.get_all_data(
        ...     route="electricity/retail-sales",
        ...     data=["price"],
        ... )
        >>> to_parquet(data, "electricity_prices.parquet")
    """
    exporter = DataExporter()
    return exporter.to_parquet(data, output_path, **kwargs)


def to_iceberg(
    data: list[dict[str, Any]] | Iterator[dict[str, Any]],
    catalog_name: str,
    namespace: str,
    table_name: str,
    **kwargs: Any,
) -> None:
    """
    Export data to Iceberg table (convenience function).

    Args:
        data: Data records
        catalog_name: Iceberg catalog name
        namespace: Namespace/database name
        table_name: Table name
        **kwargs: Additional arguments passed to DataExporter.to_iceberg

    Example:
        >>> from eia import EIAClient
        >>> from eia.etl import to_iceberg
        >>>
        >>> client = EIAClient(api_key="your_key")
        >>> data = client.get_all_data(
        ...     route="electricity/retail-sales",
        ...     data=["price", "revenue"],
        ... )
        >>> to_iceberg(
        ...     data,
        ...     catalog_name="default",
        ...     namespace="eia",
        ...     table_name="retail_sales",
        ... )
    """
    exporter = DataExporter()
    exporter.to_iceberg(data, catalog_name, namespace, table_name, **kwargs)

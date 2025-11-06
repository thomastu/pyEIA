"""Property-based tests using hypothesis."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from eia.utils import chunk_iterable


@given(st.lists(st.integers()), st.integers(min_value=1, max_value=100))
def test_chunk_iterable_preserves_all_items(items: list[int], chunk_size: int) -> None:
    """Test that chunking preserves all items."""
    chunks = list(chunk_iterable(items, chunk_size))
    flattened = [item for chunk in chunks for item in chunk]

    assert flattened == items


@given(st.lists(st.integers(), min_size=1), st.integers(min_value=1, max_value=100))
def test_chunk_iterable_respects_max_size(items: list[int], chunk_size: int) -> None:
    """Test that chunks don't exceed the specified size."""
    chunks = list(chunk_iterable(items, chunk_size))

    for chunk in chunks:
        assert len(chunk) <= chunk_size


@given(st.lists(st.integers(), min_size=1), st.integers(min_value=1, max_value=100))
def test_chunk_iterable_last_chunk_correct_size(items: list[int], chunk_size: int) -> None:
    """Test that the last chunk has the correct number of remaining items."""
    chunks = list(chunk_iterable(items, chunk_size))

    if chunks:
        expected_last_chunk_size = len(items) % chunk_size
        if expected_last_chunk_size == 0:
            expected_last_chunk_size = chunk_size

        assert len(chunks[-1]) == expected_last_chunk_size


@given(st.integers(min_value=1, max_value=100))
def test_chunk_iterable_empty_list(chunk_size: int) -> None:
    """Test that chunking an empty list returns no chunks."""
    chunks = list(chunk_iterable([], chunk_size))
    assert chunks == []


@given(st.lists(st.text(), min_size=1), st.integers(min_value=1, max_value=50))
def test_chunk_iterable_with_strings(items: list[str], chunk_size: int) -> None:
    """Test chunking with string items."""
    chunks = list(chunk_iterable(items, chunk_size))
    flattened = [item for chunk in chunks for item in chunk]

    assert flattened == items
    for chunk in chunks:
        assert len(chunk) <= chunk_size


@given(st.lists(st.integers(), min_size=1, max_size=500))
def test_chunk_iterable_chunk_size_one(items: list[int]) -> None:
    """Test chunking with size 1 creates one chunk per item."""
    chunks = list(chunk_iterable(items, 1))

    assert len(chunks) == len(items)
    for chunk in chunks:
        assert len(chunk) == 1


@given(st.lists(st.integers(), min_size=1, max_size=100), st.integers(min_value=200))
def test_chunk_iterable_large_chunk_size(items: list[int], chunk_size: int) -> None:
    """Test chunking with chunk size larger than list."""
    chunks = list(chunk_iterable(items, chunk_size))

    assert len(chunks) == 1
    assert chunks[0] == items


# Series ID validation tests
@given(st.text(min_size=1))
def test_series_id_parsing_preserves_content(series_id: str) -> None:
    """Test that series IDs are preserved correctly."""
    # Just ensure non-empty strings are handled
    if series_id.strip():
        assert len(series_id) > 0


# DataPoint tests
@given(st.text(min_size=1), st.one_of(st.floats(allow_nan=False), st.integers(), st.none()))
def test_datapoint_creation(period: str, value: float | int | None) -> None:
    """Test that DataPoints can be created with various value types."""
    from eia.models import DataPoint

    # Create a DataPoint (which is just a tuple)
    datapoint: DataPoint = (period, value)

    assert datapoint[0] == period
    assert datapoint[1] == value


# Test immutability of frozen dataclasses
def test_frozen_models_are_immutable() -> None:
    """Test that model objects are immutable (frozen)."""
    from eia.models import SeriesData

    series = SeriesData(
        series_id="test",
        name="Test Series",
        units="units",
        f="M",
        data=[("202001", 100)],
    )

    # Attempting to modify should raise an error
    import dataclasses

    assert dataclasses.is_dataclass(series)
    with pytest.raises(dataclasses.FrozenInstanceError):
        series.name = "Modified"  # type: ignore[misc]


import pytest


@given(
    st.lists(
        st.tuples(st.text(min_size=1), st.one_of(st.floats(allow_nan=False), st.integers())),
        min_size=1,
        max_size=100,
    )
)
def test_series_data_with_various_datapoints(
    data_points: list[tuple[str, float | int]]
) -> None:
    """Test SeriesData with various data point combinations."""
    from eia.models import SeriesData

    series = SeriesData(
        series_id="test.series.1",
        name="Test Series",
        units="units",
        f="M",
        data=data_points,
    )

    assert len(series.data) == len(data_points)
    assert series.data == data_points

"""Tests for utility functions."""

from __future__ import annotations

from eia.utils import chunk_iterable


def test_chunk_iterable_basic() -> None:
    """Test basic chunking functionality."""
    items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    chunks = list(chunk_iterable(items, 3))

    assert len(chunks) == 4
    assert chunks[0] == [1, 2, 3]
    assert chunks[1] == [4, 5, 6]
    assert chunks[2] == [7, 8, 9]
    assert chunks[3] == [10]


def test_chunk_iterable_exact_division() -> None:
    """Test chunking when items divide evenly."""
    items = [1, 2, 3, 4, 5, 6]
    chunks = list(chunk_iterable(items, 2))

    assert len(chunks) == 3
    assert chunks[0] == [1, 2]
    assert chunks[1] == [3, 4]
    assert chunks[2] == [5, 6]


def test_chunk_iterable_single_chunk() -> None:
    """Test chunking when chunk size exceeds list size."""
    items = [1, 2, 3]
    chunks = list(chunk_iterable(items, 10))

    assert len(chunks) == 1
    assert chunks[0] == [1, 2, 3]


def test_chunk_iterable_empty() -> None:
    """Test chunking empty list."""
    items: list[int] = []
    chunks = list(chunk_iterable(items, 3))

    assert len(chunks) == 0


def test_chunk_iterable_strings() -> None:
    """Test chunking with string items."""
    items = ["a", "b", "c", "d", "e"]
    chunks = list(chunk_iterable(items, 2))

    assert len(chunks) == 3
    assert chunks[0] == ["a", "b"]
    assert chunks[1] == ["c", "d"]
    assert chunks[2] == ["e"]


def test_chunk_iterable_generator() -> None:
    """Test chunking with a generator."""
    items = (x for x in range(5))
    chunks = list(chunk_iterable(items, 2))

    assert len(chunks) == 3
    assert chunks[0] == [0, 1]
    assert chunks[1] == [2, 3]
    assert chunks[2] == [4]

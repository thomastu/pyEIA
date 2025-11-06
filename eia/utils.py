"""Utility functions for the EIA client."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import TypeVar

T = TypeVar("T")


def chunk_iterable(iterable: Iterable[T], chunk_size: int) -> Iterator[list[T]]:
    """Split an iterable into chunks of a given size.

    Args:
        iterable: The iterable to chunk
        chunk_size: Maximum size of each chunk

    Yields:
        Lists of items with at most chunk_size elements

    Examples:
        >>> list(chunk_iterable([1, 2, 3, 4, 5], 2))
        [[1, 2], [3, 4], [5]]
    """
    chunk: list[T] = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) == chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk

"""Read log files lazily with generators and iterators."""

from collections.abc import Iterable, Iterator
from itertools import chain, islice
from pathlib import Path


def read_lines(path: str | Path) -> Iterator[str]:
    """Yield the lines of a file one at a time.

    Only one line is held in memory at a time, so even huge files can be
    read without loading the whole file.
    """
    with open(path, encoding="utf-8") as file:
        for line in file:
            yield line


def read_files(paths: list[str | Path]) -> Iterator[str]:
    """Yield the lines of several files, one file after another."""
    generators = [read_lines(path) for path in paths]
    return chain(*generators)


def paginate(items: Iterable, page: int, page_size: int) -> Iterator:
    """Return the items on the given page (pages start at 1)."""
    start = (page - 1) * page_size
    stop = start + page_size
    return islice(items, start, stop)


class BatchIterator:
    """Hand out items in lists (batches) of batch_size.

    Example:
        list(BatchIterator([1, 2, 3, 4, 5], 2)) == [[1, 2], [3, 4], [5]]
    """

    def __init__(self, items: Iterable, batch_size: int) -> None:
        """Store the items to batch and the size of each batch."""
        self.items = iter(items)
        self.batch_size = batch_size

    def __iter__(self) -> "BatchIterator":
        """Return the iterator itself, so it can be used in a for loop."""
        return self

    def __next__(self) -> list:
        """Return the next batch, or stop when there are no items left."""
        batch = list(islice(self.items, self.batch_size))
        if not batch:
            raise StopIteration
        return batch
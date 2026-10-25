"""Tests for the generator and iterator helpers."""

import sys
from pathlib import Path
from types import GeneratorType

from log_analyzer.reader import BatchIterator, paginate, read_files, read_lines

LOGS_DIR = Path(__file__).parent.parent / "logs"


def test_read_lines_is_a_generator(tmp_path):
    path = tmp_path / "small.log"
    path.write_text("first\nsecond\n", encoding="utf-8")

    assert isinstance(read_lines(path), GeneratorType)


def test_read_lines_yields_one_line_at_a_time(tmp_path):
    path = tmp_path / "small.log"
    path.write_text("first\nsecond\n", encoding="utf-8")

    lines = read_lines(path)

    assert next(lines) == "first\n"
    assert next(lines) == "second\n"


def test_read_lines_reads_every_line_of_a_sample_log():
    lines = read_lines(LOGS_DIR / "access_1.log")

    assert sum(1 for _ in lines) == 1200


def test_generator_uses_less_memory_than_a_list():
    path = LOGS_DIR / "access_1.log"

    generator_size = sys.getsizeof(read_lines(path))
    list_size = sys.getsizeof(list(read_lines(path)))

    assert generator_size < list_size


def test_generator_size_does_not_grow_with_file_size(tmp_path):
    small = tmp_path / "small.log"
    small.write_text("line\n", encoding="utf-8")
    big = LOGS_DIR / "access_1.log"

    assert sys.getsizeof(read_lines(small)) == sys.getsizeof(read_lines(big))


def test_read_files_chains_files_in_order(tmp_path):
    first = tmp_path / "first.log"
    second = tmp_path / "second.log"
    first.write_text("a\nb\n", encoding="utf-8")
    second.write_text("c\n", encoding="utf-8")

    assert list(read_files([first, second])) == ["a\n", "b\n", "c\n"]


def test_read_files_combines_both_sample_logs():
    paths = [LOGS_DIR / "access_1.log", LOGS_DIR / "access_2.log"]

    assert sum(1 for _ in read_files(paths)) == 2400


def test_paginate_returns_requested_page():
    items = range(1, 11)

    assert list(paginate(items, page=1, page_size=3)) == [1, 2, 3]
    assert list(paginate(items, page=2, page_size=3)) == [4, 5, 6]
    assert list(paginate(items, page=4, page_size=3)) == [10]


def test_paginate_past_the_end_is_empty():
    assert list(paginate(range(5), page=3, page_size=5)) == []


def test_batch_iterator_splits_items_into_batches():
    batches = BatchIterator([1, 2, 3, 4, 5], batch_size=2)

    assert list(batches) == [[1, 2], [3, 4], [5]]


def test_batch_iterator_with_no_items_gives_no_batches():
    assert list(BatchIterator([], batch_size=2)) == []


def test_batch_iterator_is_its_own_iterator():
    batches = BatchIterator([1, 2], batch_size=2)

    assert iter(batches) is batches
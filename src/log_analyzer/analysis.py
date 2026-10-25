"""Functional pipeline: transform, filter, aggregate and group log entries.

Every function takes entries in and gives entries (or a result) out, so the
steps can be chained together like a pipeline:

    lines -> parse_entries -> filter_errors -> count_by_status
"""

from collections.abc import Iterable, Iterator
from datetime import datetime
from functools import partial, reduce
from itertools import groupby, takewhile

from log_analyzer.parser import parse_line
from log_analyzer.patterns import mask_emails

# --- Transforming with map -------------------------------------------------


def parse_entries(lines: Iterable[str]) -> Iterator[dict]:
    """Turn lines into entries, skipping lines that are not valid log lines."""
    entries = map(parse_line, lines)
    return filter(None, entries)


def mask_entry(entry: dict) -> dict:
    """Return a copy of the entry with email addresses hidden in its URL."""
    masked = dict(entry)
    masked["url"] = mask_emails(entry["url"])
    return masked


def mask_urls(entries: Iterable[dict]) -> Iterator[dict]:
    """Hide email addresses in the URL of every entry."""
    return map(mask_entry, entries)


# --- Filtering with filter and partial -------------------------------------


def has_status(status: int, entry: dict) -> bool:
    """Return True if the entry has the given status code."""
    return entry["status"] == status


def filter_by_status(entries: Iterable[dict], status: int) -> Iterator[dict]:
    """Keep only the entries with the given status code."""
    return filter(partial(has_status, status), entries)


def is_error(entry: dict) -> bool:
    """Return True for client errors (4xx) and server errors (5xx)."""
    return entry["status"] >= 400


def filter_errors(entries: Iterable[dict]) -> Iterator[dict]:
    """Keep only the error entries."""
    return filter(is_error, entries)


# --- Time ranges with takewhile --------------------------------------------


def is_at_or_after(start: datetime, entry: dict) -> bool:
    """Return True if the entry happened at or after start."""
    return entry["timestamp"] >= start


def is_before(end: datetime, entry: dict) -> bool:
    """Return True if the entry happened before end."""
    return entry["timestamp"] < end


def entries_between(
    entries: Iterable[dict], start: datetime, end: datetime
) -> Iterator[dict]:
    """Keep entries from start (included) up to end (not included).

    Entries must be in time order, as they are in a log file. takewhile
    stops reading at the first entry that is too late, so the rest of the
    file is never read.
    """
    from_start = filter(partial(is_at_or_after, start), entries)
    return takewhile(partial(is_before, end), from_start)


# --- Aggregating with reduce -----------------------------------------------


def add_size(total: int, entry: dict) -> int:
    """Add the entry's size to the running total."""
    return total + entry["size"]


def total_bytes(entries: Iterable[dict]) -> int:
    """Return the total number of bytes sent for all entries."""
    return reduce(add_size, entries, 0)


def count_ip(counts: dict, entry: dict) -> dict:
    """Add one to the count for the entry's IP address."""
    ip = entry["ip"]
    counts[ip] = counts.get(ip, 0) + 1
    return counts


def count_by_ip(entries: Iterable[dict]) -> dict:
    """Return how many requests came from each IP address."""
    return reduce(count_ip, entries, {})


# --- Grouping with groupby -------------------------------------------------


def get_status(entry: dict) -> int:
    """Return the entry's status code (used as a grouping key)."""
    return entry["status"]


def get_hour(entry: dict) -> datetime:
    """Return the start of the hour the entry happened in."""
    return entry["timestamp"].replace(minute=0, second=0, microsecond=0)


def count_by_status(entries: Iterable[dict]) -> dict:
    """Return how many entries there are for each status code."""
    sorted_entries = sorted(entries, key=get_status)
    counts = {}
    for status, group in groupby(sorted_entries, key=get_status):
        counts[status] = sum(1 for _ in group)
    return counts


def count_by_hour(entries: Iterable[dict]) -> dict:
    """Return how many entries there are for each hour.

    Entries must be in time order, so entries from the same hour are
    already next to each other and no sorting is needed.
    """
    counts = {}
    for hour, group in groupby(entries, key=get_hour):
        counts[hour] = sum(1 for _ in group)
    return counts
"""Tests for the functional pipeline."""

from datetime import datetime, timezone
from functools import partial
from pathlib import Path

import pytest

from log_analyzer.analysis import (
    count_by_hour,
    count_by_ip,
    count_by_status,
    entries_between,
    filter_by_status,
    filter_errors,
    has_status,
    mask_urls,
    parse_entries,
    total_bytes,
)
from log_analyzer.reader import read_files

LOGS_DIR = Path(__file__).parent.parent / "logs"

SAMPLE_LINE = (
    '192.168.1.10 - - [01/Oct/2026:13:55:36 +0000] "GET /index.html HTTP/1.1" 200 2326'
)


def make_entry(status=200, ip="10.0.0.1", size=100, hour=10, minute=0, url="/"):
    """Build a log entry dictionary for tests."""
    return {
        "ip": ip,
        "timestamp": datetime(2026, 10, 1, hour, minute, tzinfo=timezone.utc),
        "method": "GET",
        "url": url,
        "protocol": "HTTP/1.1",
        "status": status,
        "size": size,
    }


def at(hour):
    """Return 1 October 2026 at the given hour, in UTC."""
    return datetime(2026, 10, 1, hour, tzinfo=timezone.utc)


def test_parse_entries_skips_invalid_lines():
    lines = [SAMPLE_LINE, "garbage", "", SAMPLE_LINE]

    entries = list(parse_entries(lines))

    assert len(entries) == 2
    assert entries[0]["status"] == 200


def test_parse_entries_is_lazy():
    entries = parse_entries([SAMPLE_LINE])

    assert not isinstance(entries, list)
    assert next(entries)["ip"] == "192.168.1.10"


def test_mask_urls_hides_emails_without_changing_original():
    original = make_entry(url="/subscribe?email=jane@example.com")

    masked = next(mask_urls([original]))

    assert masked["url"] == "/subscribe?email=[EMAIL]"
    assert original["url"] == "/subscribe?email=jane@example.com"


def test_partial_creates_a_specialized_filter():
    is_not_found = partial(has_status, 404)

    assert is_not_found(make_entry(status=404))
    assert not is_not_found(make_entry(status=200))


@pytest.mark.parametrize("status", [200, 404, 500])
def test_filter_by_status_keeps_only_that_status(status):
    entries = [make_entry(status=200), make_entry(status=404), make_entry(status=500)]

    result = list(filter_by_status(entries, status))

    assert len(result) == 1
    assert result[0]["status"] == status


def test_filter_errors_keeps_4xx_and_5xx():
    entries = [make_entry(status=s) for s in [200, 301, 404, 500]]

    statuses = [entry["status"] for entry in filter_errors(entries)]

    assert statuses == [404, 500]


def test_entries_between_includes_start_and_excludes_end():
    entries = [make_entry(hour=h) for h in [9, 10, 11, 12]]

    result = list(entries_between(entries, start=at(10), end=at(12)))

    assert [entry["timestamp"].hour for entry in result] == [10, 11]


def test_entries_between_stops_at_first_entry_after_end():
    # The last entry is out of order. takewhile has already stopped at 12:00,
    # so it never reaches the 10:30 entry.
    entries = [make_entry(hour=10), make_entry(hour=12), make_entry(hour=10, minute=30)]

    result = list(entries_between(entries, start=at(10), end=at(11)))

    assert len(result) == 1


def test_total_bytes_adds_all_sizes():
    entries = [make_entry(size=100), make_entry(size=250), make_entry(size=50)]

    assert total_bytes(entries) == 400


def test_total_bytes_of_no_entries_is_zero():
    assert total_bytes([]) == 0


def test_count_by_ip():
    entries = [
        make_entry(ip="1.1.1.1"),
        make_entry(ip="2.2.2.2"),
        make_entry(ip="1.1.1.1"),
    ]

    assert count_by_ip(entries) == {"1.1.1.1": 2, "2.2.2.2": 1}


def test_count_by_status_groups_unsorted_entries():
    entries = [make_entry(status=s) for s in [404, 200, 404, 500, 200, 200]]

    assert count_by_status(entries) == {200: 3, 404: 2, 500: 1}


def test_count_by_hour():
    entries = [make_entry(hour=10), make_entry(hour=10, minute=30), make_entry(hour=11)]

    assert count_by_hour(entries) == {at(10): 2, at(11): 1}


def test_full_pipeline_on_sample_logs():
    paths = [LOGS_DIR / "access_1.log", LOGS_DIR / "access_2.log"]

    entries = list(parse_entries(read_files(paths)))
    errors = list(filter_errors(entries))

    assert len(entries) > 2300
    assert all(entry["status"] >= 400 for entry in errors)
    assert sum(count_by_status(entries).values()) == len(entries)
    assert sum(count_by_hour(entries).values()) == len(entries)
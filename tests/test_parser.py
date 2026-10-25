"""Tests for turning log lines into dictionaries."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from log_analyzer.parser import parse_line, parse_timestamp

LOGS_DIR = Path(__file__).parent.parent / "logs"

SAMPLE_LINE = (
    '192.168.1.10 - - [01/Oct/2026:13:55:36 +0000] "GET /index.html HTTP/1.1" 200 2326'
)


def test_parse_timestamp_returns_datetime():
    result = parse_timestamp("01/Oct/2026:13:55:36 +0000")

    assert result == datetime(2026, 10, 1, 13, 55, 36, tzinfo=timezone.utc)


def test_parse_line_returns_dictionary_with_converted_values():
    entry = parse_line(SAMPLE_LINE)

    assert entry == {
        "ip": "192.168.1.10",
        "timestamp": datetime(2026, 10, 1, 13, 55, 36, tzinfo=timezone.utc),
        "method": "GET",
        "url": "/index.html",
        "protocol": "HTTP/1.1",
        "status": 200,
        "size": 2326,
    }


def test_parse_line_turns_dash_size_into_zero():
    entry = parse_line(SAMPLE_LINE.replace("2326", "-"))

    assert entry["size"] == 0


def test_parse_line_handles_extra_whitespace_and_newline():
    messy_line = "  " + SAMPLE_LINE.replace(" 200 ", "   200 ") + "\n"

    assert parse_line(messy_line)["status"] == 200


@pytest.mark.parametrize(
    "line", ["this is not a log line", "", "\n", "ERROR corrupted entry"]
)
def test_parse_line_returns_none_for_invalid_lines(line):
    assert parse_line(line) is None


@pytest.mark.parametrize("filename", ["access_1.log", "access_2.log"])
def test_every_real_log_line_in_sample_files_is_parsed(filename):
    bad_lines = {"this is not a log line", "", "ERROR corrupted entry"}

    with open(LOGS_DIR / filename, encoding="utf-8") as file:
        for line in file:
            if line.strip() in bad_lines:
                assert parse_line(line) is None
            else:
                assert parse_line(line) is not None
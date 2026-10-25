"""Turn raw log lines into structured dictionaries."""

from datetime import datetime

from log_analyzer.patterns import LOG_PATTERN, clean_line

TIMESTAMP_FORMAT = "%d/%b/%Y:%H:%M:%S %z"


def parse_timestamp(text: str) -> datetime:
    """Convert a log timestamp such as '01/Oct/2026:13:55:36 +0000' to a datetime."""
    return datetime.strptime(text, TIMESTAMP_FORMAT)


def parse_line(line: str) -> dict | None:
    """Parse one log line into a dictionary.

    Returns None if the line does not match the log format, so broken
    lines can be skipped instead of crashing the program.
    """
    match = LOG_PATTERN.match(clean_line(line))
    if match is None:
        return None

    entry = match.groupdict()
    entry["timestamp"] = parse_timestamp(entry["timestamp"])
    entry["status"] = int(entry["status"])
    if entry["size"] == "-":
        entry["size"] = 0
    else:
        entry["size"] = int(entry["size"])
    return entry
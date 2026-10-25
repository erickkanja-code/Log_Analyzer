"""Analyze log files and turn the results into a text report."""

from collections.abc import Iterator
from pathlib import Path

from log_analyzer.analysis import (
    count_by_hour,
    count_by_ip,
    count_by_status,
    filter_errors,
    mask_urls,
    parse_entries,
    total_bytes,
)
from log_analyzer.decorators import log_call, timer
from log_analyzer.reader import paginate, read_files


def load_entries(paths: list[str | Path]) -> Iterator[dict]:
    """Build a fresh, lazy pipeline: read lines, parse them, mask emails."""
    return mask_urls(parse_entries(read_files(paths)))


@timer
@log_call
def analyze_logs(paths: list[str | Path]) -> dict:
    """Analyze the log files and return the results in a dictionary.

    Each statistic gets its own fresh pipeline from load_entries. A generator
    can only be read once, so the files are read again for each statistic.
    This keeps memory use low: entries are never all held in memory at once.
    """
    ip_counts = count_by_ip(load_entries(paths))
    top_ips = sorted(ip_counts, key=ip_counts.get, reverse=True)[:3]

    return {
        "total_requests": sum(1 for _ in load_entries(paths)),
        "total_bytes": total_bytes(load_entries(paths)),
        "status_counts": count_by_status(load_entries(paths)),
        "hourly_counts": count_by_hour(load_entries(paths)),
        "top_ips": [(ip, ip_counts[ip]) for ip in top_ips],
        "first_errors": list(
            paginate(filter_errors(load_entries(paths)), page=1, page_size=5)
        ),
    }


def format_report(results: dict) -> str:
    """Turn the analysis results into readable text."""
    lines = [
        "=== Log Analysis Report ===",
        f"Total requests: {results['total_requests']}",
        f"Total bytes sent: {results['total_bytes']}",
        "",
        "Requests by status code:",
    ]
    for status, count in results["status_counts"].items():
        lines.append(f"  {status}: {count}")

    lines.append("")
    lines.append("Requests by hour:")
    for hour, count in results["hourly_counts"].items():
        lines.append(f"  {hour.strftime('%Y-%m-%d %H:00')}: {count}")

    lines.append("")
    lines.append("Top 3 IP addresses:")
    for ip, count in results["top_ips"]:
        lines.append(f"  {ip}: {count}")

    lines.append("")
    lines.append("First 5 errors:")
    for entry in results["first_errors"]:
        time = entry["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"  {time} {entry['status']} {entry['method']} {entry['url']}")

    return "\n".join(lines)
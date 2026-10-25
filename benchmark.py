"""Compare speed and memory use: reading a log with a list vs a generator.

Usage:
    poetry run python benchmark.py
"""

import time
import tracemalloc
from pathlib import Path

from log_analyzer.analysis import parse_entries
from log_analyzer.parser import parse_line
from log_analyzer.reader import read_lines

LARGE_LOG = Path("logs/large.log")


def create_large_log() -> None:
    """Build a large log (60,000 lines) by repeating a sample log 50 times."""
    sample = Path("logs/access_1.log").read_text(encoding="utf-8")
    LARGE_LOG.write_text(sample * 50, encoding="utf-8")


def count_with_list(path: Path) -> int:
    """Count valid entries by loading every line and entry into lists first."""
    with open(path, encoding="utf-8") as file:
        lines = file.readlines()
    entries = [parse_line(line) for line in lines]
    return len([entry for entry in entries if entry is not None])


def count_with_generator(path: Path) -> int:
    """Count valid entries by streaming them one at a time."""
    return sum(1 for _ in parse_entries(read_lines(path)))


def measure_time(func, path: Path) -> float:
    """Return how many seconds func(path) takes."""
    start = time.perf_counter()
    func(path)
    return time.perf_counter() - start


def measure_peak_memory(func, path: Path) -> int:
    """Return the most memory (in bytes) used at any moment while func(path) runs."""
    tracemalloc.start()
    func(path)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak


def main() -> None:
    """Create the large log, measure both approaches and print a comparison."""
    create_large_log()
    print(f"Created {LARGE_LOG} with 60,000 lines\n")

    print(f"{'Approach':<12}{'Entries':>10}{'Time (s)':>12}{'Peak memory':>16}")
    for name, func in [("List", count_with_list), ("Generator", count_with_generator)]:
        entries = func(LARGE_LOG)
        seconds = measure_time(func, LARGE_LOG)
        peak_mb = measure_peak_memory(func, LARGE_LOG) / 1_000_000
        print(f"{name:<12}{entries:>10}{seconds:>12.2f}{peak_mb:>13.2f} MB")


if __name__ == "__main__":
    main()
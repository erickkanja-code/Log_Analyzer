"""Generate sample web server access logs in Apache Common Log Format.

Usage:
    poetry run python scripts/generate_logs.py
"""

import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

IPS = [
    "192.168.1.10",
    "192.168.1.11",
    "10.0.0.5",
    "10.0.0.7",
    "172.16.0.3",
    "203.0.113.42",
    "198.51.100.23",
]
METHODS = ["GET", "GET", "GET", "GET", "POST", "PUT", "DELETE"]
URLS = [
    "/",
    "/index.html",
    "/about",
    "/products",
    "/products/42",
    "/api/users",
    "/login",
    "/images/logo.png",
    "/subscribe?email=jane@example.com",
    "/subscribe?email=erick@example.com",
]
STATUSES = [200, 200, 200, 200, 200, 201, 301, 304, 404, 404, 500]
BAD_LINES = ["this is not a log line", "", "ERROR corrupted entry"]


def make_line(time: datetime) -> str:
    """Build one random log line for the given time."""
    ip = random.choice(IPS)
    timestamp = time.strftime("%d/%b/%Y:%H:%M:%S %z")
    method = random.choice(METHODS)
    url = random.choice(URLS)
    status = random.choice(STATUSES)
    size = random.randint(200, 5000)
    return f'{ip} - - [{timestamp}] "{method} {url} HTTP/1.1" {status} {size}'


def generate_file(path: Path, start: datetime, line_count: int) -> None:
    """Write a log file with line_count lines, starting at the given time."""
    time = start
    lines = []
    for _ in range(line_count):
        time += timedelta(seconds=random.randint(1, 60))
        if random.random() < 0.01:
            lines.append(random.choice(BAD_LINES))
        else:
            lines.append(make_line(time))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    """Generate the sample log files in the logs/ folder."""
    random.seed(42)
    Path("logs").mkdir(exist_ok=True)
    generate_file(
        Path("logs/access_1.log"), datetime(2026, 10, 1, tzinfo=timezone.utc), 1200
    )
    generate_file(
        Path("logs/access_2.log"), datetime(2026, 10, 2, tzinfo=timezone.utc), 1200
    )
    print("Generated logs/access_1.log and logs/access_2.log")


if __name__ == "__main__":
    main()
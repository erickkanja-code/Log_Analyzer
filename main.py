"""Command-line demo: analyze log files and print a report.

Usage:
    poetry run python main.py <log_file> [<log_file> ...]

Example:
    poetry run python main.py logs/access_1.log logs/access_2.log
"""

import sys

from log_analyzer.patterns import mask_emails
from log_analyzer.report import analyze_logs, format_report


def main() -> None:
    """Analyze the log files given on the command line and print a report."""
    paths = sys.argv[1:]
    if not paths:
        print("Usage: python main.py <log_file> [<log_file> ...]")
        sys.exit(1)

    try:
        results = analyze_logs(paths)
    except FileNotFoundError as error:
        print(f"Error: file not found: {error.filename}")
        sys.exit(1)

    print()
    print(format_report(results))
    print()
    print(f"mask_emails cache: {mask_emails.cache_info()}")


if __name__ == "__main__":
    main()
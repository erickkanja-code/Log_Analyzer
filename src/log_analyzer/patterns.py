"""Compiled regular expressions for parsing, validating and cleaning log data.

Patterns are compiled once, when this module is imported, and reused
everywhere. This is faster than rebuilding the same pattern for every line.
"""

import re

from log_analyzer.decorators import cache

# One line of an Apache/Nginx access log in Common Log Format, for example:
# 192.168.1.10 - - [01/Oct/2026:13:55:36 +0000] "GET /index.html HTTP/1.1" 200 2326
LOG_PATTERN = re.compile(
    r"(?P<ip>\S+) "  # client IP address, e.g. 192.168.1.10
    r"\S+ \S+ "  # identity and user, usually "- -"
    r"\[(?P<timestamp>[^\]]+)\] "  # time inside [ ], e.g. 01/Oct/2026:13:55:36 +0000
    r'"(?P<method>[A-Z]+) '  # HTTP method after the opening quote, e.g. GET
    r"(?P<url>\S+) "  # requested URL, e.g. /index.html
    r'(?P<protocol>[^"]+)" '  # protocol before the closing quote, e.g. HTTP/1.1
    r"(?P<status>\d{3}) "  # three-digit status code, e.g. 200
    r"(?P<size>\d+|-)"  # response size in bytes, or "-" when empty
)

# Four groups of 1 to 3 digits separated by dots, e.g. 192.168.1.10
IP_PATTERN = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")

# Name, @, domain, dot, ending, e.g. jane@example.com
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

# http:// or https://, a domain, then an optional path, e.g. https://example.com/about
URL_PATTERN = re.compile(r"https?://[\w.-]+(/\S*)?")

# One or more whitespace characters in a row (spaces, tabs, newlines)
WHITESPACE_PATTERN = re.compile(r"\s+")


def is_valid_ip(text: str) -> bool:
    """Return True if text is an IPv4 address with every part between 0 and 255."""
    if not IP_PATTERN.fullmatch(text):
        return False
    return all(int(part) <= 255 for part in text.split("."))


def is_valid_email(text: str) -> bool:
    """Return True if the whole text is an email address."""
    return EMAIL_PATTERN.fullmatch(text) is not None


def is_valid_url(text: str) -> bool:
    """Return True if the whole text is an http or https URL."""
    return URL_PATTERN.fullmatch(text) is not None


def has_email(text: str) -> bool:
    """Return True if an email address appears anywhere in text."""
    return EMAIL_PATTERN.search(text) is not None


def find_emails(text: str) -> list[str]:
    """Return every email address found in text."""
    return EMAIL_PATTERN.findall(text)

@cache
def mask_emails(text: str) -> str:
    """Replace every email address in text with [EMAIL] to protect privacy."""
    return EMAIL_PATTERN.sub("[EMAIL]", text)


def clean_line(line: str) -> str:
    """Collapse repeated whitespace into single spaces and trim both ends."""
    return WHITESPACE_PATTERN.sub(" ", line).strip()
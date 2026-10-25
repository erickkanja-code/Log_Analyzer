"""Tests for the regex patterns and helper functions."""

import pytest

from log_analyzer.patterns import (
    LOG_PATTERN,
    clean_line,
    find_emails,
    has_email,
    is_valid_email,
    is_valid_ip,
    is_valid_url,
    mask_emails,
)

SAMPLE_LINE = (
    '192.168.1.10 - - [01/Oct/2026:13:55:36 +0000] "GET /index.html HTTP/1.1" 200 2326'
)


def test_log_pattern_extracts_named_groups():
    match = LOG_PATTERN.match(SAMPLE_LINE)

    assert match is not None
    assert match.group("ip") == "192.168.1.10"
    assert match.group("timestamp") == "01/Oct/2026:13:55:36 +0000"
    assert match.group("method") == "GET"
    assert match.group("url") == "/index.html"
    assert match.group("protocol") == "HTTP/1.1"
    assert match.group("status") == "200"
    assert match.group("size") == "2326"


def test_log_pattern_accepts_dash_as_size():
    line = SAMPLE_LINE.replace("2326", "-")

    assert LOG_PATTERN.match(line).group("size") == "-"


@pytest.mark.parametrize(
    "line", ["this is not a log line", "", "ERROR corrupted entry"]
)
def test_log_pattern_rejects_invalid_lines(line):
    assert LOG_PATTERN.match(line) is None


@pytest.mark.parametrize(
    "ip", ["192.168.1.10", "10.0.0.5", "0.0.0.0", "255.255.255.255"]
)
def test_valid_ips(ip):
    assert is_valid_ip(ip)


@pytest.mark.parametrize(
    "ip", ["256.1.1.1", "1.2.3", "abc.def.ghi.jkl", "1.2.3.4.5", ""]
)
def test_invalid_ips(ip):
    assert not is_valid_ip(ip)


@pytest.mark.parametrize("email", ["jane@example.com", "erick.k+news@mail.co.uk"])
def test_valid_emails(email):
    assert is_valid_email(email)


@pytest.mark.parametrize("email", ["jane@", "@example.com", "jane example.com", ""])
def test_invalid_emails(email):
    assert not is_valid_email(email)


@pytest.mark.parametrize(
    "url", ["http://example.com", "https://example.com/about", "https://a.b/x?y=1"]
)
def test_valid_urls(url):
    assert is_valid_url(url)


@pytest.mark.parametrize("url", ["example.com", "ftp://example.com", "/index.html", ""])
def test_invalid_urls(url):
    assert not is_valid_url(url)


def test_has_email():
    assert has_email("/subscribe?email=jane@example.com")
    assert not has_email("/index.html")


def test_find_emails_returns_all_emails():
    text = "from jane@example.com to erick@example.com"

    assert find_emails(text) == ["jane@example.com", "erick@example.com"]


def test_mask_emails_hides_every_email():
    text = "/subscribe?email=jane@example.com"

    assert mask_emails(text) == "/subscribe?email=[EMAIL]"


def test_clean_line_collapses_whitespace_and_trims():
    assert clean_line("  GET   /index.html \t 200 \n") == "GET /index.html 200"
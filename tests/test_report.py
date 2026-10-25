"""Tests for the analysis results and the text report."""

from pathlib import Path

from log_analyzer.report import analyze_logs, format_report

LOGS_DIR = Path(__file__).parent.parent / "logs"
PATHS = [LOGS_DIR / "access_1.log", LOGS_DIR / "access_2.log"]


def test_analyze_logs_results_are_consistent():
    results = analyze_logs(PATHS)

    assert results["total_requests"] > 2300
    assert sum(results["status_counts"].values()) == results["total_requests"]
    assert sum(results["hourly_counts"].values()) == results["total_requests"]
    assert results["total_bytes"] > 0


def test_analyze_logs_top_ips_are_sorted_by_count():
    results = analyze_logs(PATHS)

    counts = [count for _, count in results["top_ips"]]
    assert len(counts) == 3
    assert counts == sorted(counts, reverse=True)


def test_analyze_logs_first_errors_are_errors_with_masked_emails():
    results = analyze_logs(PATHS)

    assert len(results["first_errors"]) == 5
    for entry in results["first_errors"]:
        assert entry["status"] >= 400
        assert "@" not in entry["url"]


def test_analyze_logs_prints_trace_and_time(capsys):
    analyze_logs(PATHS)

    output = capsys.readouterr().out
    assert "Calling analyze_logs" in output
    assert "analyze_logs took" in output


def test_format_report_contains_every_section():
    report = format_report(analyze_logs(PATHS))

    assert "Total requests:" in report
    assert "Requests by status code:" in report
    assert "Requests by hour:" in report
    assert "Top 3 IP addresses:" in report
    assert "First 5 errors:" in report
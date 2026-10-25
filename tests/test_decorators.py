"""Tests for the timer, log_call and cache decorators."""

from log_analyzer.decorators import cache, log_call, timer
from log_analyzer.patterns import mask_emails


def test_timer_returns_the_original_result_and_prints_time(capsys):
    @timer
    def add(a, b):
        return a + b

    result = add(2, 3)

    assert result == 5
    assert "add took" in capsys.readouterr().out


def test_timer_keeps_the_function_name():
    @timer
    def add(a, b):
        return a + b

    assert add.__name__ == "add"


def test_log_call_prints_call_and_finish(capsys):
    @log_call
    def greet(name, punctuation="!"):
        return f"Hello {name}{punctuation}"

    result = greet("Erick", punctuation="?")

    output = capsys.readouterr().out
    assert result == "Hello Erick?"
    assert "Calling greet with args=('Erick',) kwargs={'punctuation': '?'}" in output
    assert "Finished greet" in output


def test_cache_runs_the_function_only_once_per_argument():
    calls = []

    @cache
    def square(n):
        calls.append(n)
        return n * n

    assert square(4) == 16
    assert square(4) == 16
    assert square(5) == 25

    assert calls == [4, 5]
    assert square.cache_info().hits == 1


def test_chained_decorators_run_outer_first(capsys):
    @timer
    @log_call
    def double(n):
        return n * 2

    result = double(21)

    lines = capsys.readouterr().out.splitlines()
    assert result == 42
    assert lines[0].startswith("Calling double")
    assert lines[1] == "Finished double"
    assert lines[2].startswith("double took")


def test_mask_emails_is_cached():
    mask_emails.cache_clear()

    mask_emails("/subscribe?email=jane@example.com")
    mask_emails("/subscribe?email=jane@example.com")

    assert mask_emails.cache_info().hits == 1
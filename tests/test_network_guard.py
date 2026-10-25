"""
Tests for the network guard in tests/conftest.py.

Each case runs an inner pytest session (via pytester) with the real conftest,
so the guard is exercised exactly as the suite uses it.
"""

import os

import pytest

pytest_plugins = ["pytester"]

CONFTEST_PATH = os.path.join(os.path.dirname(__file__), "conftest.py")
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def guarded(pytester):
    """pytester with the project's conftest, project on sys.path, and a 'live' marker registered."""
    with open(CONFTEST_PATH, encoding="utf-8") as f:
        pytester.makeconftest(f.read())
    pytester.makeini("[pytest]\nmarkers =\n    live: live network tests\n")
    pytester.syspathinsert(PROJECT_ROOT)
    return pytester


def test_socket_connection_is_blocked(guarded):
    guarded.makepyfile("""
        import socket, pytest
        from conftest import NetworkAccessBlocked

        def test_inner():
            with pytest.raises(NetworkAccessBlocked):
                socket.create_connection(("example.com", 80), timeout=1)
    """)
    result = guarded.runpytest("-p", "no:cacheprovider")
    # The block raises, and the recorded attempt still fails the test at teardown
    result.assert_outcomes(passed=1, errors=1)
    result.stdout.fnmatch_lines(["*attempted network access*", "*DNS lookup of 'example.com'*"])


def test_swallowed_requests_call_still_fails_test(guarded):
    guarded.makepyfile("""
        import requests

        def test_inner():
            try:
                requests.get("https://eodhd.com/api/fundamentals/AAPL.US", timeout=1)
            except Exception:
                pass  # application code often swallows errors like this
    """)
    result = guarded.runpytest("-p", "no:cacheprovider")
    result.assert_outcomes(passed=1, errors=1)
    result.stdout.fnmatch_lines(["*attempted network access*", "*DNS lookup of 'eodhd.com'*"])


def test_swallowed_yfinance_call_still_fails_test(guarded):
    guarded.makepyfile("""
        from clients.yfinance_client import YFinanceClient

        def test_inner():
            # get_price swallows all exceptions and returns None
            assert YFinanceClient().get_price("AAPL.US") is None
    """)
    result = guarded.runpytest("-p", "no:cacheprovider")
    result.assert_outcomes(passed=1, errors=1)
    result.stdout.fnmatch_lines(["*attempted network access*", "*curl_cffi request (yfinance)*"])


def test_localhost_is_allowed(guarded):
    guarded.makepyfile("""
        import socket

        def test_inner():
            server = socket.socket()
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            client = socket.create_connection(server.getsockname(), timeout=1)
            client.close()
            server.close()
    """)
    result = guarded.runpytest("-p", "no:cacheprovider")
    result.assert_outcomes(passed=1)


def test_live_tests_are_not_guarded(guarded):
    guarded.makepyfile("""
        import socket, pytest
        from conftest import _block_network

        REAL_CONNECT = socket.socket.connect

        @pytest.mark.live
        def test_inner():
            assert socket.socket.connect is REAL_CONNECT
    """)
    result = guarded.runpytest("-p", "no:cacheprovider")
    result.assert_outcomes(passed=1)

"""
Shared pytest configuration.

Network guard: tests must not reach the network unless marked @pytest.mark.live.
Covers both HTTP stacks used by the app:
  - requests/urllib3 (EODHD client) via the socket module
  - curl_cffi (yfinance >= 0.2.5x, used for prices and FX) via Curl.perform

The application swallows many exceptions (e.g. yfinance failures return None),
so a blocked call alone could go unnoticed. Every attempt is therefore recorded
and the test fails at teardown if any were made.
"""

import os
import socket
import sys

import pytest

# Make project packages importable from every test without per-file sys.path hacks
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from curl_cffi import curl as _curl_cffi_curl
except ImportError:  # curl_cffi not installed: nothing to guard
    _curl_cffi_curl = None


_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}


class NetworkAccessBlocked(RuntimeError):
    """Raised when a non-live test tries to reach the network."""


def _is_local(address) -> bool:
    if isinstance(address, (str, bytes)):  # AF_UNIX path
        return True
    if isinstance(address, tuple) and address:
        return str(address[0]) in _LOCAL_HOSTS
    return False


@pytest.fixture(autouse=True)
def _block_network(request, monkeypatch):
    """Block and record network access for every test not marked live."""
    if request.node.get_closest_marker("live"):
        yield
        return

    attempts = []

    def _blocked(description):
        attempts.append(description)
        raise NetworkAccessBlocked(
            f"Network access blocked in test (mark it @pytest.mark.live if intended): {description}"
        )

    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex
    real_getaddrinfo = socket.getaddrinfo

    def guarded_connect(sock, address):
        if _is_local(address):
            return real_connect(sock, address)
        _blocked(f"socket connect to {address!r}")

    def guarded_connect_ex(sock, address):
        if _is_local(address):
            return real_connect_ex(sock, address)
        _blocked(f"socket connect to {address!r}")

    def guarded_getaddrinfo(host, *args, **kwargs):
        if host is None or str(host) in _LOCAL_HOSTS:
            return real_getaddrinfo(host, *args, **kwargs)
        _blocked(f"DNS lookup of {host!r}")

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect_ex)
    monkeypatch.setattr(socket, "getaddrinfo", guarded_getaddrinfo)

    if _curl_cffi_curl is not None:
        def guarded_perform(curl, *args, **kwargs):
            _blocked("curl_cffi request (yfinance)")

        monkeypatch.setattr(_curl_cffi_curl.Curl, "perform", guarded_perform)

    yield

    if attempts:
        unique = list(dict.fromkeys(attempts))
        pytest.fail(
            "Test attempted network access (mark it @pytest.mark.live or mock the client):\n  "
            + "\n  ".join(unique),
            pytrace=False,
        )

"""
Tests that API keys never reach log output.

The EODHD key is sent as the api_token query parameter, so request URLs in
urllib3 debug logs or exception messages would otherwise expose it.
"""

import logging
import os
import sys
from io import StringIO
from unittest.mock import Mock

import pytest
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from logging_utils import redact, SecretRedactingFilter, install_secret_redaction
from clients.eodhd_client import EODHDClient
import stock_data_analyser

FAKE_KEY = "FAKEKEY1234567890abcdef"
URL_WITH_KEY = f"https://eodhd.com/api/fundamentals/AAPL.US?api_token={FAKE_KEY}&fmt=json"


@pytest.fixture
def root_stream():
    """Isolated root logger with a single StringIO handler; restores state afterwards."""
    root = logging.getLogger()
    saved_handlers, saved_level = root.handlers[:], root.level
    urllib3_logger = logging.getLogger("urllib3")
    saved_urllib3_level = urllib3_logger.level

    stream = StringIO()
    root.handlers = [logging.StreamHandler(stream)]
    root.setLevel(logging.DEBUG)
    yield stream

    root.handlers = saved_handlers
    root.setLevel(saved_level)
    urllib3_logger.setLevel(saved_urllib3_level)


class TestRedact:
    def test_redacts_api_token_query_parameter(self):
        assert redact(URL_WITH_KEY) == "https://eodhd.com/api/fundamentals/AAPL.US?api_token=***&fmt=json"

    def test_redacts_literal_secret_anywhere(self):
        assert redact(f"key is {FAKE_KEY}!", [FAKE_KEY]) == "key is ***!"

    def test_ignores_empty_and_none_secrets(self):
        assert redact("nothing secret", ["", None]) == "nothing secret"

    def test_redacts_token_at_end_of_quoted_url(self):
        text = f"Max retries exceeded with url: '/api/div/AAPL.US?api_token={FAKE_KEY}'"
        assert FAKE_KEY not in redact(text)


class TestSecretRedactingFilter:
    def test_redacts_formatted_args(self, root_stream):
        install_secret_redaction([FAKE_KEY])
        logging.getLogger("some.module").info("calling %s", URL_WITH_KEY)

        output = root_stream.getvalue()
        assert FAKE_KEY not in output
        assert "api_token=***" in output

    def test_redacts_records_from_child_loggers(self, root_stream):
        install_secret_redaction([FAKE_KEY])
        logging.getLogger("urllib3.connectionpool").warning("GET %s", URL_WITH_KEY)

        assert FAKE_KEY not in root_stream.getvalue()

    def test_redacts_tracebacks(self, root_stream):
        root_stream_handler = logging.getLogger().handlers[0]
        root_stream_handler.addFilter(SecretRedactingFilter([FAKE_KEY]))

        try:
            raise RuntimeError(f"failed: {URL_WITH_KEY}")
        except RuntimeError:
            logging.getLogger("x").exception("request failed")

        output = root_stream.getvalue()
        assert "request failed" in output
        assert "RuntimeError" in output
        assert FAKE_KEY not in output


class TestConfigureLogging:
    def test_debug_mode_silences_urllib3_request_logging(self, root_stream):
        logging.getLogger().handlers = []  # let basicConfig install its handler
        stock_data_analyser.configure_logging(debug=True, secrets=[FAKE_KEY])

        assert logging.getLogger("urllib3").level == logging.WARNING
        assert not logging.getLogger("urllib3.connectionpool").isEnabledFor(logging.DEBUG)

    def test_installs_redaction_on_root_handlers(self, root_stream):
        logging.getLogger().handlers = []
        stock_data_analyser.configure_logging(debug=True, secrets=[FAKE_KEY])

        handlers = logging.getLogger().handlers
        assert handlers
        assert all(
            any(isinstance(f, SecretRedactingFilter) for f in h.filters) for h in handlers
        )


class TestEODHDClientErrorPath:
    def test_key_not_logged_when_request_fails(self, root_stream):
        """Retry exhaustion errors include the full URL; the key must still not be logged."""
        install_secret_redaction([FAKE_KEY])
        client = EODHDClient(FAKE_KEY, fx_client=Mock())
        client.session.get = Mock(side_effect=requests.exceptions.RetryError(
            f"Max retries exceeded with url: {URL_WITH_KEY}"
        ))

        with pytest.raises(SystemExit):
            client._make_eodhd_request("AAPL.US")

        output = root_stream.getvalue()
        assert "Unexpected error" in output or "Max retries" in output
        assert FAKE_KEY not in output

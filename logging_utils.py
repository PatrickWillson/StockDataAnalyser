"""
Logging helpers that keep secrets (API keys) out of log output.

The EODHD API key travels as the ``api_token`` query parameter, so any log
line or exception message containing a request URL would otherwise expose it.
"""

import logging
import re
from typing import Iterable

REDACTED = "***"

# Matches the value of an api_token query parameter (stops at &, whitespace or quotes)
_API_TOKEN_PATTERN = re.compile(r"(api_token=)[^&\s'\"]+")


def redact(text: str, secrets: Iterable[str] = ()) -> str:
    """
    Replace api_token values and literal secret values in text with ***.

    Args:
        text: Text to sanitise
        secrets: Literal secret values to remove wherever they appear

    Returns:
        Sanitised text
    """
    text = _API_TOKEN_PATTERN.sub(r"\1" + REDACTED, text)
    for secret in secrets:
        if secret:
            text = text.replace(secret, REDACTED)
    return text


class SecretRedactingFilter(logging.Filter):
    """
    Handler filter that redacts secrets from the message and traceback of every record.

    Attach it to handlers (not loggers): logger filters do not apply to records
    propagated from child loggers such as urllib3.
    """

    def __init__(self, secrets: Iterable[str] = ()):
        super().__init__()
        self._secrets = [s for s in secrets if s]

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(record.getMessage(), self._secrets)
        record.args = None

        if record.exc_info:
            # Pre-render the traceback so the formatter uses the redacted copy
            record.exc_text = redact(
                logging.Formatter().formatException(record.exc_info), self._secrets
            )
            record.exc_info = None
        elif record.exc_text:
            record.exc_text = redact(record.exc_text, self._secrets)

        return True


def install_secret_redaction(secrets: Iterable[str] = ()) -> None:
    """
    Attach a SecretRedactingFilter to every handler on the root logger.

    Args:
        secrets: Literal secret values (e.g. API keys) to redact
    """
    redacting_filter = SecretRedactingFilter(secrets)
    for handler in logging.getLogger().handlers:
        handler.addFilter(redacting_filter)

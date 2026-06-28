"""
Structured logging for the S.A.R.A.L. backend.

Emits one line per event in a parseable key=value format:

    ts=... level=INFO logger=saral.recommendation msg='ENGINE START ...'

Call :func:`setup_logging` once at process start (done in main.py) and use
:func:`get_logger` everywhere else.
"""

import logging
import os
import sys

_configured = False


class KeyValueFormatter(logging.Formatter):
    """Compact, grep-friendly structured formatter."""

    def format(self, record: logging.LogRecord) -> str:
        msg = record.getMessage().replace("\n", " ").strip()
        line = (
            f"ts={self.formatTime(record, '%Y-%m-%dT%H:%M:%S')} "
            f"level={record.levelname} "
            f"logger={record.name} "
            f"msg={msg!r}"
        )
        if record.exc_info:
            line += " | " + self.formatException(record.exc_info).replace("\n", " ")
        return line


def setup_logging(level: str | None = None) -> None:
    """Configure the 'saral' logger tree once (idempotent)."""
    global _configured
    if _configured:
        return
    resolved = (level or os.getenv("SARAL_LOG_LEVEL", "INFO")).upper()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(KeyValueFormatter())

    root = logging.getLogger("saral")
    root.handlers = [handler]
    root.setLevel(resolved)
    root.propagate = False
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger under the 'saral' tree."""
    setup_logging()
    return logging.getLogger(f"saral.{name}")

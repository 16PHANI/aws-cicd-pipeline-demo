"""Structured logging setup.

Plain logging.Formatter gives you free-text lines that are annoying to grep
and impossible to query once they land in CloudWatch or any log aggregator.
This formatter emits one JSON object per line instead, so every field is
queryable (request_id, path, status, duration_ms) without regexing strings.
"""

import json
import logging
import time
from typing import Any, Dict


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Anything attached via extra={...} gets merged in, so callers can
        # add request_id / path / status / duration_ms without subclassing.
        for key, value in record.__dict__.items():
            if key in (
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "taskName",
            ):
                continue
            payload[key] = value

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    # Gunicorn's own loggers should flow through the same JSON formatter
    # instead of printing their default plain-text access lines.
    for name in ("gunicorn.error", "gunicorn.access"):
        gl = logging.getLogger(name)
        gl.handlers = [handler]
        gl.propagate = False

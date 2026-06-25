from __future__ import annotations

import contextvars
import json
import logging
from typing import Any

from app.core.config import Settings

request_id_var = contextvars.ContextVar("request_id", default="-")
trace_id_var = contextvars.ContextVar("trace_id", default="-")
run_id_var = contextvars.ContextVar("run_id", default="-")
user_id_var = contextvars.ContextVar("user_id", default="-")


class CorrelationFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        record.trace_id = trace_id_var.get()
        record.run_id = run_id_var.get()
        record.user_id = user_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
            "trace_id": getattr(record, "trace_id", "-"),
            "run_id": getattr(record, "run_id", "-"),
            "user_id": getattr(record, "user_id", "-"),
        }
        for key in ("method", "path", "status_code", "duration_ms", "component", "span", "task"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        extra = getattr(record, "structured", None)
        if isinstance(extra, dict):
            payload.update(extra)
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def configure_logging(settings: Settings) -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = []

    handler = logging.StreamHandler()
    handler.addFilter(CorrelationFilter())
    use_json = settings.log_json or settings.api_env != "development"
    if use_json:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s "
                "request_id=%(request_id)s trace_id=%(trace_id)s run_id=%(run_id)s %(message)s"
            )
        )
    root_logger.addHandler(handler)


def log_structured(message: str, *, level: str = "INFO", logger_name: str = "app.observability", **fields: Any) -> None:
    logger = logging.getLogger(logger_name)
    log_fn = getattr(logger, level.lower(), logger.info)
    record_fields = {key: value for key, value in fields.items() if value is not None}
    extra = {"structured": record_fields}
    for key, value in record_fields.items():
        extra[key] = value
    log_fn(message, extra=extra)

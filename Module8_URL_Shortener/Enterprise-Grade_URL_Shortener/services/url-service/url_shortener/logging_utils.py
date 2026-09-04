import json
import logging


class JSONFormatter(logging.Formatter):
    """Renders each log record as a single-line JSON object for log-aggregator ingestion."""

    def format(self, record):
        """Build the JSON payload, including exception info and any structured `extra` fields, for one record."""
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        reserved = logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys()
        for key, value in record.__dict__.items():
            if key not in reserved and key not in payload:
                payload[key] = value

        return json.dumps(payload, default=str)

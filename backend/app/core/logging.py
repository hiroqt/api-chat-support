import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """
    Structured JSON log formatter for enterprise production observability.
    Compatible with Datadog, GCP Cloud Logging, BetterStack, and AWS CloudWatch.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include exception trace if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Attach custom contextual attributes if passed in extra
        for attr in ("request_id", "vapi_call_id", "tool_name", "status_code", "duration_ms", "client_ip"):
            if hasattr(record, attr):
                log_obj[attr] = getattr(record, attr)

        return json.dumps(log_obj)


def setup_logging(is_production: bool = True, log_level: int = logging.INFO):
    """Configure root logger with structured JSON formatting for production or readable formatting for dev."""
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    if is_production:
        stream_handler.setFormatter(JSONFormatter())
    else:
        stream_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )

    root_logger.addHandler(stream_handler)
    root_logger.setLevel(log_level)

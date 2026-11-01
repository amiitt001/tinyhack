import logging
import sys


class RequestIdFilter(logging.Filter):
    """Provide a fallback so service-layer records without request context log cleanly."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


def configure_logging() -> None:
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.addFilter(RequestIdFilter())
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s %(message)s"
            )
        )
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.INFO)
    else:
        for handler in root_logger.handlers:
            handler.addFilter(RequestIdFilter())

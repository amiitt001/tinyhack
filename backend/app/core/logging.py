import logging
import sys


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s %(message)s",
            defaults={"request_id": "-"},
        )
    )
    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler],
    )

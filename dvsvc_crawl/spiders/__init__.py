import logging
import os
from datetime import datetime

__SPIDERS_LOGGER = None
__SPIDERS_LOGGER_FILENAME = (
    f"dvsvc-spiders-{datetime.now().strftime('%Y-%m-%dT%H:%M')}.log"
)


def get_spiders_logger() -> logging.Logger:
    global __SPIDERS_LOGGER

    if not os.path.exists("logs"):
        os.makedirs("logs")

    if __SPIDERS_LOGGER:
        return __SPIDERS_LOGGER

    fh = logging.FileHandler(os.path.join("logs", __SPIDERS_LOGGER_FILENAME))
    fh.setLevel(logging.INFO)
    fh.setFormatter(
        logging.Formatter("%(name)s - %(asctime)s - %(levelname)s - %(message)s")
    )

    __SPIDERS_LOGGER = logging.getLogger("dvsvc-spiders")
    __SPIDERS_LOGGER.addHandler(fh)

    return __SPIDERS_LOGGER

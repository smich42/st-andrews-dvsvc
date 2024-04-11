import logging
import os

__SPIDERS_LOGGER = None


def get_spiders_logger() -> logging.Logger:
    global __SPIDERS_LOGGER

    if not os.path.exists("logs"):
        os.makedirs("logs")

    if __SPIDERS_LOGGER:
        return __SPIDERS_LOGGER

    fh = logging.FileHandler("logs/dvsvc-spiders.log")
    fh.setLevel(logging.INFO)
    fh.setFormatter(
        logging.Formatter("%(name)s - %(asctime)s - %(levelname)s - %(message)s")
    )

    __SPIDERS_LOGGER = logging.getLogger("dvsvc-spiders")
    __SPIDERS_LOGGER.addHandler(fh)

    return __SPIDERS_LOGGER

import logging
import os

_SPIDERS_LOGGER = None


def get_spiders_logger() -> logging.Logger:
    global _SPIDERS_LOGGER

    if not os.path.exists("logs"):
        os.makedirs("logs")

    if _SPIDERS_LOGGER:
        return _SPIDERS_LOGGER

    fh = logging.FileHandler("logs/dvsvc-spiders.log")
    fh.setLevel(logging.INFO)
    fh.setFormatter(
        logging.Formatter("%(name)s - %(asctime)s - %(levelname)s - %(message)s")
    )

    _SPIDERS_LOGGER = logging.getLogger("dvsvc-spiders")
    _SPIDERS_LOGGER.addHandler(fh)

    return _SPIDERS_LOGGER

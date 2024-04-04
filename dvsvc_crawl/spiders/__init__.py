# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.

import logging

_SPIDERS_LOGGER = None


def get_spiders_logger() -> logging.Logger:
    global _SPIDERS_LOGGER

    if _SPIDERS_LOGGER:
        return _SPIDERS_LOGGER

    fh = logging.FileHandler("dvsvc_crawl.log")
    fh.setLevel(logging.INFO)
    fh.setFormatter(
        logging.Formatter("%(name)s - %(asctime)s - %(levelname)s - %(message)s")
    )

    _SPIDERS_LOGGER = logging.getLogger("dvsvc-spiders")
    _SPIDERS_LOGGER.addHandler(fh)

    return _SPIDERS_LOGGER

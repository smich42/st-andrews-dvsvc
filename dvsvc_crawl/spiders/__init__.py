# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.

import logging

_SPIDER_LOGGER = None


def get_dvsvc_logger() -> logging.Logger:
    global _SPIDER_LOGGER

    if _SPIDER_LOGGER:
        return _SPIDER_LOGGER

    fh = logging.FileHandler("dvsvc_crawl.log")
    fh.setLevel(logging.INFO)
    fh.setFormatter(
        logging.Formatter("%(name)s - %(asctime)s - %(levelname)s - %(message)s")
    )

    _SPIDER_LOGGER = logging.getLogger("dvsvc-spiders")
    _SPIDER_LOGGER.addHandler(fh)

    return _SPIDER_LOGGER

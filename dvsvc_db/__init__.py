import logging
import os

POSTGRES_DB = os.environ["POSTGRES_DB"]
POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
DB_HOST = os.environ["DB_HOST"]

__DB_LOGGER = None


def get_db_logger() -> logging.Logger:
    global __DB_LOGGER

    if not os.path.exists("logs"):
        os.makedirs("logs")

    if __DB_LOGGER:
        return __DB_LOGGER

    fh = logging.FileHandler("logs/dvsvc-db.log")
    fh.setLevel(logging.INFO)
    fh.setFormatter(
        logging.Formatter("%(name)s - %(asctime)s - %(levelname)s - %(message)s")
    )

    __DB_LOGGER = logging.getLogger("dvsvc-db")
    __DB_LOGGER.addHandler(fh)

    return __DB_LOGGER

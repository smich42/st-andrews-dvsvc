import psycopg2

from dvsvc_db import (
    DB_HOST,
    POSTGRES_DB,
    POSTGRES_PASSWORD,
    POSTGRES_USER,
    get_db_logger,
)

LOGGER = get_db_logger()


def connect(
    host=DB_HOST, database=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD
) -> psycopg2.extensions.connection:
    LOGGER.info("Connecting to PostgreSQL database with: %s", locals())
    try:
        with psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
        ) as conn:
            LOGGER.info("Connected to PostgreSQL database")
            return conn
    except psycopg2.DatabaseError as error:
        LOGGER.error("Failed to connect to PostgreSQL database: %s", error)

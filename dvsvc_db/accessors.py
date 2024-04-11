from datetime import datetime
import psycopg2

from dvsvc_db import get_db_logger
from heuristics.scorers import Score

LOGGER = get_db_logger()


def insert_crawl_item(
    conn: psycopg2.extensions.connection,
    link: str,
    pscore: Score | None,
    lscore: Score | None,
    time_queued: datetime | None,
    time_crawled: datetime | None,
    batch_id: int | None = None,
) -> int:
    with conn.cursor() as cursor:
        cursor.execute(
            "insert into crawl_item (link, pscore, lscore, time_queued, time_crawled, batch_id) values (%s, %s, %s, %s, %s, %s) returning id",
            (
                link,
                pscore.value if pscore else None,
                lscore.value if lscore else None,
                time_queued.isoformat() if time_queued else None,
                time_crawled.isoformat() if time_crawled else None,
                batch_id,
            ),
        )
        item_id = cursor.fetchone()[0]

        if pscore and pscore.matched_predicates:
            for tag in pscore.matched_predicates:
                cursor.execute(
                    "insert into crawl_item_tag (item_id, tag) values (%s, %s)",
                    (item_id, tag.__str__()),
                )

        conn.commit()

    LOGGER.info(
        "Attempted to insert crawl_item [time_crawled=%s, id=%s]", time_crawled, item_id
    )

    return item_id


def insert_crawl_item_batch(
    conn: psycopg2.extensions.connection,
    time_batched: datetime | None,
    links: tuple[str],
    pscores: tuple[Score | None],
    lscores: tuple[Score | None],
    times_queued: tuple[datetime | None],
    times_crawled: tuple[datetime | None],
) -> int:
    with conn.cursor() as cursor:
        cursor.execute(
            "insert into crawl_item_batch (time_batched) values (%s) returning id",
            (time_batched.isoformat() if time_batched else None,),
        )
        batch_id = cursor.fetchone()[0]
        conn.commit()

    LOGGER.info(
        "Attempted to insert crawl_item_batch [id=%s, size=%s]", batch_id, len(links)
    )

    for link, pscore, lscore, time_queued, time_crawled in zip(
        links, pscores, lscores, times_queued, times_crawled
    ):
        insert_crawl_item(
            conn,
            link,
            pscore,
            lscore,
            time_queued,
            time_crawled,
            batch_id,
        )

    return batch_id


def insert_crawl_item_tag(
    conn: psycopg2.extensions.connection,
    item_id: int,
    tag: str,
):
    with conn.cursor() as cursor:
        cursor.execute(
            "insert into crawl_item_tag (item_id, tag) values (%s, %s)",
            (item_id, tag),
        )
        conn.commit()

    LOGGER.info("Attempted to insert crawl_item_tag [item_id=%s, tag=%s]", item_id, tag)

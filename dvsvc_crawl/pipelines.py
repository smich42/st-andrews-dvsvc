from datetime import datetime
from itemadapter.adapter import ItemAdapter
from dvsvc_crawl.items import DvsvcCrawlItem, DvsvcCrawlBatch
from dvsvc_crawl.spiders import get_spiders_logger
from dvsvc_db import connect, accessors


class DvsvcCrawlPipeline:
    def process_item(self, item, spider):
        if isinstance(item, DvsvcCrawlItem):
            item_id = accessors.insert_crawl_item(
                self.db_conn,
                item["link"],
                item["pscore"],
                item["lscore"],
                item["time_queued"],
                item["time_crawled"],
            )
            if item_id:
                self.db_conn.commit()

        elif isinstance(item, DvsvcCrawlBatch):
            links = [i["link"] for i in item["crawl_items"]]
            pscores = [i["pscore"] for i in item["crawl_items"]]
            lscores = [i["lscore"] for i in item["crawl_items"]]
            times_queued = [i["time_queued"] for i in item["crawl_items"]]
            times_crawled = [i["time_crawled"] for i in item["crawl_items"]]

            batch_id = accessors.insert_crawl_item_batch(
                self.db_conn,
                item["time_batched"],
                links,
                pscores,
                lscores,
                times_queued,
                times_crawled,
            )
            if batch_id:
                self.db_conn.commit()

        else:
            raise ValueError(f"Unknown item type: {item}, {type(item)}")

        return item

    def __init__(self):
        self.db_conn = connect.connect()

    def __del__(self):
        self.db_conn.close()

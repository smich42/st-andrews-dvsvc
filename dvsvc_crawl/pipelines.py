from itemadapter.adapter import ItemAdapter
from dvsvc_db import connect, accessors


class DvsvcCrawlPipeline:
    def process_item(self, item, spider):
        # logging.info("Pipeline: %s" % item["url"])
        return item

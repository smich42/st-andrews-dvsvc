from itemadapter.adapter import ItemAdapter


class DvsvcCrawlPipeline:
    def process_item(self, item, spider):
        # logging.info("Pipeline: %s" % item["url"])
        return item

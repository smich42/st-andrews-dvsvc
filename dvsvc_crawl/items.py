from scrapy import Item, Field


class DvsvcCrawlItem(Item):
    link = Field()
    pscore = Field()
    lscore = Field()
    time_queued = Field()
    time_crawled = Field()

    def __str__(self):
        return f"{self.__class__.__name__}({self['link']}, {self['pscore']})"


class DvsvcCrawlBatch(Item):
    crawl_items = Field()
    time_batched = Field()

    def __str__(self):
        return f"{self.__class__.__name__}({self['crawl_items']})"

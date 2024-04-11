from dvsvc_crawl.pipelines import DvsvcCrawlPipeline


BOT_NAME = "dvsvc_crawl"

SPIDER_MODULES = ["dvsvc_crawl.spiders"]
NEWSPIDER_MODULE = "dvsvc_crawl.spiders"

ROBOTSTXT_OBEY = False

CONCURRENT_REQUESTS = 50

DOWNLOAD_DELAY = 5

COOKIES_ENABLED = False

DOWNLOADER_MIDDLEWARES = {
    "dvsvc_crawl.middlewares.DvsvcBlacklistMiddleware": 100,
}

ITEM_PIPELINES = {
    DvsvcCrawlPipeline: 300,
}

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

DEPTH_PRIORITY = 1
SCHEDULER_DISK_QUEUE = "scrapy.squeues.PickleFifoDiskQueue"
SCHEDULER_MEMORY_QUEUE = "scrapy.squeues.FifoMemoryQueue"
SCHEDULER_PRIORITY_QUEUE = "scrapy.pqueues.ScrapyPriorityQueue"

REACTOR_THREADPOOL_MAXSIZE = 20

RETRY_ENABLED = False

DOWNLOAD_TIMEOUT = 15

REDIRECT_ENABLED = False

AJAXCRAWL_ENABLED = True

URLLENGTH_LIMIT = 2048

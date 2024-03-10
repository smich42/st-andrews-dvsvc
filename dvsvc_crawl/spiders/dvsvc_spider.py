import logging
from collections import deque
from scrapy import Request, signals
from scrapy.spiders.crawl import CrawlSpider
from scrapy.linkextractors import LinkExtractor
from heuristics import dvsvc_scorers
from dvsvc_crawl.items import CandidatePage

PAGE_SCORE_TO_ITEMISE = 0.9

fh = logging.FileHandler("dvsvc_crawl.log")
fh.setLevel(logging.INFO)
fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
SPIDER_LOGGER = logging.getLogger("spider_logger")
SPIDER_LOGGER.addHandler(fh)

LINK_SCORER = dvsvc_scorers.get_link_scorer()
PAGE_SCORER = dvsvc_scorers.get_page_scorer()


def lscore_to_prio(lscore: float) -> int:
    if lscore > 0.8:
        return 3
    elif lscore > 0.6:
        return 2
    elif lscore > 0.4:
        return 1
    return 0


class DvsvcSpider(CrawlSpider):
    name = "dvsvc"
    start_urls = [
        "https://www.scotborders.gov.uk/directory/21/domestic_abuse_services",
        "https://womensaid.scot/"
    ]

    log_lscores = deque(maxlen=1_000)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.request_scheduled,
                                signal=signals.request_scheduled)
        return spider

    def start_requests(self):
        if self.crawler.stats:
            self.crawler.stats.set_value("total_requests", 1)

        for url in self.start_urls:
            yield Request(url, callback=self.parse)

    def parse(self, response):
        pscore = PAGE_SCORER.get_score(response.text)

        for link in LinkExtractor().extract_links(response):
            lscore = LINK_SCORER.get_score(link.url, pscore.value)

            request = Request(link.url,
                              callback=self.parse,
                              priority=lscore_to_prio(lscore.value))

            self.log_lscores.append(lscore.value)

            if self.crawler.stats:
                self.crawler.stats.inc_value("total_requests")

            yield request

        if pscore.value > PAGE_SCORE_TO_ITEMISE:
            page = CandidatePage()
            page["link"] = response.url
            page["pscore"] = pscore
            page["time_crawled"] = response.headers["Date"]

            yield page

    def request_scheduled(self, request, spider):
        if self.log_lscores and self.crawler.stats and \
                self.crawler.stats.get_value("total_requests") % self.log_lscores.maxlen == 0:

            lscore_avg = (sum(self.log_lscores) /
                          len(self.log_lscores)) if self.log_lscores else 1

            SPIDER_LOGGER.info(
                f"Avg 1_000 lscore values: {lscore_avg}")

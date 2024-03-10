import logging
from collections import deque
from scrapy import Request, signals
from scrapy.spiders.crawl import CrawlSpider
from scrapy.linkextractors import LinkExtractor
from ..heuristics import scorers
from ..items import CandidatePage

crawl_logger = logging.getLogger("crawl_logger")

fh = logging.FileHandler("dvsvc_crawl.log")
fh.setLevel(logging.INFO)
fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

crawl_logger.addHandler(fh)


def _url_score_to_priority(url_score: int) -> int:
    if url_score > 0.8:
        return 3
    elif url_score > 0.6:
        return 2
    elif url_score > 0.4:
        return 1
    return 0


class DvsvcSpider(CrawlSpider):
    __THRESHOLD_PAGE_SCORE_TO_ITEMISE = 0.9

    url_scores_window = deque(maxlen=1_000)

    name = "dvsvc"
    start_urls = [
        "https://www.scotborders.gov.uk/directory/21/domestic_abuse_services"
    ]

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.request_scheduled,
                                signal=signals.request_scheduled)
        return spider

    def start_requests(self):
        self.crawler.stats.set_value("total_requests", 1)

        for url in self.start_urls:
            yield Request(url, callback=self.parse)

    def parse(self, response):
        page_score, page_score_keywords = scorers.score_page(
            response.text)

        for link in LinkExtractor().extract_links(response):
            url_score, _ = scorers.score_url(
                link.url, page_score)

            request = Request(link.url,
                              callback=self.parse,
                              priority=_url_score_to_priority(url_score))

            self.url_scores_window.append(url_score)
            self.crawler.stats.inc_value("total_requests", 1)

            yield request

        if page_score > self.__THRESHOLD_PAGE_SCORE_TO_ITEMISE:
            page = CandidatePage()
            page["url"] = response.url
            page["relevance"] = page_score
            page["relevance_keyword_matches"] = page_score_keywords
            # page["page_text"] = page_text
            page["time_crawled"] = response.headers["Date"]

            yield page

    def request_scheduled(self, request, spider):
        if self.url_scores_window and self.crawler.stats.get_value("total_requests") % self.url_scores_window.maxlen == 0:

            avg_url_score = (sum(self.url_scores_window) /
                             len(self.url_scores_window)) if self.url_scores_window else 1

            crawl_logger.info(
                f"Avg 1_000 url score values: {avg_url_score}")
            # crawl_logger.info(
            #     f"Max 1_000 url score value: {max(self.url_scores_window)}")
            # crawl_logger.info(
            #     f"Min 1_000 url score value: {min(self.url_scores_window)}")

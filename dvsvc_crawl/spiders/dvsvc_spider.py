from datetime import datetime, timezone
from scrapy import Request, signals
from scrapy.spiders.crawl import CrawlSpider
from scrapy.linkextractors import LinkExtractor

from expiringdict import ExpiringDict
from collections import deque
import typing

from dvsvc_crawl import helpers
from dvsvc_crawl.spiders import get_spiders_logger
from dvsvc_crawl.items import DvsvcCrawlItem, DvsvcCrawlBatch
from heuristics import dvsvc_scorers
from heuristics.scorers import Score


LOGGER = get_spiders_logger()
LINK_SCORER = dvsvc_scorers.get_link_scorer()
PAGE_SCORER = dvsvc_scorers.get_page_scorer()

SUFFICIENT_PSCORE = 0.95  # A sufficient pscore to immediately itemise a page

NECESSARY_PSCORE = 0.80  # A necessary pscore to consider itemising as part of a page set for the same fld
NECESSARY_FLD_RATIO = 0.5  # The minimum ratio of good pscores to total pscores needed
NECESSARY_FLD_SAMPLES = 5  # The minimum number of samples needed

# Cache a visit count and good-pscore count for each domain
FLD_HISTORIES = ExpiringDict(
    max_len=100_000, max_age_seconds=60.0 * 60.0 * 24.0  # 24-hour expiry
)


def lscore_to_prio(lscore: float) -> int:
    return int(lscore * 10)


def get_response_time(response: Request) -> datetime:
    return datetime.strptime(
        response.headers["Date"].decode("utf-8"), "%a, %d %b %Y %H:%M:%S %Z"
    )


class FLDVisits:
    good_pages: list[DvsvcCrawlItem]  # We expect the size of this to not increase much
    total_pages: int

    def __init__(self):
        self.good_pages = []
        self.total_pages = 0

    def add_visit(
        self,
        link: str,
        pscore: Score,
        lscore: Score,
        time_queued: datetime,
        time_crawled: datetime,
    ):
        # No need to test URLs for having the same FLD
        self.total_pages += 1
        if pscore.value >= NECESSARY_PSCORE:
            self.good_pages.append(
                DvsvcCrawlItem(
                    link=link,
                    pscore=pscore,
                    lscore=lscore,
                    time_queued=time_queued,
                    time_crawled=time_crawled,
                )
            )

    def has_necessary_fld_ratio(self) -> float:
        return (
            self.total_pages >= NECESSARY_FLD_SAMPLES
            and len(self.good_pages) / self.total_pages >= NECESSARY_FLD_RATIO
        )


class DvsvcSpider(CrawlSpider):
    name = "dvsvc"
    start_urls = ["https://www.scotborders.gov.uk/directory/21/domestic_abuse_services"]

    # Health metric: track the last 1,000 lscores
    log_lscores = deque(maxlen=1_000)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        # Invoke request_scheduled every time a request is scheduled, e.g. to update health metrics.
        crawler.signals.connect(
            spider.request_scheduled, signal=signals.request_scheduled
        )
        return spider

    def start_requests(self):
        if self.crawler.stats:
            # Initialise to 1 to avoid division by 0
            self.crawler.stats.set_value("total_requests", 1)

        for url in self.start_urls:
            yield Request(
                url,
                callback=self.parse,
                priority=0,
                meta={"lscore": None, "time_queued": datetime.now(timezone.utc)},
            )

    def parse(self, response):
        pscore = PAGE_SCORER.score(response.text)

        links = list(LinkExtractor().extract_links(response))

        for link in links:
            # Yield new request
            lscore = LINK_SCORER.score(link.url, pscore.value)
            yield Request(
                link.url,
                callback=self.parse,
                priority=lscore_to_prio(lscore.value),
                meta={"lscore": lscore, "time_queued": datetime.now(timezone.utc)},
            )
            # Update health metrics
            self.log_lscores.append(lscore.value)
            if self.crawler.stats:
                self.crawler.stats.inc_value("total_requests")

        # Itemise immediately for exceptional pscore
        if pscore.value >= SUFFICIENT_PSCORE:
            yield DvsvcCrawlItem(
                link=response.url,
                pscore=pscore,
                lscore=response.meta["lscore"],
                time_queued=response.meta["time_queued"],
                time_crawled=get_response_time(response),
            )
            LOGGER.info(f"Itemised page: {response.url}")

        # Consider itemising set of pages of the same fld
        fld = helpers.get_fld(response.url)
        fld_history = typing.cast(
            FLDVisits, FLD_HISTORIES[fld] if fld in FLD_HISTORIES else FLDVisits()
        )
        fld_history.add_visit(
            response.url,
            pscore,
            response.meta["lscore"],
            response.meta["time_queued"],
            time_crawled=get_response_time(response),
        )

        if fld_history.has_necessary_fld_ratio():
            yield DvsvcCrawlBatch(
                crawl_items=fld_history.good_pages,
                time_batched=get_response_time(response),
            )
            FLD_HISTORIES.pop(fld)
            LOGGER.info(f"Itemised page set for FLD: {fld}")
        else:
            FLD_HISTORIES[fld] = fld_history

    def request_scheduled(self, request, spider):
        if not self.log_lscores or not self.crawler.stats:
            return

        total_requests = self.crawler.stats.get_value("total_requests")
        lscore_window = self.log_lscores.maxlen
        # Nothing to log or lscore_window is undefined
        if not total_requests or not lscore_window:
            return

        # Log the average lscore every `lscore_window` requests
        if total_requests % lscore_window == 0 and self.log_lscores:
            lscore_avg = sum(self.log_lscores) / len(self.log_lscores)
            LOGGER.info(
                f"Mean lscore value for last {lscore_window} requests: {lscore_avg}"
            )

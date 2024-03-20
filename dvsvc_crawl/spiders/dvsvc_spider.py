import random
from scrapy import Request, signals
from scrapy.spiders.crawl import CrawlSpider
from scrapy.linkextractors import LinkExtractor

from expiringdict import ExpiringDict
from collections import deque
from tld import get_tld

from dvsvc_crawl.spiders import get_logger
from dvsvc_crawl.items import CandidatePage
from heuristics import dvsvc_scorers


LOGGER = get_logger()
LINK_SCORER = dvsvc_scorers.get_link_scorer()
PAGE_SCORER = dvsvc_scorers.get_page_scorer()

EXCEPTIONAL_PSCORE = 0.95  # TODO Impossible

GOOD_PSCORE = 0.80
GOOD_PSCORE_PROPORTION = 0.5
ENOUGH_PSCORE_SAMPLES = 5

# Cache a visit count and good-pscore count for each domain
DOMAIN_PSCORES_CACHE = ExpiringDict(
    max_len=1_000_000, max_age_seconds=60.0 * 60.0 * 24.0  # 24-hour expiry
)


def lscore_to_prio(lscore: float) -> int:
    # if lscore > 0.8:
    #     return 3
    # elif lscore > 0.6:
    #     return 2
    # elif lscore > 0.4:
    #     return 1
    # return 0
    return int(lscore * 10)


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
            yield Request(url, callback=self.parse)

    def parse(self, response):
        pscore = PAGE_SCORER.score(response.text)

        links = list(LinkExtractor().extract_links(response))
        random.shuffle(links)

        for link in links:
            # Yield new request
            lscore = LINK_SCORER.score(link.url, pscore.value)
            yield Request(
                link.url, callback=self.parse, priority=lscore_to_prio(lscore.value)
            )
            # Update health metrics
            self.log_lscores.append(lscore.value)
            if self.crawler.stats:
                self.crawler.stats.inc_value("total_requests")

        # Itemise immediately for exceptional pscore
        if pscore.value >= EXCEPTIONAL_PSCORE:
            yield CandidatePage(
                link=response.url, pscore=pscore, time_crawled=response.headers["Date"]
            )

        # Otherwise, itemise if the proportion of good pscores is high and we have enough samples
        domain = get_tld(response.url, as_object=True).fld
        domain_pscores = (
            # Default to 0 visits, 0 good pscores
            DOMAIN_PSCORES_CACHE[domain]
            if domain in DOMAIN_PSCORES_CACHE
            else (0, 0)
        )
        # Increment pscores for the domain
        domain_pscores = (
            domain_pscores[0] + 1,
            domain_pscores[1] + int(pscore.value >= GOOD_PSCORE),
        )
        if (
            domain_pscores[0] > ENOUGH_PSCORE_SAMPLES
            and domain_pscores[1] / domain_pscores[0] >= GOOD_PSCORE_PROPORTION
        ):
            DOMAIN_PSCORES_CACHE[domain] = (
                0,
                0,
            )  # TODO: Entirely stop requests to the domain
            yield CandidatePage(
                link=domain, pscore=pscore, time_crawled=response.headers["Date"]
            )
        else:
            DOMAIN_PSCORES_CACHE[domain] = domain_pscores

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

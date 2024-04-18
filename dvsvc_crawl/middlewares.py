from scrapy.exceptions import IgnoreRequest
from scrapy.http import Response

from dvsvc_crawl import helpers
from dvsvc_crawl.spiders import get_spiders_logger

FLD_BAD_RESPONSES_ALLOWED = 10

_LOGGER = get_spiders_logger()

_IGNORE_FLDS = {
    # By reach, from https://www.pressgazette.co.uk/media-audience-and-business-data/media_metrics/most-popular-websites-news-uk-monthly-2/
    "bbc.com",
    "thesun.co.uk",
    "dailymail.co.uk",
    "mirror.co.uk",
    "theguardian.com",
    "independent.co.uk",
    "news.sky.com",
    "itv.com",
    "telegraph.co.uk",
    "metro.co.uk",
    "moneysavingexpert.com",
    "thetimes.co.uk",
    "express.co.uk",
    "birminghammail.co.uk",
    "standard.co.uk",
    "manchestereveningnews.co.uk",
    "gbnews.com",
    "dailyrecord.co.uk",
    "radiotimes.com",
    "nytimes.com",
    "liverpoolecho.co.uk",
    "digitalspy.com",
    "walesonline.co.uk",
    "hellomagazine.com",
    "inews.co.uk",
    "dailystar.co.uk",
    "forbes.com",
    "lbc.co.uk",
    "chroniclelive.co.uk",
    "ok.co.uk",
    "goodhousekeeping.com",
    "bristolpost.co.uk",
    "examinerlive.co.uk",
    "expressandstar.com",
    "reuters.com",
    "ft.com",
    "inyourarea.co.uk",
    "gloucestershirelive.co.uk",
    "unilad.co.uk",
    "mylondon.news",
    "businessinsider.com",
    "people.com",
    "cnn.com",
    "cosmopolitan.com",
    "belfasttelegraph.co.uk",
    # With some duplicates, https://pressgazette.co.uk/media-audience-and-business-data/media_metrics/most-popular-websites-news-us-monthly-3/
    "nytimes.com",
    "cnn.com",
    "msn.com",
    "foxnews.com",
    "finance.yahoo.com",
    "people.com",
    "usatoday.com",
    "nypost.com",
    "news.google.com",
    "washingtonpost.com",
    "dailymail.co.uk",
    "bbc.com",
    "cnbc.com",
    "forbes.com",
    "newsweek.com",
    "apnews.com",
    "nbcnews.com",
    "news.yahoo.com",
    "wsj.com",
    "theguardian.com",
    "businessinsider.com",
    "cbsnews.com",
    "thehill.com",
    "abcnews.go.com",
    "politico.com",
    "usnews.com",
    "buzzfeed.com",
    "huffpost.com",
    "drudgereport.com",
    "reuters.com",
    "the-sun.com",
    "latimes.com",
    "substack.com",
    "variety.com",
    "thecooldown.com",
    "theatlantic.com",
    "bloomberg.com",
    "patch.com",
    "breitbart.com",
    "sfgate.com",
    "independent.co.uk",
    "axios.com",
    "theepochtimes.com",
    "today.com",
    "thedailybeast.com",
    "sciencealert.com",
    "newsmax.com",
    "nj.com",
    "usmagazine.com",
    "al.com",
    # Wikipedia and Wikimedia projects
    "wikipedia.org",
    "wikimedia.org",
    "wiktionary.org",
    "wikidata.org",
    "mediawiki.org",
    "wikibooks.org",
    "wikisource.org",
    "wikiversity.org",
    "wikinews.org",
    "wikivoyage.org",
    "wikiquote.org",
    "wikispecies.org",
    # UK government data sources
    "assets.publishing.service.gov.uk",
    "ons.gov.uk",
    "cy.ons.gov.uk",
}


class DvsvcBlacklistMiddleware:
    def __init__(self):
        self.fld_blacklist = set()
        self.fld_bad_responses = {}

        self.fld_blacklist.update(_IGNORE_FLDS)

    def process_request(self, request, spider):
        fld = helpers.get_fld(request.url)

        if fld in self.fld_blacklist:
            raise IgnoreRequest(f"Ignoring request to blacklisted FLD: {request.url}")
        return None

    def process_response(self, request, response, spider):
        fld = helpers.get_fld(request.url)

        if response.status != 200 and fld not in self.fld_blacklist:
            # Increment counter for non-200 responses
            if fld not in self.fld_bad_responses:
                self.fld_bad_responses[fld] = 1
            else:
                self.fld_bad_responses[fld] += 1

            if self.fld_bad_responses[fld] >= FLD_BAD_RESPONSES_ALLOWED:
                self.fld_blacklist.add(fld)
                _LOGGER.info(f"Blacklisted FLD: {fld}")

        return response

    def process_exception(self, request, exception, spider):
        if isinstance(exception, IgnoreRequest):
            # Propagate rudimentary response to spider so it may be processed
            return Response(url=request.url, status=400, request=request)
        # Non-IgnoreRequest exceptions will be propagated to other middleware
        return None

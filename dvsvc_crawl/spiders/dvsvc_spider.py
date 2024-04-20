from scrapy import Request, signals
from scrapy.spiders.crawl import CrawlSpider
from scrapy.linkextractors import LinkExtractor
from scrapy.http.response.text import TextResponse
from scrapy.http.response import Response

from expiringdict import ExpiringDict
from collections import deque
from datetime import datetime, timezone
import typing

from dvsvc_crawl import helpers
from dvsvc_crawl.spiders import get_spiders_logger
from dvsvc_crawl.items import DvsvcCrawlItem, DvsvcCrawlBatch
from heuristics import dvsvc_scorers
from heuristics.scorers import Score


_LOGGER = get_spiders_logger()

_LINK_SCORER = dvsvc_scorers.get_link_scorer()
_PAGE_SCORER = dvsvc_scorers.get_page_scorer()

_SUFFICIENT_PSCORE = 0.95  # A sufficient pscore to immediately itemise a page

_NECESSARY_PSCORE = 0.80  # A necessary pscore to consider itemising as part of a page set for the same fld
_NECESSARY_FLD_RATIO = 0.5  # The minimum ratio of good pscores to total pscores needed
_NECESSARY_FLD_SAMPLES = 5  # The minimum number of samples needed

# Cache a visit count and good-pscore count for each domain
_FLD_HISTORIES = ExpiringDict(
    max_len=100_000, max_age_seconds=60.0 * 60.0 * 24.0  # 24-hour expiry
)

_METRIC_OUTPUT_FREQUENCY = 100  # Log health metrics every 100 requests


def lscore_to_prio(lscore: float) -> int:
    return int(lscore * 10)


def get_response_time(resp: Response) -> datetime:
    return datetime.strptime(
        resp.headers["Date"].decode("utf-8"), "%a, %d %b %Y %H:%M:%S %Z"
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
        if pscore.value >= _NECESSARY_PSCORE:
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
            self.total_pages >= _NECESSARY_FLD_SAMPLES
            and len(self.good_pages) / self.total_pages >= _NECESSARY_FLD_RATIO
        )


class DvsvcSpider(CrawlSpider):
    name = "dvsvc"
    start_urls = [
        # "https://www.scotborders.gov.uk/directory/21/domestic_abuse_services",
        "https://refuge.org.uk/?gclid=CjwKCAiA2L-dBhACEiwAu8Q9YMl0P8KmygqPQxh8hTpqV9XnaGtLZgtwawGxAJBvx6STc8lZRLCcdxoCeaIQAvD_BwE",
        "https://www.womensaid.org.uk/?gclid=CjwKCAiA2L-dBhACEiwAu8Q9YFi0psjaVOq4uwCmOQveikZfaiIeriGSNx--ju_p1hrV7fQp-aDHHxoChegQAvD_BwE",
        "https://fifewomensaid.org.uk/",
        "https://www.dogstrustfreedomproject.org.uk/",
        "https://galop.org.uk/",
        "https://karmanirvana.org.uk/",
        "https://www.opoka.org.uk/",
        "https://www.sdafmh.org.uk/en/",
        "https://www.modernslaveryhelpline.org/",
        "https://www.aberconwydomesticabuseservice.com/",
        "https://westwalesdas.org.uk/",
        "https://www.advancecharity.org.uk/",
        "https://www.al-hasaniya.org.uk/",
        "https://amadudu.org/",
        "https://www.anahproject.org/",
        "http://www.andovercrisisandsupportcentre.org.uk/",
        "https://apnahaq.org.uk/",
        "https://www.wgn.org.uk/our-services/counselling-and-therapeutic-support/ascent-counselling",
        "http://www.ashaprojects.org.uk/",
        "https://www.ashiana.org.uk/",
        "http://www.ashianasheffield.org/",
        "https://www.asianwomencentre.org.uk/",
        "https://atalyfro.org/",
        "https://www.aurorand.org.uk/",
        "https://idas.org.uk/",
        "https://basisyorkshire.org.uk/",
        "https://www.bcha.org.uk/",
        "https://www.p-a-c.org.uk/",
        "http://www.bedehouse.org.uk/",
        "http://impakt.org.uk/domestic-abuse/",
        "https://www.behind-closed-doors.org.uk/",
        "https://www.stroudwomensrefuge.org/",
        "https://phoenixdas.co.uk/",
        "https://www.actionhomeless.org.uk/",
        "https://broxtowewomensproject.org.uk/",
        "https://calderdalestayingsafe.org.uk/",
        "https://www.solacewomensaid.org/get-help/other-support-services/camden-safety-net",
        "https://caraessex.org.uk/",
        "https://westwalesdas.org.uk/",
        "https://www.chadd.org.uk/",
        "https://www.changegrowlive.org/domestic-abuse-service-east-sussex/info",
        "https://changingpathways.org/",
        "https://www.cheshireeast.gov.uk/livewell/staying-safe/domestic-abuse-and-sexual-violence/domestic-abuse-getting-help.aspx",
        "https://www.cheshirewestandchester.gov.uk/residents/crime-prevention/domestic-abuse",
        "http://claudiajones.org/",
        "https://www.essexcompass.org.uk/",
        "https://www.contentosocialhomes.com/",
        "https://www.cornwallrefugetrust.co.uk/",
        "https://www.crossroadsderbyshire.org/",
        "https://www.davss.org.uk/",
        "https://www.ncha.org.uk/care-and-support/care-homes-and-services/all-care-homes-and-services/derbyshire-wish/",
        "https://devonrapecrisis.org.uk/",
        "https://dasunorthwales.co.uk/",
        "https://dsahelpline.org/",
        "https://dvip.org/",
        "https://www.doncaster.gov.uk/services/crime-anti-social-behaviour-nuisance/domestic-abuse-2",
        "http://www.ddwa.org.uk/",
        "http://www.calandvs.org.uk/",
        "https://www.esdas.org.uk/",
        "https://1space.eastsussex.gov.uk/Services/823/East-Sussex-refuge-s",
        "https://edanlincs.org.uk/",
        "https://mwht.org.uk/eden-house-uk/",
        "https://www.ellas.org.uk/",
        "https://empowermentcharity.org.uk/the-den/",
        "https://www.endeavourproject.org.uk/",
        "https://www.nhs.uk/services/service-directory/erin-house/N10976074",
        "https://eveda.org.uk/",
        "https://www.fearless.org/",
        "https://findtheglow.org.uk/",
        "https://flagdv.org.uk/",
        "https://fortalice.org.uk/",
        "https://www.foundationuk.org/",
        "https://www.freeva.org.uk/",
        "https://www.gateshead.gov.uk/article/8723/Domestic-abuse",
        "https://www.gilgalbham.org.uk/",
        "https://www.gdass.org.uk/",
        "http://www.gorwel.org/eng/",
        "http://www.gdva.org.uk/",
        "https://www.derbyshirehealthcareft.nhs.uk/getting-help/community-support-near-you-infolink/hadhari-nari-advice-and-information-centre",
        "https://hafancymru.co.uk/",
        "https://www.haloproject.org.uk/",
        "https://www.myharbour.org.uk/",
        "https://www.harvoutreach.org.uk/",
        "https://www.hayshousing.co.uk/womens-project",
        "https://www.haringey.gov.uk/community/community-safety-and-engagement/domestic-violence/hearthstone",
        "https://hercentre.org/",
        "https://hertsrapecrisis.org.uk/",
        "https://www.hestia.org/",
        "https://www.nhs.uk/services/service-directory/holly-house-your-housing-group/N10968518",
        "https://www.hounslow.gov.uk/info/20056/community_safety/2133/domestic_abuse_and_violence_against_women_and_girls_vawg/4",
        "https://www.hfw.org.uk/",
        "https://humraaz.co.uk/",
        "https://www.ichoosefreedom.co.uk/",
        "https://idas.org.uk/",
        "https://ikwro.org.uk/",
        "https://imece.org.uk/",
        "https://www.domesticabusehelpline.co.uk/",
        "https://www.saferderbyshire.gov.uk/what-we-do/domestic-abuse/staff-guidance/adults/independent-domestic-violence-advisor/independent-domestic-violence-advisor.aspx",
        "https://www.survivorsuk.org/ways-we-can-help/",
        "https://www.nhs.uk/services/service-directory/jasmine-and-lotus-grove/N10987095",
        "https://www.julianhouse.org.uk/service/children-and-young-people-domestic-abuse-service/",
        "http://www.kiranss.org.uk/",
        "https://www.kmewo.com/",
        "https://www.leewaysupport.org/?gclid=CjwKCAiA2L-dBhACEiwAu8Q9YP3K_OC-rnJmkIJUIxX8SpE2OMDAJ91d6RU4XB63GH7Sw9d6QufLtBoC4msQAvD_BwE",
        "https://www.lincolnshirerapecrisis.org.uk/",
        "https://gov.wales/live-fear-free",
        "https://liverpooldomesticabuseservice.org.uk/",
        "https://livingbeyondsurviving.co.uk/",
        "https://lwa.org.uk/",
        "https://www.llamau.org.uk/?gclid=CjwKCAiA2L-dBhACEiwAu8Q9YCClKR5cn3WjKDy5BQR4BNcmntRuq0XS2euJtGwEnxD12isbQRtj6xoCOcYQAvD_BwE",
        "https://www.lbwp.co.uk/",
        "https://www.nhs.uk/services/service-directory/maggie-neil-house/N10502572",
        "https://www.nhs.uk/services/service-directory/malala-house/N10968559",
        "https://mensadviceline.org.uk/",
        "https://www.mkact.com/",
        "https://www.moneyadviceplus.org.uk/fsl/",
        "https://www.familycrisis.co.uk/",
        "https://www.nhs.uk/services/service-directory/mozaic-advocacy-service/N10968560",
        "https://www.mysistersplace.org.uk/",
        "https://www.mycwa.org.uk/",
        "https://mylife.redbridge.gov.uk/homepage",
        "https://www.ndas.co/",
        "https://citizensadvicerushmoor.org.uk/domestic-abuse-support/",
        "https://www.new-era.uk/",
        "https://www.newhorizonsdv.com/our-impact/",
        "https://www.thenextchapter.org.uk/",
        "https://nextlinkhousing.co.uk/",
        "https://www.newcastleidas.co.uk/",
        "https://www.nhs.uk/services/service-directory/nightingale-house/N10968556",
        "https://ndada.co.uk/",
        "https://www.northlincs.gov.uk/people-health-and-care/worried-about-a-relationship/",
        "https://www.nsdas.org.uk/",
        "https://www.oasisdaservice.org/",
        "https://www.opoka.org.uk/",
        "https://www.osarcc.org.uk/",
        "https://www.cats.org.uk/what-we-do/paws-protect",
        "https://pdap.co.uk/",
        "https://www.placesforpeople.co.uk/about-us/who-we-are/our-companies/places-for-people-living-plus",
        "https://www.sanctuary-supported-living.co.uk/find-services/domestic-abuse/devon/plymouth-domestic-abuse-services-pdas",
        "https://www.pdvs.org.uk/",
        "https://www.rasasc.org.uk/",
        "https://rapecrisis.org.uk/find-a-centre/rape-crisis-tyneside-and-northumberland/",
        "https://www.wa-rct.org.uk/",
        "https://reducingtherisk.org.uk/",
        "https://refuge.org.uk/?gclid=CjwKCAiA2L-dBhACEiwAu8Q9YMl0P8KmygqPQxh8hTpqV9XnaGtLZgtwawGxAJBvx6STc8lZRLCcdxoCeaIQAvD_BwE",
        "https://www.nationaldahelpline.org.uk/",
        "https://refuge4pets.org.uk/",
        "https://www.riseuk.org.uk/",
        "http://www.risingsunkent.com/",
        "https://www.rwwa.org.uk/",
        "https://rojwomen.org.uk/",
        "https://www.rosswa.co.uk/",
        "https://rotherhamrise.org.uk/",
        "https://www.rsacc-thecentre.org.uk/",
        "https://www.nhs.uk/services/service-directory/ruffley-house/N10968205",
        "https://www.safeinsussex.co.uk/",
        "https://www.safepartnership.org/",
        "https://www.safesteps.org/",
        "https://safe2speak.co.uk/",
        "https://safenet.org.uk/",
        "https://safenet.org.uk/",
        "https://www.saferplaces.co.uk/",
        "https://www.saheli.org.uk/",
        "https://sateda.org/",
        "https://www.savana.org.uk/",
        "https://www.maryseacolehouse.com/",
        "https://swaca.com/",
        "https://selbyadvice.org.uk/organisation/idas-independent-domestic-abuse-services/",
        "https://sericc.org.uk/",
        "https://www.shropsdas.org.uk/",
        "http://www.signhealth.org.uk/",
        "https://www.sarsas.org.uk/",
        "https://www.sl-domesticabuseservices.org.uk/",
        "https://www.swsda.org.uk/",
        "https://southallblacksisters.org.uk/",
        "https://springfieldsupport.org/",
        "https://www.pathway-project.co.uk/",
        "https://stamma.org/",
        "https://stayingput.org.uk/",
        "https://www.steppingstonesluton.co.uk/",
        "http://www.stockportwithoutabuse.org.uk/",
        "https://www.thirteengroup.co.uk/",
        "https://stonewallhousing.org/",
        "https://www.stonewater.org/",
        "https://stopdomesticabuse.uk/",
        "https://www.voicenorthants.org/about-voice-northants/sunflower-centre/",
        "http://supportafterrapeleeds.org.uk/",
        "https://survivingeconomicabuse.org/what-we-do/survivor-forum/",
        "https://www.stevenage.gov.uk/",
        "https://survivorsnetwork.org.uk/",
        "https://www.suttonwomen.co.uk/",
        "https://swadomesticabuse.org/",
        "https://tender.org.uk/",
        "https://www.acorncare.org.uk/",
        "https://angelou-centre.org.uk/",
        "http://www.birminghamcrisis.org.uk/",
        "https://thedashcharity.org.uk/",
        "https://www.theelmfoundation.org.uk/",
        "https://thefirststep.org.uk/",
        "https://thehavenproject.org.uk/",
        "https://thelibertycentre.org.uk/",
        "https://niaendingviolence.org.uk/",
        "http://www.survivorpathway.org.uk/services/the-phoenix-project-wiltshire/",
        "https://www.thewishcentre.org/",
        "https://www.womenscentrecornwall.org.uk/",
        "https://theyoutrust.org.uk/",
        "https://threshold-das.org.uk/",
        "https://thrivewomensaid.org.uk/",
        "https://www.sanctuary-supported-living.co.uk/find-services/domestic-abuse/devon/torbay-domestic-abuse-service-tdas",
        "https://www.towerhamlets.gov.uk/lgnl/community_and_living/community_safety__crime_preve/domestic_violence/VAWG-Service-Directory/Support_services_for_domestic_abuse.aspx",
        "https://www.tdas.org.uk/",
        "https://cranstoun.org/help-and-advice/domestic-abuse/transform-sutton/",
        "https://www.frameworkha.org/placement-providers/umuada-womens-refuge",
        "https://www.nhs.uk/services/service-directory/va-housing-provider-beth-refuge/N10968255",
        "https://valleyhouse.org.uk/",
        "https://www.riverside.org.uk/",
        "https://localgiving.org/charity/voices/",
        "https://www.waitsaction.org/",
        "https://www.walthamforest.gov.uk/safestreets",
        "https://www.wwin.org.uk/",
        "https://directory.westberks.gov.uk/kb5/westberkshire/directory/service.page?id=w27XGexXKV8",
        "https://www.cheshirewestandchester.gov.uk/",
        "https://www.wmrsasc.org.uk/",
        "https://www.wightdash.co.uk/",
        "https://www.wiltshire.gov.uk/article/1033/Domestic-abuse-awareness-and-information",
        "https://www.wwaca.org/",
        "https://womanstrust.org.uk/",
        "https://www.wgn.org.uk/",
        "https://www.womensaid.org.uk/?gclid=CjwKCAiA2L-dBhACEiwAu8Q9YGz8NSc2nD-JY3DrfC7qAkayOqEYWnt7160vajACMu0PYNPXHTnqhRoCmzMQAvD_BwE",
        "https://www.westsussex.gov.uk/fire-emergencies-and-crime/domestic-abuse/",
        "https://www.yoursanctuary.org.uk/",
    ]

    log_lscores = deque(maxlen=_METRIC_OUTPUT_FREQUENCY)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        # Invoke request_scheduled every time a request is scheduled, e.g. to update health metrics.
        crawler.signals.connect(
            spider.request_scheduled, signal=signals.request_scheduled
        )
        return spider

    def start_requests(self):
        for url in self.start_urls:
            yield Request(
                url,
                callback=self.parse,
                priority=0,
                meta={"lscore": None, "time_queued": datetime.now(timezone.utc)},
            )

    def parse(self, response):
        if self.crawler.stats:
            self.crawler.stats.inc_value("total_responses")

        if not isinstance(response, TextResponse):
            return

        pscore = _PAGE_SCORER.score(response.text)

        links = list(LinkExtractor().extract_links(response))

        for link in links:
            # Yield new request
            lscore = _LINK_SCORER.score(link.url, pscore.value)
            yield Request(
                link.url,
                callback=self.parse,
                priority=lscore_to_prio(lscore.value),
                meta={"lscore": lscore, "time_queued": datetime.now(timezone.utc)},
            )
            # Update health metrics
            self.log_lscores.append(lscore.value)

        # Itemise immediately for exceptional pscore
        if pscore.value >= _SUFFICIENT_PSCORE:
            yield DvsvcCrawlItem(
                link=response.url,
                pscore=pscore,
                lscore=response.meta["lscore"],
                time_queued=response.meta["time_queued"],
                time_crawled=get_response_time(response),
            )
            _LOGGER.info(f"Itemised page: {response.url}")

        # Consider itemising set of pages of the same fld
        fld = helpers.get_fld(response.url)
        fld_history = typing.cast(
            FLDVisits, _FLD_HISTORIES[fld] if fld in _FLD_HISTORIES else FLDVisits()
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
            _FLD_HISTORIES.pop(fld)
            _LOGGER.info(f"Itemised page set for FLD: {fld}")
        else:
            _FLD_HISTORIES[fld] = fld_history

        self.log_metrics()

    def log_metrics(self):
        # Log health metrics every METRIC_OUTPUT_FREQUENCY requests
        if not self.log_lscores or not self.crawler.stats:
            return

        total_responses = self.crawler.stats.get_value("total_responses")
        if total_responses != 0 and total_responses % _METRIC_OUTPUT_FREQUENCY == 0:
            _LOGGER.info(f"Total responses: {total_responses}")
            _LOGGER.info(
                f"Mean lscore value generated from last {_METRIC_OUTPUT_FREQUENCY} responses: {sum(self.log_lscores) / len(self.log_lscores)}"
            )
            _LOGGER.info(f"Queued requests: {len(self.crawler.engine.slot.scheduler)}")

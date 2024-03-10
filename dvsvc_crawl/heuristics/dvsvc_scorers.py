import os
from bs4 import BeautifulSoup

from helpers import read_csv
from scorers import *

__CURDIRNAME = os.path.dirname(__file__)


def _has_quick_exit(soup: BeautifulSoup) -> bool:
    anchors = soup.find_all("a")
    buttons = soup.find_all("button")
    clickables = soup.find_all(attrs={"onclick": True})

    matches = 0
    NECESSARY_MATCHES = 2

    for element in anchors + buttons + clickables:
        words = element.get_text().lower().split(" ")

        if any(w in words for w in ["close", "exit", "leave", "hide"]):
            matches += 1
        if any(w in words for w in ["now", "quick", "emergency", "instant"]):
            matches += 1
        if any(w in words for w in ["site", "website", "page", "webpage"]):
            matches += 1

    return matches >= NECESSARY_MATCHES


__SCOTTISH_CHARITIES = read_csv(os.path.join(
    __CURDIRNAME, "Scot-CharityExport-09-Mar-2024.csv"))

__PAGE_PREDICATES = [
    KeywordPredicate({"victim", "victims", "victimizing", "victimization", "victimize",
                     "victimized", "victimising", "victimisation", "victimise", "victimised"},
                     {"abuse", "violence", "partner"}, constant_weight=7),
    KeywordPredicate({"rape", "raped"}, constant_weight=10),
    KeywordPredicate({"abuse", "abusing", "abused"}, constant_weight=3),
    KeywordPredicate({"assault", "assaulted"}, constant_weight=3),
    KeywordPredicate({"survive", "survivor", "survivors",
                     "survival", "survived", "surviving"},
                     {"abuse", "abusing", "violent", "violence", "trauma", "relationship"}, constant_weight=4),
    KeywordPredicate({"living", "life", "lives"},
                     {"free", "fear", "without"}, constant_weight=2),
    KeywordPredicate({"referral"}, constant_weight=2),
    KeywordPredicate({"sexual", "sexually"},
                     {"abuse", "abused", "assault", "assaulted", "harassment", "harassed", "exploitation", "exploited", "violence"}, constant_weight=8),
    KeywordPredicate({"economic"}, {"abuse"}, constant_weight=6),
    KeywordPredicate({"homeless", "homelessness"}, constant_weight=2),
    KeywordPredicate({"shelter", "shelters"}, constant_weight=2),
    KeywordPredicate({"refuge"}, constant_weight=3),
    KeywordPredicate({"refugee"}, constant_weight=3),
    KeywordPredicate({"domestic"}, constant_weight=12),
    KeywordPredicate({"agency", "agencies"}, constant_weight=1),
    KeywordPredicate({"help", "helps"}, {
                     "find", "seek", "deal"}, constant_weight=1),
    KeywordPredicate({"power", "dynamic", "dynamics"}, {"relationship", "partner"},
                     constant_weight=2),
    KeywordPredicate({"organisation", "organization"}, constant_weight=2),
    KeywordPredicate({"women", "woman"},
                     {"help", "helps", "helping", "aid", "aids", "aiding", "assist", "assists", "assisting"}, constant_weight=2),  # Not -hood
    KeywordPredicate({"child", "children", "childhood"}, constant_weight=1),
    KeywordPredicate({"girl", "girls"}, constant_weight=1),
    KeywordPredicate({"boy", "boys"}, constant_weight=1),
    KeywordPredicate({"adult", "adulthood"}, constant_weight=1),
    KeywordPredicate({"neglect", "neglected"},
                     {"partner", "adult", "child", "childhood", "children"}, constant_weight=2),
    KeywordPredicate({"crisis"}, constant_weight=5),  # Not crises
    KeywordPredicate({"lgbt", "lgbtq", "lgbtqi",
                     "lgbtqia", "lgb", "grsm"}, constant_weight=3),
    KeywordPredicate({"emergency"}, constant_weight=2),
    KeywordPredicate({"advisor", "advisors"}, constant_weight=2),
    KeywordPredicate({"counsel", "counsellor", "counselor",
                     "counsellors", "counselors", "counseling", "counselling"}, constant_weight=3),
    KeywordPredicate({"therapy", "therapist", "therapists"},
                     constant_weight=2),
    KeywordPredicate({"community", "communities"}, constant_weight=1),
    KeywordPredicate({"coalition", "coalitions"}, constant_weight=1),
    KeywordPredicate({"violence"}, constant_weight=4),  # Not violent
    KeywordPredicate({"harass", "harasses", "harassing",
                     "harassment"}, constant_weight=4),
    KeywordPredicate({"sanctuary", "sanctuaries"}, constant_weight=4),
    KeywordPredicate({"safehouse", "safehouses"}, constant_weight=5),
    KeywordPredicate({"haven", "havens"}, constant_weight=3),
    KeywordPredicate({"trust"}, constant_weight=3),
    KeywordPredicate({"charity", "charitable"}, constant_weight=5),
    KeywordPredicate({"foundation"}, constant_weight=2),
    KeywordPredicate({"prevent", "prevents"}, constant_weight=2),
    KeywordPredicate({"marriage", "relationship"}, constant_weight=2),
    KeywordPredicate({"marriage"},
                     {"force", "forced", "trap", "trapped", "coerce", "coercion", "coerced"}, constant_weight=9),
    KeywordPredicate({"donate", "donation", "donations", "fundraise", "fundraising"},
                     constant_weight=2),
    KeywordPredicate({"trauma", "traumatic"},
                     constant_weight=5),  # Not traumatise
    KeywordPredicate({"confidential", "confidentiality", "confidentially"},
                     constant_weight=4),
    KeywordPredicate({"helpline", "hotline"}, constant_weight=8),
    KeywordPredicate({"protection"}, {"order", "orders"}, constant_weight=5),
    KeywordPredicate({"empowerment"},
                     {"program", "programs", "programme", "programmes"}, constant_weight=6),
    KeywordPredicate({"ptsd"}, constant_weight=5),
    KeywordPredicate({"stalking", "stalker"}, constant_weight=4),
    KeywordPredicate({"report", "reporting"}, {
                     "anonymous", "anonymously"}, constant_weight=2),
    KeywordPredicate({"duluth"}, {"model"}, constant_weight=5),
    KeywordPredicate({"restraining"}, {"order"}, constant_weight=5),
    KeywordPredicate({"reproduce", "reproductive"}, {
                     "coerced", "coerce", "coercing", "coercion"}, constant_weight=7),

    KeywordPredicate(__SCOTTISH_CHARITIES.keys(), constant_weight=20),

    HtmlPredicate(_has_quick_exit, constant_weight=25, scaling_weight=1),
]


__URL_PREDICATES = [
    # Weigh words lower than before, particularly context-dependent ones, as we expect fewer overall matches, giving us less contextual understanding.
    PartialKeywordPredicate({"victim"}, constant_weight=2),
    PartialKeywordPredicate({"rape"}, constant_weight=2),
    PartialKeywordPredicate({"abus"}, constant_weight=3),
    PartialKeywordPredicate({"assault", "assaulted"}, {
                            "sexual"}, constant_weight=3),
    PartialKeywordPredicate({"surviv"}, constant_weight=2),
    PartialKeywordPredicate({"homeless"}, constant_weight=1),
    PartialKeywordPredicate({"shelter"}, constant_weight=2),
    PartialKeywordPredicate({"refuge"}, constant_weight=2),
    PartialKeywordPredicate(
        {"domestic"}, {"violence", "abuse"}, constant_weight=5),
    PartialKeywordPredicate({"agenc"}, constant_weight=1),
    PartialKeywordPredicate(
        {"organisation", "organization"}, constant_weight=1),
    PartialKeywordPredicate(
        {"neglect"}, {"partner", "child"}, constant_weight=2),
    PartialKeywordPredicate({"crisis"}, {
                            "line", "centre"}, constant_weight=4),
    PartialKeywordPredicate({"crisis"}, {
                            "abuse", "volence"}, constant_weight=3),
    PartialKeywordPredicate({"lgbt", "grsm"}, constant_weight=2),
    PartialKeywordPredicate({"emergency"}, constant_weight=2),
    PartialKeywordPredicate({"advisor"}, constant_weight=2),
    PartialKeywordPredicate({"counsel"}, constant_weight=1),
    PartialKeywordPredicate(
        {"therapy", "therapist"}, constant_weight=1),
    PartialKeywordPredicate(
        {"service"}, {"violence", "line", "abuse", "overcom"}, constant_weight=1),
    PartialKeywordPredicate({"communit"}, constant_weight=1),
    PartialKeywordPredicate({"coalition"}, constant_weight=1),
    PartialKeywordPredicate({"violence"}, constant_weight=2),  # Not violent
    PartialKeywordPredicate({"harass"}, constant_weight=3),
    PartialKeywordPredicate({"sanctuar"}, constant_weight=3),
    PartialKeywordPredicate({"haven", "havens"}, constant_weight=2),
    PartialKeywordPredicate({"trust"}, constant_weight=2),
    PartialKeywordPredicate({"charit"}, constant_weight=3),
    PartialKeywordPredicate({"foundation"}, constant_weight=2),
    PartialKeywordPredicate({"marriage"}, {"force"}, constant_weight=4),
    PartialKeywordPredicate({"trauma"}, constant_weight=4),  # Not traumatise
    PartialKeywordPredicate({"confidential"}, constant_weight=2),
    PartialKeywordPredicate({"helpline"}, constant_weight=3),


    TldPredicate("org", constant_weight=2, scaling_weight=1.3),
    TldPredicate("uk", constant_weight=1),
    TldPredicate("scot", constant_weight=1),
    TldPredicate("gov.uk", constant_weight=3, scaling_weight=1.2),
    TldPredicate("gov.scot", constant_weight=3, scaling_weight=1.2),
    TldPredicate("org.uk", constant_weight=3, scaling_weight=1.4),
    TldPredicate("org.scot", constant_weight=3, scaling_weight=1.4),
]


def get_url_scorer() -> URLScorer:
    return URLScorer(6, __URL_PREDICATES)


def get_page_scorer() -> PageScorer:
    return PageScorer(30, __PAGE_PREDICATES)


print(__PAGE_PREDICATES[-1])

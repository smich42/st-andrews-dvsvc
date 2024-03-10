import os
from bs4 import BeautifulSoup

from heuristics.helpers import read_csv
from heuristics.scorers import (
    HtmlPredicate,
    KeywordSearchPredicate,
    KeywordTokenPredicate,
    TldPredicate,
    LinkScorer,
    PageScorer,
)

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


def get_link_scorer() -> LinkScorer:
    LINK_PREDICATES = [
        # Weigh words lower than before, particularly context-dependent ones, as we expect fewer overall matches, giving us less contextual understanding.
        KeywordSearchPredicate({"victim"}, constant_weight=2),
        KeywordSearchPredicate({"rape"}, constant_weight=2),
        KeywordSearchPredicate({"abus"}, constant_weight=3),
        KeywordSearchPredicate({"assault", "assaulted"},
                               {"sexual"}, constant_weight=3),
        KeywordSearchPredicate({"surviv"}, constant_weight=2),
        KeywordSearchPredicate({"homeless"}, constant_weight=1),
        KeywordSearchPredicate({"shelter"}, constant_weight=2),
        KeywordSearchPredicate({"refuge"}, constant_weight=2),
        KeywordSearchPredicate({"domestic"}, {"violence", "abuse", "abuser"},
                               constant_weight=5),
        KeywordSearchPredicate({"agenc"}, constant_weight=1),
        KeywordSearchPredicate({"organisation", "organization"},
                               constant_weight=1),
        KeywordSearchPredicate({"neglect"},
                               {"partner", "child"}, constant_weight=2),
        KeywordSearchPredicate({"crisis"},
                               {"line", "centre"}, constant_weight=4),
        KeywordSearchPredicate({"crisis"},
                               {"abuse", "volence"}, constant_weight=3),
        KeywordSearchPredicate({"lgbt", "grsm"}, constant_weight=2),
        KeywordSearchPredicate({"emergency"}, constant_weight=2),
        KeywordSearchPredicate({"advisor"}, constant_weight=2),
        KeywordSearchPredicate({"counsel"}, constant_weight=1),
        KeywordSearchPredicate({"empower"}, constant_weight=2),
        KeywordSearchPredicate({"woman", "women"}, constant_weight=2),
        KeywordSearchPredicate({"ptsd"}, constant_weight=1),
        KeywordSearchPredicate({"therapy", "therapist"},
                               constant_weight=1),
        KeywordSearchPredicate({"service"}, {"violence", "line", "abuse", "overcom"},
                               constant_weight=1),
        KeywordSearchPredicate({"communit"}, constant_weight=1),
        KeywordSearchPredicate({"relationship"}, constant_weight=1),
        KeywordSearchPredicate({"coalition"}, constant_weight=1),
        KeywordSearchPredicate({"violence"}, constant_weight=2),
        KeywordSearchPredicate({"harass"}, constant_weight=3),
        KeywordSearchPredicate({"sanctuar"}, constant_weight=3),
        KeywordSearchPredicate({"haven", "havens"}, constant_weight=2),
        KeywordSearchPredicate({"neglect"}, constant_weight=2),
        KeywordSearchPredicate({"trust"}, constant_weight=2),
        KeywordSearchPredicate({"house", "housing"}, constant_weight=1),
        KeywordSearchPredicate({"charit"}, constant_weight=3),
        KeywordSearchPredicate({"foundation"}, constant_weight=2),
        KeywordSearchPredicate({"marriage"}, {"force"}, constant_weight=4),
        KeywordSearchPredicate({"trauma"}, constant_weight=4),
        KeywordSearchPredicate({"confidential"}, constant_weight=2),
        KeywordSearchPredicate({"helpline"}, constant_weight=3),


        TldPredicate("org", constant_weight=2, scaling_weight=1.3),
        TldPredicate("uk", constant_weight=1),
        TldPredicate("co.uk", constant_weight=1),
        TldPredicate("scot", constant_weight=1),
        TldPredicate("co.scot", constant_weight=1),
        TldPredicate("gov.uk", constant_weight=3, scaling_weight=1.2),
        TldPredicate("gov.scot", constant_weight=3, scaling_weight=1.2),
        TldPredicate("org.uk", constant_weight=3, scaling_weight=1.4),
        TldPredicate("org.scot", constant_weight=3, scaling_weight=1.4),
    ]
    return LinkScorer(6, 0.2, LINK_PREDICATES)


def get_page_scorer() -> PageScorer:
    SCOTTISH_CHARITIES = read_csv(os.path.join(
        __CURDIRNAME, "Scot-CharityExport-09-Mar-2024.csv"))
    print("Loaded charities:", len(SCOTTISH_CHARITIES))

    PAGE_PREDICATES = [
        KeywordTokenPredicate({"victim", "victims", "victimizing", "victimization", "victimize",
                               "victimized", "victimising", "victimisation", "victimise", "victimised"},
                              {"abuse", "violence", "partner"}, constant_weight=7),
        KeywordTokenPredicate({"rape", "raped"}, constant_weight=10),
        KeywordTokenPredicate({"abuse", "abusing", "abused"},
                              constant_weight=3),
        KeywordTokenPredicate({"assault", "assaulted"}, constant_weight=3),
        KeywordTokenPredicate({"survive", "survivor", "survivors",
                               "survival", "survived", "surviving"},
                              {"abuse", "abusing", "violent", "violence", "trauma", "relationship"}, constant_weight=4),
        KeywordTokenPredicate({"living", "life", "lives"},
                              {"free", "fear", "without"}, constant_weight=2),
        KeywordTokenPredicate({"referral"}, constant_weight=2),
        KeywordTokenPredicate({"sexual", "sexually"},
                              {"abuse", "abused", "assault", "assaulted", "harassment", "harassed", "exploitation", "exploited", "violence"}, constant_weight=8),
        KeywordTokenPredicate({"economic"}, {"abuse"}, constant_weight=6),
        KeywordTokenPredicate({"homeless", "homelessness"},
                              constant_weight=2),
        KeywordTokenPredicate({"shelter", "shelters"}, constant_weight=2),
        KeywordTokenPredicate({"refuge", "refuges"}, constant_weight=3),
        KeywordTokenPredicate({"refugee"}, constant_weight=3),
        KeywordTokenPredicate({"domestic"}, {"violence", "abuse", "abuser"},
                              constant_weight=15),
        KeywordTokenPredicate({"agency", "agencies"}, constant_weight=1),
        KeywordTokenPredicate({"help", "helps"},
                              {"find", "seek", "deal"}, constant_weight=1),
        KeywordTokenPredicate({"support", "supports"},
                              {"find", "seek"}, constant_weight=1),
        KeywordTokenPredicate({"suffer", "suffering", "suffers", "suffered"},
                              constant_weight=1),
        KeywordTokenPredicate({"power", "dynamic", "dynamics"},
                              {"relationship", "partner"},
                              constant_weight=2),
        KeywordTokenPredicate({"organisation", "organization"},
                              constant_weight=2),
        KeywordTokenPredicate({"women", "woman"},
                              {"help", "helps", "helping", "aid", "aids", "aiding", "assist", "assists", "assisting"}, constant_weight=2),  # Not -hood
        KeywordTokenPredicate({"child", "children", "childhood"},
                              constant_weight=1),
        KeywordTokenPredicate({"girl", "girls"}, constant_weight=1),
        KeywordTokenPredicate({"boy", "boys"}, constant_weight=1),
        KeywordTokenPredicate({"adult", "adulthood"}, constant_weight=1),
        KeywordTokenPredicate({"neglect", "neglected"},
                              {"partner", "adult", "child", "childhood", "children"}, constant_weight=2),
        KeywordTokenPredicate({"crisis"}, constant_weight=5),  # Not crises
        KeywordTokenPredicate({"lgbt", "lgbtq", "lgbtqi",
                               "lgbtqia", "lgb", "grsm"}, constant_weight=3),
        KeywordTokenPredicate({"emergency"}, constant_weight=2),
        KeywordTokenPredicate({"advisor", "advisors"}, constant_weight=2),
        KeywordTokenPredicate({"counsel", "counsellor", "counselor",
                               "counsellors", "counselors", "counseling", "counselling"}, constant_weight=3),
        KeywordTokenPredicate({"therapy", "therapist", "therapists"},
                              constant_weight=2),
        KeywordTokenPredicate({"community", "communities"}, constant_weight=1),
        KeywordTokenPredicate({"coalition", "coalitions"}, constant_weight=1),
        KeywordTokenPredicate({"violence"}, constant_weight=4),  # Not violent
        KeywordTokenPredicate({"harass", "harasses", "harassing",
                               "harassment"}, constant_weight=4),
        KeywordTokenPredicate({"sanctuary", "sanctuaries"}, constant_weight=4),
        KeywordTokenPredicate({"safehouse", "safehouses"}, constant_weight=5),
        KeywordTokenPredicate({"haven", "havens"}, constant_weight=3),
        KeywordTokenPredicate({"trust", "trusts", "trusting", "trusted",
                              "trustworthy"}, constant_weight=2),  # Noun and verb
        KeywordTokenPredicate({"charity", "charitable"}, constant_weight=5),
        KeywordTokenPredicate({"foundation", "foundations"},
                              constant_weight=2),
        KeywordTokenPredicate({"prevent", "prevents"}, constant_weight=1),
        KeywordTokenPredicate({"marriage", "relationship"}, constant_weight=2),
        KeywordTokenPredicate({"marriage"},
                              {"force", "forced", "trap", "trapped", "coerce", "coercion", "coerced"}, constant_weight=9),
        KeywordTokenPredicate({"donate", "donation", "donations", "fundraise", "fundraising"},
                              constant_weight=2),
        KeywordTokenPredicate({"trauma", "traumatic"},
                              constant_weight=5),  # Not traumatise
        KeywordTokenPredicate({"confidential", "confidentiality", "confidentially"},
                              constant_weight=4),
        KeywordTokenPredicate({"helpline", "hotline"}, constant_weight=8),
        KeywordTokenPredicate({"protection"}, {"order", "orders"},
                              constant_weight=5),
        KeywordTokenPredicate({"empowerment"},
                              {"program", "programs", "programme", "programmes"}, constant_weight=6),
        KeywordTokenPredicate({"ptsd"}, constant_weight=5),
        KeywordTokenPredicate({"stalking", "stalker"}, constant_weight=4),
        KeywordTokenPredicate({"worry", "worried"}, constant_weight=1),
        KeywordTokenPredicate({"report", "reporting"},
                              {"anonymous", "anonymously"}, constant_weight=2),
        KeywordTokenPredicate({"duluth"}, {"model"}, constant_weight=5),
        KeywordTokenPredicate({"restraining"}, {"order"}, constant_weight=5),
        KeywordTokenPredicate({"reproduce", "reproductive"},
                              {"coerced", "coerce", "coercing", "coercion"}, constant_weight=7),

        KeywordTokenPredicate(
            set(SCOTTISH_CHARITIES.keys()), constant_weight=20),

        HtmlPredicate(_has_quick_exit, constant_weight=25, scaling_weight=1),
    ]

    return PageScorer(30, PAGE_PREDICATES)

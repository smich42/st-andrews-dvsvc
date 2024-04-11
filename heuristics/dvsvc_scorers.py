import os
from bs4 import BeautifulSoup

from heuristics.helpers import read_csv_as_dict
from heuristics.scorers import (
    HtmlPredicate,
    KeywordSearchPredicate,
    KeywordTokenPredicate,
    TldPredicate,
    LinkScorer,
    PageScorer,
)

__CURDIRNAME = os.path.dirname(__file__)
__SCOT_CHARITIES_PATH = os.path.join(
    __CURDIRNAME, "..", "resource", "Scot-CharityExport-09-Mar-2024.csv"
)

if not os.path.exists(__SCOT_CHARITIES_PATH):
    raise FileNotFoundError(
        f"Could not find Scottish charities register at {__SCOT_CHARITIES_PATH}"
    )


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
            if any(
                w in words
                for w in [
                    "now",
                    "quick",
                    "quickly",
                    "emergency",
                    "instant",
                    "instantly",
                ]
            ):
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
        KeywordSearchPredicate({"assault", "assaulted"}, {"sexual"}, constant_weight=3),
        KeywordSearchPredicate({"surviv"}, constant_weight=2),
        KeywordSearchPredicate({"homeless"}, constant_weight=1),
        KeywordSearchPredicate({"shelter"}, constant_weight=2),
        KeywordSearchPredicate({"refuge"}, constant_weight=2),
        KeywordSearchPredicate(
            {"domestic"}, {"violence", "abuse", "abuser"}, constant_weight=5
        ),
        KeywordSearchPredicate({"agenc"}, constant_weight=1),
        KeywordSearchPredicate({"organisation", "organization"}, constant_weight=1),
        KeywordSearchPredicate({"neglect"}, {"partner", "child"}, constant_weight=2),
        KeywordSearchPredicate({"crisis"}, {"line", "centre"}, constant_weight=4),
        KeywordSearchPredicate({"crisis"}, {"abuse", "volence"}, constant_weight=3),
        KeywordSearchPredicate({"lgbt", "grsm"}, constant_weight=2),
        KeywordSearchPredicate({"emergency"}, constant_weight=2),
        KeywordSearchPredicate({"advisor"}, constant_weight=2),
        KeywordSearchPredicate({"counsel"}, constant_weight=1),
        KeywordSearchPredicate({"empower"}, constant_weight=2),
        KeywordSearchPredicate({"woman", "women"}, constant_weight=2),
        KeywordSearchPredicate({"ptsd"}, constant_weight=1),
        KeywordSearchPredicate({"therapy", "therapist"}, constant_weight=1),
        KeywordSearchPredicate(
            {"service"}, {"violence", "line", "abuse", "overcom"}, constant_weight=1
        ),
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
    return LinkScorer(15, 0.5, LINK_PREDICATES)


def get_page_scorer() -> PageScorer:
    SCOT_CHARITIES = read_csv_as_dict(__SCOT_CHARITIES_PATH)

    print("Loaded charities:", len(SCOT_CHARITIES))

    PAGE_PREDICATES = [
        KeywordTokenPredicate(
            {
                "victim",
                "victims",
                "victimizing",
                "victimization",
                "victimize",
                "victimized",
                "victimising",
                "victimisation",
                "victimise",
                "victimised",
            },
            {"abuse", "violence", "partner"},
            constant_weight=7,
            alias="VICTIM",
        ),
        KeywordTokenPredicate({"rape", "raped"}, constant_weight=10, alias="RAPE"),
        KeywordTokenPredicate(
            {"survive", "survivor", "survivors", "survival", "survived", "surviving"},
            {"abuse", "abusing", "violent", "violence", "trauma", "relationship"},
            constant_weight=4,
            alias="SURVIVOR",
        ),
        KeywordTokenPredicate({"referral"}, constant_weight=2, alias="REFERRAL"),
        KeywordTokenPredicate(
            {"sexual", "sexually"},
            {
                "abuse",
                "abused",
                "assault",
                "assaulted",
                "harassment",
                "harassed",
                "exploitation",
                "exploited",
                "violence",
            },
            constant_weight=8,
            alias="SEXUAL",
        ),
        KeywordTokenPredicate(
            {"homeless", "homelessness"}, constant_weight=2, alias="HOMELESS"
        ),
        KeywordTokenPredicate(
            {"shelter", "shelters"}, constant_weight=2, alias="SHELTER"
        ),
        KeywordTokenPredicate({"refuge", "refuges"}, constant_weight=3, alias="REFUGE"),
        KeywordTokenPredicate({"refugee"}, constant_weight=3, alias="REFUGEE"),
        KeywordTokenPredicate(
            {"domestic"},
            {"violence", "abuse", "abuser"},
            constant_weight=15,
            alias="DOMESTIC-ABUSE",
        ),
        KeywordTokenPredicate(
            {"suffer", "suffering", "suffers", "suffered"},
            constant_weight=1,
            alias="SUFFER",
        ),
        KeywordTokenPredicate(
            {"power", "powerless", "powerlessness"},
            {"relationship", "partner", "dynamic", "dynamics", "differential"},
            constant_weight=2,
            alias="POWER",
        ),
        KeywordTokenPredicate(
            {"women", "woman"},
            {
                "help",
                "helps",
                "helping",
                "aid",
                "aids",
                "aiding",
                "assist",
                "assists",
                "assisting",
            },
            constant_weight=2,
            alias="WOMAN",
        ),  # Not -hood
        KeywordTokenPredicate(
            {"neglect", "neglected"},
            {"partner", "adult", "child", "childhood", "children"},
            constant_weight=2,
            alias="NEGLECT",
        ),
        KeywordTokenPredicate(
            {"crisis"}, constant_weight=3, alias="CRISIS"
        ),  # Not crises
        KeywordTokenPredicate(
            {"lgbt", "lgbtq", "lgbtqi", "lgbtqia", "lgb", "grsm"},
            constant_weight=3,
            alias="LGBT",
        ),
        KeywordTokenPredicate({"emergency"}, constant_weight=2, alias="EMERGENCY"),
        KeywordTokenPredicate(
            {"advisor", "advisors"}, constant_weight=2, alias="ADVISOR"
        ),
        KeywordTokenPredicate(
            {
                "counsel",
                "counsellor",
                "counselor",
                "counsellors",
                "counselors",
                "counseling",
                "counselling",
            },
            {"abuse", "violence", "trauma", "health", "survivor"},
            constant_weight=3,
            alias="COUNSEL",
        ),
        KeywordTokenPredicate(
            {"therapy", "therapist", "therapists"}, constant_weight=2, alias="THERAPY"
        ),
        KeywordTokenPredicate(
            {"community", "communities"}, constant_weight=1, alias="COMMUNITY"
        ),
        KeywordTokenPredicate(
            {"harass", "harasses", "harassing", "harassment"},
            constant_weight=4,
            alias="HARASSMENT",
        ),
        KeywordTokenPredicate(
            {"sanctuary", "sanctuaries"}, constant_weight=4, alias="SANCTUARY"
        ),
        KeywordTokenPredicate(
            {"safehouse", "safehouses"}, constant_weight=5, alias="SAFEHOUSE"
        ),
        KeywordTokenPredicate(
            {"safe"}, {"room", "rooms"}, constant_weight=5, alias="SAFE-ROOM"
        ),
        KeywordTokenPredicate(
            {"trust", "trusts", "trusting", "trusted", "trustworthy"},
            constant_weight=2,
            alias="TRUST",
        ),
        KeywordTokenPredicate(
            {"charity"},
            {"reg", "registration", "number"},
            constant_weight=5,
            alias="CHARITY",
        ),
        KeywordTokenPredicate(
            {"marriage", "relationship"}, constant_weight=2, alias="RELATIONSHIP"
        ),
        KeywordTokenPredicate(
            {"marriage"},
            {"force", "forced", "trap", "trapped", "coerce", "coercion", "coerced"},
            constant_weight=9,
            alias="FORCED-MARRIAGE",
        ),
        KeywordTokenPredicate(
            {"donate", "donation", "donations", "fundraise", "fundraising"},
            constant_weight=2,
            alias="DONATION",
        ),
        KeywordTokenPredicate(
            {"trauma", "traumatic"}, constant_weight=5, alias="TRAUMA"
        ),  # Not traumatise
        KeywordTokenPredicate(
            {"confidential", "confidentiality", "confidentially"},
            constant_weight=4,
            alias="CONFIDENTIAL",
        ),
        KeywordTokenPredicate(
            {"helpline", "hotline"}, constant_weight=8, alias="HELPLINE"
        ),
        KeywordTokenPredicate(
            {"protection"},
            {"order", "orders"},
            constant_weight=5,
            alias="PROTECTION-ORDER",
        ),
        KeywordTokenPredicate(
            {"empowerment"},
            {"program", "programs", "programme", "programmes"},
            constant_weight=6,
            alias="EMPOWERMENT",
        ),
        KeywordTokenPredicate({"ptsd"}, constant_weight=5, alias="PTSD"),
        KeywordTokenPredicate(
            {"volunteer", "volunteers"}, constant_weight=1, alias="VOLUNTEER"
        ),
        KeywordTokenPredicate(
            {"stalking", "stalker"}, constant_weight=6, alias="STALKING"
        ),
        KeywordTokenPredicate(
            {"report", "reporting"},
            {"anonymous", "anonymously"},
            constant_weight=2,
            alias="ANONYMOUS-REPORTING",
        ),
        KeywordTokenPredicate({"duluth"}, {"model"}, constant_weight=5, alias="DULUTH"),
        KeywordTokenPredicate(
            {"restraining"}, {"order"}, constant_weight=5, alias="RESTRAINING-ORDER"
        ),
        KeywordTokenPredicate(
            {"reproduce", "reproductive"},
            {"coerced", "coerce", "coercing", "coercion"},
            constant_weight=7,
            alias="REPRODUCTIVE-COERCION",
        ),
        # # Penalise news sites
        KeywordTokenPredicate(
            {
                # Many DV sites have "news" section, so back this up with more keywords
                "weather",
                "politics",
                "sport",
                "newsroom",
                "news",
            },
            {
                "breaking",
                "business",
                "column",
                "columnist",
                "editor",
                "editorial",
                "headline",
                "headlines",
                "coverage",
            },
            required_occurrences=2,
            constant_weight=-10,
            alias="SUB-NEWS",
        ),
        # Penalise forums
        KeywordTokenPredicate(
            {
                "forum",
                "forums",
                "board",
                "boards",
                "thread",
                "threads",
                "featured",
                "trending",
                "communities",
                "community",
                "popular",
                "modified",
            },
            required_occurrences=3,
            constant_weight=-10,
            alias="SUB-FORUM",
        ),
        # Penalise developer websites
        KeywordTokenPredicate(
            {
                "software",
                "docs",
                "devops",
                "cloud",
                "api",
                "sdk",
                "sdks",
                "documentation",
                "github",
                "gitlab",
                "bitbucket",
            },
            required_occurrences=2,
            constant_weight=-10,
            alias="SUB-DEV",
        ),
        # Penalise commercial websites
        KeywordTokenPredicate(
            {
                "shop",
                "store",
                "company",
                "enterprise",
                "buy",
                "purchase",
                "purchases",
                "product",
                "products",
                "pricing",
                "discount",
                "discounts",
                "sale",
                "sales",
                "coupon",
                "coupons",
                "promotional",  # Not promotion
            },
            required_occurrences=2,
            constant_weight=-10,
            alias="SUB-COMMERCIAL",
        ),
        KeywordTokenPredicate(
            set(SCOT_CHARITIES.keys()), constant_weight=20, alias="SCOT-CHARITY"
        ),
        HtmlPredicate(_has_quick_exit, constant_weight=10, alias="QUICK-EXIT"),
    ]

    return PageScorer(25, -0.01, 0, PAGE_PREDICATES)

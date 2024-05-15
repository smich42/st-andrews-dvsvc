from math import inf
import os
from bs4 import BeautifulSoup

from heuristics.helpers import read_csv_as_dict
from heuristics.scorers import (
    HtmlPredicate,
    RegexPredicate,
    KeywordPredicate,
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
                    "fast",
                ]
            ):
                matches += 1
            if any(
                w in words
                for w in ["site", "website", "page", "webpage", "history", "visit"]
            ):
                matches += 1

    return matches >= NECESSARY_MATCHES


def get_link_scorer() -> LinkScorer:
    LINK_PREDICATES = [
        # Weigh words lower than before, particularly context-dependent ones, as we expect fewer overall matches, giving us less contextual understanding.
        RegexPredicate({r"victim"}, constant_weight=2),
        RegexPredicate({r"rape"}, constant_weight=2),
        RegexPredicate({r"abus"}, constant_weight=3),
        RegexPredicate({r"assault", r"assaulted"}, {r"sexual"}, constant_weight=3),
        RegexPredicate({r"surviv"}, constant_weight=2),
        RegexPredicate({r"homeless"}, constant_weight=1),
        RegexPredicate({r"shelter"}, constant_weight=2),
        RegexPredicate({r"refuge"}, constant_weight=2),
        RegexPredicate(
            {r"domestic"}, {r"violence", r"abuse", r"abuser"}, constant_weight=6
        ),
        RegexPredicate({r"agenc"}, constant_weight=1),
        RegexPredicate({r"organisation", r"organization"}, constant_weight=1),
        RegexPredicate({r"neglect"}, {r"partner", r"child"}, constant_weight=2),
        RegexPredicate({r"crisis"}, {r"line", r"centre"}, constant_weight=4),
        RegexPredicate({r"crisis"}, {r"abuse", r"volence"}, constant_weight=3),
        RegexPredicate({r"lgbt", r"grsm"}, constant_weight=2),
        RegexPredicate({r"emergency"}, constant_weight=2),
        RegexPredicate({r"advisor"}, constant_weight=2),
        RegexPredicate({r"counsel"}, constant_weight=1),
        RegexPredicate({r"empower"}, constant_weight=2),
        RegexPredicate({r"woman", r"women"}, constant_weight=2),
        RegexPredicate({r"ptsd"}, constant_weight=1),
        RegexPredicate({r"therapy", r"therapist"}, constant_weight=1),
        RegexPredicate(
            {r"service"}, {r"violence", r"line", r"abuse"}, constant_weight=1
        ),
        RegexPredicate({r"communit"}, constant_weight=1),
        RegexPredicate({r"relationship"}, constant_weight=1),
        RegexPredicate({r"coalition"}, constant_weight=1),
        RegexPredicate({r"violence"}, constant_weight=2),
        RegexPredicate({r"harass"}, constant_weight=3),
        RegexPredicate({r"sanctuar"}, constant_weight=3),
        RegexPredicate({r"haven", r"havens"}, constant_weight=2),
        RegexPredicate({r"neglect"}, constant_weight=2),
        RegexPredicate({r"trust"}, constant_weight=2),
        RegexPredicate({r"house", r"housing"}, constant_weight=1),
        RegexPredicate({r"charit"}, constant_weight=3),
        RegexPredicate({r"foundation"}, constant_weight=2),
        RegexPredicate({r"marriage"}, {r"force"}, constant_weight=4),
        RegexPredicate({r"trauma"}, constant_weight=4),
        RegexPredicate({r"confidential"}, constant_weight=2),
        RegexPredicate({r"helpline"}, constant_weight=3),
        RegexPredicate({r"\.co\.uk($|/)"}, constant_weight=0, scaling_weight=0.6),
        RegexPredicate({r"\.ac\.uk($|/)"}, constant_weight=0, scaling_weight=0.8),
        RegexPredicate({r"\.gov\.uk($|/)"}, constant_weight=5, scaling_weight=1.2),
        RegexPredicate({r"\.gov\.scot($|/)"}, constant_weight=5, scaling_weight=1.2),
        RegexPredicate({r"\.org($|/)"}, constant_weight=2, scaling_weight=1.4),
        RegexPredicate({r"\.org\.uk($|/)"}, constant_weight=5, scaling_weight=1.4),
        RegexPredicate({r"\.com($|/)"}, constant_weight=-5, scaling_weight=0.8),
        RegexPredicate({r"\.co.uk($|/)"}, constant_weight=-3, scaling_weight=0.8),
        RegexPredicate({r"\.gov($|/)"}, constant_weight=-inf),
        RegexPredicate({r"\.edu($|/)"}, constant_weight=-inf),
        RegexPredicate({r"\.au($|/)"}, constant_weight=-inf),
        RegexPredicate({r"\.nz($|/)"}, constant_weight=-inf),
        RegexPredicate({r"\.ie($|/)"}, constant_weight=-inf),
        RegexPredicate({r"\.ca($|/)"}, constant_weight=-inf),
        RegexPredicate({r"\.us($|/)"}, constant_weight=-inf),
        RegexPredicate({r"\.jm($|/)"}, constant_weight=-inf),
        RegexPredicate({r"\.bb($|/)"}, constant_weight=-inf),
        RegexPredicate({r"\.tt($|/)"}, constant_weight=-inf),
        RegexPredicate({r"\.ng($|/)"}, constant_weight=-inf),
        RegexPredicate({r"\.gy($|/)"}, constant_weight=-inf),
        RegexPredicate({r"\.bz($|/)"}, constant_weight=-inf),
    ]
    return LinkScorer(25, 0.2, LINK_PREDICATES)


def get_page_scorer() -> PageScorer:
    SCOT_CHARITIES = read_csv_as_dict(__SCOT_CHARITIES_PATH)

    print("Loaded charities:", len(SCOT_CHARITIES))

    PAGE_PREDICATES = [
        KeywordPredicate(
            set(SCOT_CHARITIES.keys()),
            constant_weight=3,
            scaling_weight=1.2,
            alias="SCOT-CHARITY",
        ),
        KeywordPredicate(
            {"domestic"},
            {"violence", "abuse", "abuser", "assault"},
            {"service", "services", "support", "help", "helpline", "hotline"},
            constant_weight=10,
            scaling_weight=1.5,
            alias="DOMESTIC-ABUSE-SERVICE",
        ),
        KeywordPredicate(
            {"intimate", "gender"},
            {"partner", "based"},
            {"violence", "abuse"},
            constant_weight=9,
            scaling_weight=1.3,
            alias="GENDER-ABUSE",
        ),
        KeywordPredicate(
            {"sexual", "sexually"},
            {
                "abuse",
                "abused",
                "abusive",
                "assault",
                "assaulted",
                "harassment",
                "harassed",
                "exploitation",
                "exploited",
                "violence",
            },
            constant_weight=8,
            scaling_weight=1.2,
            alias="SEXUAL-VIOLENCE",
        ),
        KeywordPredicate(
            {"rape", "raped"}, constant_weight=8, scaling_weight=1.1, alias="RAPE"
        ),
        KeywordPredicate(
            {
                # Avoid American spelling
                "victim",
                "victims",
                "victimising",
                "victimisation",
                "victimise",
                "victimised",
            },
            {"abuse", "violence", "partner"},
            constant_weight=7,
            alias="VICTIM",
        ),
        KeywordPredicate(
            {"survive", "survivor", "survivors", "survival", "survived", "surviving"},
            {
                "abuse",
                "abusing",
                "abusive",
                "violent",
                "violence",
                "trauma",
                "relationship",
                "assistance",
                "mindfulness",
            },
            constant_weight=4,
            alias="SURVIVOR",
        ),
        KeywordPredicate(
            {"trafficking"},
            constant_weight=5,
            alias="TRAFFICKING",
        ),
        # Not "modern slavery" because "statement on modern slavery" is a common phrase
        KeywordPredicate(
            {"recovery"},
            {"workshop", "workshops", "program", "programs", "programme", "programmes"},
            constant_weight=3,
        ),
        KeywordPredicate({"referral"}, constant_weight=2, alias="REFERRAL"),
        KeywordPredicate(
            {"homeless", "homelessness"}, constant_weight=1, alias="HOMELESS"
        ),
        KeywordPredicate(
            {"housing"}, {"assistance", "aid"}, constant_weight=3, alias="HOUSING-AID"
        ),
        KeywordPredicate(
            {"safe"}, {"shelter", "shelters"}, constant_weight=2, alias="SHELTER"
        ),
        KeywordPredicate({"refuge", "refuges"}, constant_weight=4, alias="REFUGE"),
        KeywordPredicate({"refugee"}, constant_weight=2, alias="REFUGEE"),
        KeywordPredicate(
            {"suffer", "suffering", "suffers", "suffered"},
            constant_weight=1,
            alias="SUFFER",
        ),
        KeywordPredicate(
            {"mandatory"},
            {"arrest"},
            {"policy"},
            constant_weight=5,
            alias="MANDATORY-ARREST-POLICY",
        ),
        KeywordPredicate(
            {"power", "powerless", "powerlessness"},
            {"relationship", "partner", "dynamic", "dynamics", "differential"},
            constant_weight=4,
            alias="POWER",
        ),
        KeywordPredicate(
            {"cohabitation"}, {"effect"}, constant_weight=4, alias="COHABITATION-EFFECT"
        ),
        KeywordPredicate(
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
            constant_weight=3,
            alias="WOMAN",
        ),
        KeywordPredicate(
            {"neglect", "neglected"},
            {"partner", "adult", "child", "childhood", "children"},
            constant_weight=2,
            alias="NEGLECT",
        ),
        KeywordPredicate(
            {"crisis"}, {"intervention", "support"}, constant_weight=4, alias="CRISIS"
        ),
        KeywordPredicate(
            {"lgbt", "lgbtq", "lgbtqi", "lgbtqia", "lgb", "grsm"},
            constant_weight=2,
            alias="LGBT",
        ),
        KeywordPredicate(
            {"advisor", "advisors", "advice"}, constant_weight=1, alias="ADVICE"
        ),
        KeywordPredicate(
            {"outreach"},
            {"program", "programs", "programme", "programmes", "service", "services"},
            constant_weight=3,
            alias="OUTREACH",
        ),
        KeywordPredicate(
            {"equality"},
            {"advocacy", "advocate", "advocates"},
            constant_weight=3,
            alias="EQUALITY-ADVOCATE",
        ),
        KeywordPredicate(
            {"police"},
            {"liaison"},
            constant_weight=2,
            alias="POLICE-LIAISON",
        ),
        KeywordPredicate(
            {"court"},
            {"support", "supported"},
            constant_weight=2,
            alias="COURT-SUPPORT",
        ),
        KeywordPredicate(
            {"abuser"},
            {"intervention"},
            {"service", "services", "programme", "programmes", "program", "programs"},
            constant_weight=6,
            alias="ABUSER-INTERVENTION",
        ),
        KeywordPredicate(
            {"economic", "economically", "financial", "financially"},
            {"empower", "empowerment", "empowered"},
            constant_weight=2,
            alias="ECONOMIC-EMPOWERMENT",
        ),
        KeywordPredicate(
            {"multilingual"},
            {"service", "services", "support"},
            constant_weight=1,
            alias="MULTILINGUAL",
        ),
        KeywordPredicate(
            {"cultural", "cultures", "culturally"},
            {"sensitive", "sensitivity"},
            constant_weight=1,
            alias="CULTURE-SENSITIVE",
        ),
        KeywordPredicate(
            {"legal"}, {"aid", "advice", "advocacy"}, constant_weight=2, alias="LEGAL"
        ),
        KeywordPredicate(
            {"emotional"}, {"support"}, constant_weight=1, alias="EMOTIONAL-SUPPORT"
        ),
        KeywordPredicate(
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
            constant_weight=5,
            alias="COUNSELLING",
        ),
        KeywordPredicate(
            {"therapy", "therapist", "therapists"}, constant_weight=1, alias="THERAPY"
        ),
        KeywordPredicate(
            {"community", "communities"}, constant_weight=1, alias="COMMUNITY"
        ),
        KeywordPredicate(
            {"harass", "harasses", "harassing", "harassment"},
            constant_weight=4,
            alias="HARASSMENT",
        ),
        KeywordPredicate(
            {"sanctuary", "sanctuaries"}, constant_weight=2, alias="SANCTUARY"
        ),
        KeywordPredicate(
            {"safehouse", "safehouses"}, constant_weight=3, alias="SAFEHOUSE"
        ),
        KeywordPredicate(
            {"safe"}, {"room", "rooms"}, constant_weight=3, alias="SAFE-ROOM"
        ),
        KeywordPredicate(
            {"coercive"}, {"control"}, {"support"}, constant_weight=2, alias="HAVEN"
        ),
        KeywordPredicate(
            {"safety", "escape"},
            {"plan", "planning"},
            constant_weight=1,
            alias="SAFETY-PLAN",
        ),
        KeywordPredicate(
            {"coercive"},
            {"control"},
            {"support", "supporting", "supports"},
            constant_weight=5,
            alias="COERCIVE-CONTROL",
        ),
        KeywordPredicate(
            {"cycle"},
            {"violence"},
            constant_weight=1,
            alias="VIOLENCE-CYCLE",
        ),
        KeywordPredicate(
            {"power"},
            {"control"},
            {"wheel"},
            constant_weight=5,
            alias="POWER-CONTROL-WHEEL",
        ),
        KeywordPredicate(
            {"social"},
            {"learning"},
            {"theory"},
            constant_weight=1,
            alias="SOCIAL-LEARNING-THEORY",
        ),
        KeywordPredicate(
            {"trust", "trusts", "trusting", "trusted"},
            constant_weight=1,
            alias="TRUST",
        ),
        KeywordPredicate(
            {"charity"},
            {"reg", "registration", "number"},
            constant_weight=3,
            alias="CHARITY",
        ),
        KeywordPredicate(
            {"marriage"},
            {"force", "forced", "trap", "trapped", "coerce", "coercion", "coerced"},
            constant_weight=6,
            alias="FORCED-MARRIAGE",
        ),
        KeywordPredicate(
            {"abusive"},
            {"marriage", "relationship"},
            constant_weight=6,
            alias="ABUSIVE-RELATIONSHIP",
        ),
        KeywordPredicate(
            {"donate", "donation", "donations", "fundraise", "fundraising"},
            constant_weight=2,
            alias="DONATION",
        ),
        KeywordPredicate(
            {"trauma", "traumatic"},
            {"recover", "recovery", "recovering", "care"},
            constant_weight=5,
            alias="TRAUMA",
        ),
        KeywordPredicate(
            {"confidential", "confidentiality", "confidentially"},
            constant_weight=2,
            alias="CONFIDENTIAL",
        ),
        KeywordPredicate({"helpline", "hotline"}, constant_weight=8, alias="HELPLINE"),
        KeywordPredicate(
            {"protection"},
            {"order", "orders"},
            constant_weight=5,
            alias="PROTECTION-ORDER",
        ),
        KeywordPredicate(
            {"empowerment"},
            {"program", "programs", "programme", "programmes"},
            constant_weight=3,
            alias="EMPOWERMENT",
        ),
        KeywordPredicate({"ptsd"}, constant_weight=3, alias="PTSD"),
        KeywordPredicate(
            {"volunteer", "volunteers"}, constant_weight=1, alias="VOLUNTEER"
        ),
        KeywordPredicate({"stalking", "stalker"}, constant_weight=4, alias="STALKING"),
        KeywordPredicate(
            {"gendered"},
            {"crime", "violence", "abuse"},
            constant_weight=4,
            alias="GENDERED-CRIME",
        ),
        KeywordPredicate(
            {"symbolic"},
            {"interactionism"},
            constant_weight=3,
            alias="SYMBOLIC-INTERACTIONISM",
        ),
        KeywordPredicate(
            {"report", "reporting"},
            {"anonymous", "anonymously"},
            constant_weight=2,
            alias="ANONYMOUS-REPORTING",
        ),
        KeywordPredicate({"duluth"}, {"model"}, constant_weight=5, alias="DULUTH"),
        KeywordPredicate(
            {"restraining"}, {"order"}, constant_weight=4, alias="RESTRAINING-ORDER"
        ),
        KeywordPredicate(
            {"reproduce", "reproductive"},
            {"coerced", "coerce", "coercing", "coercion"},
            constant_weight=7,
            alias="REPRODUCTIVE-COERCION",
        ),
        # Penalise news sites
        KeywordPredicate(
            {
                # Many DV sites have "news" section, so back this up with more keywords
                "newsroom",
                "newspaper",
                "newspapers",
                "news",
                "journalist",
                "columnist",
                "editorial",
                "editor",
                "headline",
                "headlines",
            },
            {
                "weather",
                "politics",
                "sport",
                "breaking",
                "business",
                "entertainment",
                "lifestyle",
                "coverage",
                "exclusive",
            },
            required_occurrences_per_set=2,
            constant_weight=-10,
            alias="SUB-NEWS",
        ),
        # Penalise forums
        KeywordPredicate(
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
            required_occurrences_per_set=3,
            constant_weight=-10,
            alias="SUB-FORUM",
        ),
        # Penalise developer websites
        KeywordPredicate(
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
            required_occurrences_per_set=2,
            constant_weight=-10,
            scaling_weight=0.5,
            alias="SUB-DEV",
        ),
        # Penalise commercial websites
        KeywordPredicate(
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
            required_occurrences_per_set=2,
            constant_weight=-10,
            scaling_weight=0.6,
            alias="SUB-COMMERCIAL",
        ),
        # Penalise academic websites
        KeywordPredicate(
            {
                "study",
                "studies",
                "academic",
                "academics",
                "journal",
                "journals",
                "thesis",
                "theses",
                "professor",
                "lecturer",
                "scholar",
                "scholars",
                "researchgate",
                "academia",
                "scholarly",
                "citation",
                "citations",
                "jstor",
                "arxiv",
                "syllabus",
            },
            required_occurrences_per_set=2,
            constant_weight=-5,
            scaling_weight=0.7,
            alias="SUB-ACADEMIC",
        ),
        HtmlPredicate(_has_quick_exit, constant_weight=10, alias="QUICK-EXIT"),
        RegexPredicate({r"501\(c\)\(3\)"}, constant_weight=-15, alias="501-3-C"),
    ]

    return PageScorer(
        predicates=PAGE_PREDICATES, percentile_90=30, word_count_factor=-0.01
    )

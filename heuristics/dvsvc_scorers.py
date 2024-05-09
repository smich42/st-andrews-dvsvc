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
        KeywordSearchPredicate({"victim"}, constant_weight=2),
        KeywordSearchPredicate({"rape"}, constant_weight=2),
        KeywordSearchPredicate({"abus"}, constant_weight=3),
        KeywordSearchPredicate({"assault", "assaulted"}, {"sexual"}, constant_weight=3),
        KeywordSearchPredicate({"surviv"}, constant_weight=2),
        KeywordSearchPredicate({"homeless"}, constant_weight=1),
        KeywordSearchPredicate({"shelter"}, constant_weight=2),
        KeywordSearchPredicate({"refuge"}, constant_weight=2),
        KeywordSearchPredicate(
            {"domestic"}, {"violence", "abuse", "abuser"}, constant_weight=6
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
    return LinkScorer(20, 0.2, LINK_PREDICATES)


def get_page_scorer() -> PageScorer:
    SCOT_CHARITIES = read_csv_as_dict(__SCOT_CHARITIES_PATH)

    print("Loaded charities:", len(SCOT_CHARITIES))

    PAGE_PREDICATES = [
        KeywordTokenPredicate(
            set(SCOT_CHARITIES.keys()),
            constant_weight=3,
            scaling_weight=1.2,
            alias="SCOT-CHARITY",
        ),
        KeywordTokenPredicate(
            {"domestic"},
            {"violence", "abuse", "abuser", "assault"},
            constant_weight=10,
            scaling_weight=1.5,
            alias="DOMESTIC-ABUSE-SERVICE",
        ),
        KeywordTokenPredicate(
            {"intimate", "gender"},
            {"partner", "based"},
            {"violence", "abuse"},
            constant_weight=9,
            scaling_weight=1.3,
            alias="GENDER-ABUSE",
        ),
        KeywordTokenPredicate(
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
        KeywordTokenPredicate(
            {"rape", "raped"}, constant_weight=8, scaling_weight=1.1, alias="RAPE"
        ),
        KeywordTokenPredicate(
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
        KeywordTokenPredicate(
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
        KeywordTokenPredicate(
            {"trafficking"},
            constant_weight=5,
            alias="TRAFFICKING",
        ),
        # Not "modern slavery" because "statement on modern slavery" is a common phrase
        KeywordTokenPredicate(
            {"recovery"},
            {"workshop", "workshops", "program", "programs", "programme", "programmes"},
            constant_weight=3,
        ),
        KeywordTokenPredicate({"referral"}, constant_weight=2, alias="REFERRAL"),
        KeywordTokenPredicate(
            {"homeless", "homelessness"}, constant_weight=1, alias="HOMELESS"
        ),
        KeywordTokenPredicate(
            {"housing"}, {"assistance", "aid"}, constant_weight=3, alias="HOUSING-AID"
        ),
        KeywordTokenPredicate(
            {"safe"}, {"shelter", "shelters"}, constant_weight=2, alias="SHELTER"
        ),
        KeywordTokenPredicate({"refuge", "refuges"}, constant_weight=4, alias="REFUGE"),
        KeywordTokenPredicate({"refugee"}, constant_weight=2, alias="REFUGEE"),
        KeywordTokenPredicate(
            {"suffer", "suffering", "suffers", "suffered"},
            constant_weight=1,
            alias="SUFFER",
        ),
        KeywordTokenPredicate(
            {"mandatory"},
            {"arrest"},
            {"policy"},
            constant_weight=5,
            alias="MANDATORY-ARREST-POLICY",
        ),
        KeywordTokenPredicate(
            {"power", "powerless", "powerlessness"},
            {"relationship", "partner", "dynamic", "dynamics", "differential"},
            constant_weight=4,
            alias="POWER",
        ),
        KeywordTokenPredicate(
            {"cohabitation"}, {"effect"}, constant_weight=4, alias="COHABITATION-EFFECT"
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
            constant_weight=3,
            alias="WOMAN",
        ),
        KeywordTokenPredicate(
            {"neglect", "neglected"},
            {"partner", "adult", "child", "childhood", "children"},
            constant_weight=2,
            alias="NEGLECT",
        ),
        KeywordTokenPredicate(
            {"crisis"}, {"intervention", "support"}, constant_weight=4, alias="CRISIS"
        ),
        KeywordTokenPredicate(
            {"lgbt", "lgbtq", "lgbtqi", "lgbtqia", "lgb", "grsm"},
            constant_weight=2,
            alias="LGBT",
        ),
        KeywordTokenPredicate(
            {"advisor", "advisors", "advice"}, constant_weight=1, alias="ADVICE"
        ),
        KeywordTokenPredicate(
            {"outreach"},
            {"program", "programs", "programme", "programmes", "service", "services"},
            constant_weight=3,
            alias="OUTREACH",
        ),
        KeywordTokenPredicate(
            {"equality"},
            {"advocacy", "advocate", "advocates"},
            constant_weight=3,
            alias="EQUALITY-ADVOCATE",
        ),
        KeywordTokenPredicate(
            {"police"},
            {"liaison"},
            constant_weight=2,
            alias="POLICE-LIAISON",
        ),
        KeywordTokenPredicate(
            {"court"},
            {"support", "supported"},
            constant_weight=2,
            alias="COURT-SUPPORT",
        ),
        KeywordTokenPredicate(
            {"abuser"},
            {"intervention"},
            {"service", "services", "programme", "programmes", "program", "programs"},
            constant_weight=6,
            alias="ABUSER-INTERVENTION",
        ),
        KeywordTokenPredicate(
            {"economic", "economically", "financial", "financially"},
            {"empower", "empowerment", "empowered"},
            constant_weight=2,
            alias="ECONOMIC-EMPOWERMENT",
        ),
        KeywordTokenPredicate(
            {"multilingual"},
            {"service", "services", "support"},
            constant_weight=1,
            alias="MULTILINGUAL",
        ),
        KeywordTokenPredicate(
            {"cultural", "cultures", "culturally"},
            {"sensitive", "sensitivity"},
            constant_weight=1,
            alias="CULTURE-SENSITIVE",
        ),
        KeywordTokenPredicate(
            {"legal"}, {"aid", "advice", "advocacy"}, constant_weight=2, alias="LEGAL"
        ),
        KeywordTokenPredicate(
            {"emotional"}, {"support"}, constant_weight=1, alias="EMOTIONAL-SUPPORT"
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
            constant_weight=5,
            alias="COUNSELLING",
        ),
        KeywordTokenPredicate(
            {"therapy", "therapist", "therapists"}, constant_weight=1, alias="THERAPY"
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
            {"sanctuary", "sanctuaries"}, constant_weight=2, alias="SANCTUARY"
        ),
        KeywordTokenPredicate(
            {"safehouse", "safehouses"}, constant_weight=3, alias="SAFEHOUSE"
        ),
        KeywordTokenPredicate(
            {"safe"}, {"room", "rooms"}, constant_weight=3, alias="SAFE-ROOM"
        ),
        KeywordTokenPredicate(
            {"coercive"}, {"control"}, {"support"}, constant_weight=2, alias="HAVEN"
        ),
        KeywordTokenPredicate(
            {"safety", "escape"},
            {"plan", "planning"},
            constant_weight=1,
            alias="SAFETY-PLAN",
        ),
        KeywordTokenPredicate(
            {"coercive"},
            {"control"},
            {"support", "supporting", "supports"},
            constant_weight=5,
            alias="COERCIVE-CONTROL",
        ),
        KeywordTokenPredicate(
            {"cycle"},
            {"violence"},
            constant_weight=1,
            alias="VIOLENCE-CYCLE",
        ),
        KeywordTokenPredicate(
            {"power"},
            {"control"},
            {"wheel"},
            constant_weight=5,
            alias="POWER-CONTROL-WHEEL",
        ),
        KeywordTokenPredicate(
            {"social"},
            {"learning"},
            {"theory"},
            constant_weight=1,
            alias="SOCIAL-LEARNING-THEORY",
        ),
        KeywordTokenPredicate(
            {"trust", "trusts", "trusting", "trusted"},
            constant_weight=1,
            alias="TRUST",
        ),
        KeywordTokenPredicate(
            {"charity"},
            {"reg", "registration", "number"},
            constant_weight=3,
            alias="CHARITY",
        ),
        KeywordTokenPredicate(
            {"marriage"},
            {"force", "forced", "trap", "trapped", "coerce", "coercion", "coerced"},
            constant_weight=6,
            alias="FORCED-MARRIAGE",
        ),
        KeywordTokenPredicate(
            {"abusive"},
            {"marriage", "relationship"},
            constant_weight=6,
            alias="ABUSIVE-RELATIONSHIP",
        ),
        KeywordTokenPredicate(
            {"donate", "donation", "donations", "fundraise", "fundraising"},
            constant_weight=2,
            alias="DONATION",
        ),
        KeywordTokenPredicate(
            {"trauma", "traumatic"},
            {"recover", "recovery", "recovering", "care"},
            constant_weight=5,
            alias="TRAUMA",
        ),
        KeywordTokenPredicate(
            {"confidential", "confidentiality", "confidentially"},
            constant_weight=2,
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
            constant_weight=3,
            alias="EMPOWERMENT",
        ),
        KeywordTokenPredicate({"ptsd"}, constant_weight=3, alias="PTSD"),
        KeywordTokenPredicate(
            {"volunteer", "volunteers"}, constant_weight=1, alias="VOLUNTEER"
        ),
        KeywordTokenPredicate(
            {"stalking", "stalker"}, constant_weight=4, alias="STALKING"
        ),
        KeywordTokenPredicate(
            {"gendered"},
            {"crime", "violence", "abuse"},
            constant_weight=4,
            alias="GENDERED-CRIME",
        ),
        KeywordTokenPredicate(
            {"symbolic"},
            {"interactionism"},
            constant_weight=3,
            alias="SYMBOLIC-INTERACTIONISM",
        ),
        KeywordTokenPredicate(
            {"report", "reporting"},
            {"anonymous", "anonymously"},
            constant_weight=2,
            alias="ANONYMOUS-REPORTING",
        ),
        KeywordTokenPredicate({"duluth"}, {"model"}, constant_weight=5, alias="DULUTH"),
        KeywordTokenPredicate(
            {"restraining"}, {"order"}, constant_weight=4, alias="RESTRAINING-ORDER"
        ),
        KeywordTokenPredicate(
            {"reproduce", "reproductive"},
            {"coerced", "coerce", "coercing", "coercion"},
            constant_weight=7,
            alias="REPRODUCTIVE-COERCION",
        ),
        # Penalise news sites
        KeywordTokenPredicate(
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
            required_occurrences_per_set=3,
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
            required_occurrences_per_set=2,
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
            required_occurrences_per_set=2,
            constant_weight=-10,
            alias="SUB-COMMERCIAL",
        ),
        # Penalise academic websites
        KeywordTokenPredicate(
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
            constant_weight=-10,
            alias="SUB-ACADEMIC",
        ),
        HtmlPredicate(_has_quick_exit, constant_weight=10, alias="QUICK-EXIT"),
    ]

    return PageScorer(
        predicates=PAGE_PREDICATES,
        percentile_90=30,
        word_count_factor=-0.01,
        topic_count_factor=0,
    )

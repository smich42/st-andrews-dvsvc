from typing import Callable
from bs4 import BeautifulSoup
from tld import get_tld
import re

from helpers import logistic00


class Predicate:
    constant_weight: float
    scaling_weight: float
    apply: Callable[[str | set[str] | BeautifulSoup], bool]


class HtmlPredicate(Predicate):
    def __init__(self, apply: Callable[[BeautifulSoup], bool], constant_weight: float = 0., scaling_weight: float = 1.):
        self.apply = apply
        self.constant_weight = constant_weight
        self.scaling_weight = scaling_weight

    def __str__(self) -> str:
        return f"HtmlPredicate({self.apply})"


class KeywordPredicate(Predicate):
    keyword_sets: list[set[str]]

    def __init__(self, *keyword_sets: set[str], constant_weight: float = 0., scaling_weight: float = 1.):
        self.keyword_sets = keyword_sets
        self.constant_weight = constant_weight
        self.scaling_weight = scaling_weight

        self.apply = lambda page_words: all(any(keyword in page_words
                                                for keyword in keyword_set)
                                            for keyword_set in self.keyword_sets)

    def __str__(self):
        return "KeywordPredicate(" + " ".join([f"{{{next(iter(keyword_set))} ... }}" for keyword_set in self.keyword_sets]) + ")"

# N.B. Slower as it searches text rather than set.


class PartialKeywordPredicate(Predicate):
    keyword_sets: list[set[str]]

    def __init__(self, *keyword_sets: set[str], constant_weight: float = 0., scaling_weight: float = 1.):
        self.keywords_sets = keyword_sets
        self.constant_weight = constant_weight
        self.scaling_weight = scaling_weight

        self.apply = lambda page_text: all(any(keyword in page_text
                                               for keyword in keyword_set)
                                           for keyword_set in self.keyword_sets)

    def __str__(self):
        return "PartialKeywordPredicate(" + " ".join([f"{{{next(iter(keyword_set))} ... }}" for keyword_set in self.keyword_sets]) + ")"


class TldPredicate(Predicate):
    tld: str  # e.g. "org" or "gov.uk"

    def __init__(self, tld: str, constant_weight: float = 0., scaling_weight: float = 1.):
        if tld.startswith("."):  # Remove leading full stop
            tld = tld[1:]

        self.tld = tld
        self.constant_weight = constant_weight
        self.scaling_weight = scaling_weight

        self.apply = lambda tld: self.tld == tld

    def __str__(self):
        return f"TldPredicate({self.tld})"


class Score:
    def __init__(self, value: float, matched_predicates: list[Predicate]):
        self.value = value
        self.matched_predicates = matched_predicates


class _ScoreBuilder:
    def __init__(self):
        self.value = 0
        self.matched_predicates = []

    def compound(self, predicate: Predicate) -> None:
        self.apply_weights(predicate.constant_weight, predicate.scaling_weight)
        self.matched_predicates.append(predicate)

    def apply_weights(self, constant_weight: float, scaling_weight: float) -> None:
        self.value *= constant_weight
        self.value *= scaling_weight

    def get_score(self, percentile_90: float) -> Score:
        return Score(logistic00(self.value, (percentile_90, 0.9)),
                     self.matched_predicates)


class PageScorer:
    def __init__(self, percentile_90: float, predicates: list[HtmlPredicate | KeywordPredicate]):
        self.percentile_90 = percentile_90  # 20 is good
        self.predicates = predicates

    def get_score(self, page_html: str) -> Score:
        soup = BeautifulSoup(page_html, "html.parser")

        page_text = self._clean_text(soup.get_text())
        page_words = set(page_text.split(" "))

        sb = _ScoreBuilder()

        for predicate in self.predicates:
            is_match = predicate.apply(soup) \
                if type(predicate) is HtmlPredicate \
                else predicate.apply(page_words)

            if is_match:
                sb.compound(predicate)

        return sb.get_score(self.percentile_90)

    def _clean_text(self, page_text: str) -> str:
        page_text = page_text.strip().lower()
        page_text = re.sub(
            r"[`!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?~]+", " ", page_text)
        page_text = re.sub(r"\s+", " ", page_text)
        return page_text


class URLScorer:
    def __init__(self, predicates: list[TldPredicate | PartialKeywordPredicate], percentile_90: float, parent_factor: float):
        self.predicates = predicates
        self.percentile_90 = percentile_90  # 5 is good
        self.parent_factor = parent_factor  # 0.2 is good

    def get_score(self, url: str, parent_page_score: int) -> Score:
        url = url.lower()
        tld = get_tld(url, fail_silently=True)

        sb = _ScoreBuilder()

        for predicate in self.predicates:
            if type(predicate) is TldPredicate and tld:
                is_match = predicate.apply(tld)
            elif type(predicate) is PartialKeywordPredicate:
                is_match = predicate.apply(url)

            if is_match:
                sb.compound(predicate)

        sb.apply_weights(self.parent_factor * parent_page_score, 1.)

        return sb.get_score(self.percentile_90)

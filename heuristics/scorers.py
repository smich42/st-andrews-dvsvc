from typing import Callable
from bs4 import BeautifulSoup
from tld import get_tld
from typing import Any
import re

from heuristics.helpers import logistic00


class Predicate:
    constant_weight: float
    scaling_weight: float
    topic: int
    apply: Callable[[Any], bool]


class HtmlPredicate(Predicate):
    def __init__(
        self,
        apply: Callable[[BeautifulSoup], bool],
        constant_weight: float = 0.0,
        scaling_weight: float = 1.0,
        topic: int = 0,
    ):
        self.apply = apply
        self.constant_weight = constant_weight
        self.scaling_weight = scaling_weight
        self.topic = topic

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.apply})"


class KeywordPredicate(Predicate):
    keyword_sets: list[set[str]]  # An instance of each must occur

    def __str__(self):
        return (
            self.__class__.__name__
            + "("
            + " ".join(
                [
                    f"{{{next(iter(keyword_set))} ... }}"
                    for keyword_set in self.keyword_sets
                ]
            )
            + ")"
        )


class KeywordTokenPredicate(Predicate):
    def __init__(
        self,
        *keyword_sets: set[str],
        constant_weight: float = 0.0,
        scaling_weight: float = 1.0,
        topic: int = 0,
    ):
        self.keyword_sets = keyword_sets
        self.constant_weight = constant_weight
        self.scaling_weight = scaling_weight
        self.topic = topic

        self.apply = lambda page_words: all(
            any(keyword in page_words for keyword in keyword_set)
            for keyword_set in self.keyword_sets
        )


class KeywordSearchPredicate(Predicate):
    # N.B. Slower as it searches text rather than set.
    def __init__(
        self,
        *keyword_sets: set[str],
        constant_weight: float = 0.0,
        scaling_weight: float = 1.0,
        topic: int = 0,
    ):
        self.keyword_sets = keyword_sets
        self.constant_weight = constant_weight
        self.scaling_weight = scaling_weight
        self.topic = topic

        self.apply = lambda page_text: all(
            any(keyword in page_text for keyword in keyword_set)
            for keyword_set in self.keyword_sets
        )


class TldPredicate(Predicate):
    tld: str  # e.g. "org" or "gov.uk"

    def __init__(
        self,
        tld: str,
        constant_weight: float = 0.0,
        scaling_weight: float = 1.0,
        topic: int = 0,
    ):
        if tld.startswith("."):  # Remove leading full stop
            tld = tld[1:]

        self.tld = tld
        self.constant_weight = constant_weight
        self.scaling_weight = scaling_weight
        self.topic = topic

        self.apply = lambda tld: self.tld == tld

    def __str__(self):
        return f"{self.__class__.__name__}({self.tld})"


class Score:
    def __init__(self, value: float, matched_predicates: list[Predicate]):
        self.value = value
        self.matched_predicates = matched_predicates

    def __str__(self):
        return f"{self.__class__.__name__}({self.value:.3f}, {self.matched_predicates})"


class _ScoreBuilder:
    def __init__(self):
        self.value = 0
        self.matched_predicates = []

    def compound(self, predicate: Predicate) -> None:
        self.apply_weights(predicate.constant_weight, predicate.scaling_weight)
        self.matched_predicates.append(predicate)

    def apply_weights(self, constant_weight: float, scaling_weight: float) -> None:
        self.value += constant_weight
        self.value *= scaling_weight

    def get_score(self, percentile_90: float) -> Score:
        return Score(
            logistic00(self.value, (percentile_90, 0.9)), self.matched_predicates
        )


class PageScorer:
    def __init__(
        self,
        percentile_90: float,
        word_count_factor: float,
        topic_count_factor: float,
        predicates: list[HtmlPredicate | KeywordTokenPredicate],
    ):
        self.percentile_90 = percentile_90
        self.word_count_factor = word_count_factor
        self.topic_count_factor = topic_count_factor
        self.predicates = predicates

    def get_score(self, page_html: str) -> Score:
        soup = BeautifulSoup(page_html, "html.parser")

        page_text = self._clean_text(soup.get_text())
        page_words = set(page_text.split(" "))

        sb = _ScoreBuilder()
        topics = set()

        for predicate in self.predicates:
            if type(predicate) is HtmlPredicate:
                is_match = predicate.apply(soup)
            elif type(predicate) is KeywordTokenPredicate:
                is_match = predicate.apply(page_words)

            if is_match:
                sb.compound(predicate)
            topics.add(predicate.topic)

        sb.apply_weights(len(page_words) * self.word_count_factor, 1.0)
        sb.apply_weights(len(topics) * self.topic_count_factor, 1.0)

        return sb.get_score(self.percentile_90)

    def _clean_text(self, page_text: str) -> str:
        page_text = page_text.strip().lower()
        page_text = re.sub(r"[`!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?~]+", " ", page_text)
        page_text = re.sub(r"\s+", " ", page_text)
        return page_text


class LinkScorer:
    def __init__(
        self,
        percentile_90: float,
        parent_factor: float,
        predicates: list[TldPredicate | KeywordSearchPredicate],
    ):
        self.predicates = predicates
        self.percentile_90 = percentile_90
        self.parent_factor = parent_factor

    def get_score(self, link: str, parent_page_score: float) -> Score:
        link = link.lower()
        tld = get_tld(link, fail_silently=True, as_object=False)

        sb = _ScoreBuilder()

        for predicate in self.predicates:
            if type(predicate) is TldPredicate and tld:
                is_match = predicate.apply(tld)
            elif type(predicate) is KeywordSearchPredicate:
                is_match = predicate.apply(link)

            if is_match:
                sb.compound(predicate)

        sb.apply_weights(self.parent_factor * parent_page_score, 1.0)

        return sb.get_score(self.percentile_90)

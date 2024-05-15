from typing import Callable, Collection
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
        alias: str | None = None,
    ):
        self.apply = apply
        self.constant_weight = constant_weight
        self.scaling_weight = scaling_weight
        self.topic = topic
        self.alias = alias

    def __str__(self) -> str:
        return (
            "HTML-" + self.alias
            if self.alias
            else f"{self.__class__.__name__}({self.apply})"
        )


class KeywordPredicate(Predicate):
    def __init__(
        self,
        *keyword_sets: set[str],
        constant_weight: float = 0.0,
        scaling_weight: float = 1.0,
        required_occurrences_per_set: int = 1,
        topic: int = 0,
        alias: str | None = None,
    ):
        self.keyword_sets = [
            {kw.lower() for kw in keyword_set} for keyword_set in keyword_sets
        ]
        self.constant_weight = constant_weight
        self.scaling_weight = scaling_weight
        self.required_occurrences = required_occurrences_per_set
        self.topic = topic
        self.alias = alias

    def apply(self, page_words: set[str]) -> bool:
        for keyword_set in self.keyword_sets:
            occurrences = 0
            for keyword in keyword_set:
                if keyword in page_words:
                    occurrences += 1
                if occurrences >= self.required_occurrences:
                    break
            else:
                # Fail if not all keyword sets have enough occurrences
                return False
        return True

    def __str__(self):
        if self.alias:
            return "KW-" + self.alias
        return (
            self.__class__.__name__
            + "("
            + " ".join(
                [
                    f"{{{next(iter(keyword_set))} ... }}"
                    for keyword_set in self.keyword_set
                ]
            )
            + ")"
        )


class RegexPredicate(Predicate):
    def __init__(
        self,
        *patterns: set[str],
        constant_weight: float = 0.0,
        scaling_weight: float = 1.0,
        alias: str | None = None,
    ):
        self.patterns = [re.compile("|".join(p)) for p in patterns]
        self.constant_weight = constant_weight
        self.scaling_weight = scaling_weight
        self.alias = alias

    def apply(self, page_text: str) -> bool:
        for pattern in self.patterns:
            if not pattern.findall(page_text):
                return False
        return True

    def __str__(self):
        if self.alias:
            return "RX-" + self.alias
        return (
            self.__class__.__name__
            + "("
            + " ".join([f"{{{next(iter(p))} ... }}" for p in self.patterns])
            + ")"
        )


class Score:
    def __init__(self, value: float, matched_predicates: list[Predicate]):
        self.value = value
        self.matched_predicates = matched_predicates

    def __str__(self):
        return f"{self.__class__.__name__}({self.value:.3f}, {[str(p) for p in self.matched_predicates]})"


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
        predicates: list[Predicate],
    ):
        self.percentile_90 = percentile_90
        self.word_count_factor = word_count_factor
        self.predicates = predicates

    def score(self, page_html: str) -> Score:
        soup = BeautifulSoup(page_html, "html.parser")

        page_text = self._cleaned_text(soup.get_text())
        page_words = set(page_text.lower().split(" "))

        sb = _ScoreBuilder()

        for predicate in self.predicates:
            if type(predicate) is HtmlPredicate:
                is_match = predicate.apply(soup)
            elif type(predicate) is KeywordPredicate:
                is_match = predicate.apply(page_words)
            elif type(predicate) is RegexPredicate:
                is_match = predicate.apply(page_text)

            if is_match:
                sb.compound(predicate)

        sb.apply_weights(len(page_words) * self.word_count_factor, 1.0)
        return sb.get_score(self.percentile_90)

    def _cleaned_text(self, page_text: str) -> str:
        page_text = page_text.strip()
        page_text = re.sub(r"[`!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?~]+", " ", page_text)
        page_text = re.sub(r"\s+", " ", page_text)
        return page_text


class LinkScorer:
    def __init__(
        self,
        percentile_90: float,
        parent_factor: float,
        predicates: list[RegexPredicate],
    ):
        self.predicates = predicates
        self.percentile_90 = percentile_90
        self.parent_factor = parent_factor

    def score(self, link: str, parent_page_score: float) -> Score:
        sb = _ScoreBuilder()
        for predicate in self.predicates:
            if predicate.apply(link.lower()):
                sb.compound(predicate)

        sb.apply_weights(self.parent_factor * parent_page_score, 1.0)

        return sb.get_score(self.percentile_90)

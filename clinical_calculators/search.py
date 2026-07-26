from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable, Sequence
import unicodedata


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEARCH_TERMS_CSV = ROOT / "clinical_calculator_search_terms.csv"

FIELD_WEIGHTS = {
    "name_cn": 10,
    "name_en": 10,
    "scenario": 6,
    "subspecialty": 4,
    "category": 3,
    "purpose": 2,
    "source": 1,
    "tags": 10,
    "aliases": 10,
}

SEARCH_FIELDS = tuple(FIELD_WEIGHTS)
_CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]+")
_LATIN_RE = re.compile(r"[a-z0-9]+")


def normalize_search_text(value: str) -> str:
    """Normalize width, case, punctuation, and whitespace for search only."""

    value = unicodedata.normalize("NFKC", value).casefold()
    normalized: list[str] = []
    for character in value:
        category = unicodedata.category(character)
        if character.isalnum() or _is_cjk(character):
            normalized.append(character)
        elif category.startswith(("P", "S", "Z")) or character.isspace():
            normalized.append(" ")
        else:
            normalized.append(" ")
    return " ".join("".join(normalized).split())


def tokenize_search_text(value: str) -> tuple[str, ...]:
    """Return deterministic CJK unigram/bigram and Latin search variants."""

    normalized = normalize_search_text(value)
    if not normalized:
        return ()

    tokens: list[str] = []
    for run in _CJK_RE.findall(normalized):
        tokens.extend(run)
        tokens.extend(run[index : index + 2] for index in range(len(run) - 1))
        if len(run) > 2:
            tokens.append(run)

    latin_runs = _LATIN_RE.findall(normalized)
    for run in latin_runs:
        tokens.append(run)
        without_digits = "".join(character for character in run if not character.isdigit())
        if without_digits and without_digits != run:
            tokens.append(without_digits)

    if len(latin_runs) > 1:
        compact = "".join(latin_runs)
        tokens.append(compact)
        without_digits = "".join(character for character in compact if not character.isdigit())
        if without_digits and without_digits != compact:
            tokens.append(without_digits)

    width_normalized = unicodedata.normalize("NFKC", value)
    case_split = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", width_normalized)
    case_split = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", case_split)
    for run in _LATIN_RE.findall(normalize_search_text(case_split)):
        tokens.append(run)

    return tuple(dict.fromkeys(token for token in tokens if token))


def load_search_aliases(
    path: str | Path = DEFAULT_SEARCH_TERMS_CSV,
) -> dict[str, tuple[str, ...]]:
    """Load and validate clinician-maintained query expansions."""

    csv_path = Path(path)
    aliases: dict[str, tuple[str, ...]] = {}
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["term", "expands_to", "note"]:
            raise ValueError("search terms CSV must have columns: term, expands_to, note")
        for line_number, row in enumerate(reader, start=2):
            raw_term = row.get("term", "").strip()
            raw_expansions = row.get("expands_to", "").strip()
            if not raw_term or not raw_expansions:
                raise ValueError(
                    f"search term row {line_number} requires non-empty term and expands_to"
                )
            term = normalize_search_text(raw_term)
            if not term:
                raise ValueError(f"search term row {line_number} normalizes to empty text")
            if term in aliases:
                raise ValueError(f"duplicate search term: {raw_term}")
            expansions: list[str] = []
            for raw_expansion in raw_expansions.split(";"):
                expansion = normalize_search_text(raw_expansion)
                if not expansion:
                    raise ValueError(
                        f"search term row {line_number} has an empty expansion"
                    )
                if expansion == term:
                    raise ValueError(f"search term cannot expand to itself: {raw_term}")
                if expansion not in expansions:
                    expansions.append(expansion)
            aliases[term] = tuple(expansions)
    return aliases


@dataclass(frozen=True)
class SearchMatch:
    score: float
    coverage: float
    matched_fields: tuple[str, ...]
    matched_terms: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "score": self.score,
            "coverage": self.coverage,
            "matched_fields": list(self.matched_fields),
            "matched_terms": list(self.matched_terms),
        }


@dataclass(frozen=True)
class SearchHit:
    calculator_id: str
    match: SearchMatch


@dataclass(frozen=True)
class SearchResponse:
    status: str
    hits: tuple[SearchHit, ...]
    suggestions: tuple[str, ...] = ()


class SearchIndex:
    """Immutable in-memory inverted index for one registry instance."""

    def __init__(
        self,
        skills: Sequence[object],
        aliases: dict[str, tuple[str, ...]] | None = None,
    ) -> None:
        self._skills = {skill.metadata.id: skill for skill in skills}
        self._aliases = aliases if aliases is not None else load_search_aliases()
        self._normalized_fields: dict[str, dict[str, str]] = {}
        self.postings: dict[str, set[tuple[str, str]]] = {}
        for skill in skills:
            calculator_id = skill.metadata.id
            fields: dict[str, str] = {}
            for field in SEARCH_FIELDS:
                value = getattr(skill.metadata, field, "")
                if isinstance(value, (tuple, list, set)):
                    value = " ".join(str(item) for item in value)
                if not isinstance(value, str) or not value:
                    continue
                normalized = normalize_search_text(value)
                fields[field] = normalized
                for token in tokenize_search_text(value):
                    self.postings.setdefault(token, set()).add((calculator_id, field))
            self._normalized_fields[calculator_id] = fields

    def search(
        self,
        query: str,
        limit: int | None = 20,
        allowed_ids: Iterable[str] | None = None,
    ) -> SearchResponse:
        normalized_query = normalize_search_text(query)
        if not normalized_query:
            return SearchResponse("no_match", ())

        allowed = set(allowed_ids) if allowed_ids is not None else set(self._skills)
        variants = self._query_variants(normalized_query)
        best_matches: dict[str, SearchMatch] = {}
        partial_matches: dict[str, SearchMatch] = {}

        for variant in variants:
            tokens = tokenize_search_text(variant)
            if not tokens:
                continue
            candidate_ids = {
                calculator_id
                for token in tokens
                for calculator_id, _ in self.postings.get(token, ())
                if calculator_id in allowed
            }
            for calculator_id in candidate_ids:
                match = self._score(calculator_id, variant, tokens)
                previous_partial = partial_matches.get(calculator_id)
                if previous_partial is None or _is_better(match, previous_partial):
                    partial_matches[calculator_id] = match
                if not self._qualifies(match, tokens):
                    continue
                previous = best_matches.get(calculator_id)
                if previous is None or _is_better(match, previous):
                    best_matches[calculator_id] = match

        if not best_matches:
            suggestions = self._suggestions(partial_matches)
            return SearchResponse("no_match", (), suggestions)

        ranked = sorted(
            best_matches.items(),
            key=lambda item: (
                -item[1].score,
                self._skills[item[0]].metadata.name_cn,
                item[0],
            ),
        )
        if limit is not None:
            ranked = ranked[:limit]
        return SearchResponse(
            "ok",
            tuple(SearchHit(calculator_id, match) for calculator_id, match in ranked),
        )

    def _query_variants(self, normalized_query: str) -> tuple[str, ...]:
        variants = [normalized_query]
        seen = {normalized_query}
        frontier = [normalized_query]
        for _ in range(2):
            next_frontier: list[str] = []
            for variant in frontier:
                for term, expansions in self._aliases.items():
                    if not _contains_term(variant, term):
                        continue
                    for expansion in expansions:
                        expanded = variant.replace(term, expansion, 1)
                        if expanded in seen:
                            continue
                        seen.add(expanded)
                        variants.append(expanded)
                        next_frontier.append(expanded)
                        if len(variants) >= 64:
                            return tuple(variants)
            frontier = next_frontier
            if not frontier:
                break
        return tuple(variants)

    def _score(
        self,
        calculator_id: str,
        normalized_query: str,
        tokens: tuple[str, ...],
    ) -> SearchMatch:
        matched_terms: list[str] = []
        matched_fields: set[str] = set()
        weighted_hits = 0
        for token in tokens:
            token_fields = {
                field
                for candidate_id, field in self.postings.get(token, ())
                if candidate_id == calculator_id
            }
            if not token_fields:
                continue
            matched_terms.append(token)
            matched_fields.update(token_fields)
            weighted_hits += sum(FIELD_WEIGHTS[field] for field in token_fields)

        coverage = len(matched_terms) / len(tokens)
        bonus = 0
        fields = self._normalized_fields[calculator_id]
        names = (fields.get("name_cn", ""), fields.get("name_en", ""))
        compact_query = normalized_query.replace(" ", "")
        compact_names = tuple(name.replace(" ", "") for name in names)
        if normalized_query in names or compact_query in compact_names:
            bonus = 1000
        elif any(
            name.startswith(normalized_query) or compact_name.startswith(compact_query)
            for name, compact_name in zip(names, compact_names)
            if normalized_query
        ):
            bonus = 300
        elif any(
            normalized_query in name or compact_query in compact_name
            for name, compact_name in zip(names, compact_names)
            if normalized_query
        ):
            bonus = 150
        score = weighted_hits * coverage + bonus
        return SearchMatch(
            score=round(score, 6),
            coverage=round(coverage, 6),
            matched_fields=tuple(
                field for field in SEARCH_FIELDS if field in matched_fields
            ),
            matched_terms=tuple(matched_terms),
        )

    @staticmethod
    def _qualifies(match: SearchMatch, tokens: tuple[str, ...]) -> bool:
        latin_terms = tuple(
            token for token in tokens if not _contains_cjk(token) and len(token) >= 3
        )
        if latin_terms and not any(token in match.matched_terms for token in latin_terms):
            return False
        distinctive = any(
            token in match.matched_terms and (_contains_cjk(token) and len(token) >= 2 or len(token) >= 3)
            for token in tokens
        )
        minimum_coverage = 0.2 if latin_terms else 0.3
        return distinctive and (match.coverage >= minimum_coverage or match.score >= 150)

    def _suggestions(self, partial_matches: dict[str, SearchMatch]) -> tuple[str, ...]:
        ranked = sorted(
            partial_matches.items(),
            key=lambda item: (
                -item[1].score,
                self._skills[item[0]].metadata.name_cn,
                item[0],
            ),
        )
        suggestions: list[str] = []
        for calculator_id, _ in ranked:
            name = self._skills[calculator_id].metadata.name_cn
            if name not in suggestions:
                suggestions.append(name)
            if len(suggestions) == 5:
                break
        return tuple(suggestions)


def _is_cjk(character: str) -> bool:
    return "\u3400" <= character <= "\u4dbf" or "\u4e00" <= character <= "\u9fff"


def _contains_cjk(value: str) -> bool:
    return any(_is_cjk(character) for character in value)


def _contains_term(text: str, term: str) -> bool:
    if _contains_cjk(term):
        return term in text
    return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text) is not None


def _is_better(candidate: SearchMatch, current: SearchMatch) -> bool:
    return (candidate.score, candidate.coverage, candidate.matched_terms) > (
        current.score,
        current.coverage,
        current.matched_terms,
    )

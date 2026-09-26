"""
Regex-based citation/claim checks (citation coverage + quantitative
grounding). No LLM involved in this module.

IMPORTANT: these regex/substring checks (CITATION_CHECK_PATTERNS in
config.py; check_citation_coverage() and verify_quantitative_grounding()
below) confirm that a claim of a given type (dollar figure, TRL level,
percentage, year) is present, cited, and formatted consistently with its
source text - they are a format/presence check, not a correctness check.
A number can be verbatim-matched here and still be the wrong number (e.g.
a correctly-quoted figure pulled from the wrong context). Do not treat a
"flagged": False / "verbatim_match": True result as a semantic-accuracy
guarantee. score_faithfulness()'s LLM-judge pass, and cross-source
corroboration for quantitative claims in the sections listed in
QUANTITATIVE_CORROBORATION_SECTIONS, are the layers that actually judge
correctness; this module only judges whether a checkable claim looks
properly and consistently cited.
"""

import re

from rag.hallucination.config import CITATION_CHECK_PATTERNS, CITATION_MARKER_PATTERN

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")


def split_into_sentences(text: str) -> list[str]:
    """Splits text into sentences/lines.

    Args:
        text: The text to split.

    Returns:
        A list of trimmed, non-empty sentences/lines.
    """
    return [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip()]


def check_citation_coverage(section_text: str) -> list[dict]:
    """Flags sentences with a checkable claim but no citation marker.

    Args:
        section_text: The section text to check.

    Returns:
        A list of dicts, one per sentence containing a checkable claim
        (dollar figure, TRL level, percentage, year): {"sentence",
        "has_citation", "flagged"}. Sentences with no checkable claim are
        omitted.
    """
    flagged_sentences = []

    for sentence in split_into_sentences(section_text):
        requires_citation = any(p["pattern"].search(sentence) for p in CITATION_CHECK_PATTERNS)
        if not requires_citation:
            continue

        has_citation = bool(CITATION_MARKER_PATTERN.search(sentence))
        flagged_sentences.append({
            "sentence": sentence,
            "has_citation": has_citation,
            "flagged": not has_citation,
        })

    return flagged_sentences


_UNIT_WORD_MAP = {"billion": "b", "bn": "b", "million": "m", "mm": "m", "thousand": "k"}

_DOC_INDEX_PATTERN = re.compile(r"\d+")


def _normalize_quantitative_text(text: str) -> str:
    """
    Normalizes currency/percent/TRL formatting variants for near-verbatim
    comparison: lowercases, strips whitespace/commas/$/%, and maps unit
    words to one abbreviation, so "$500 million", "$ 500 million", and
    "$500M" all normalize identically.

    Known limitation: no magnitude arithmetic - this does not equate
    "$0.5 billion" with "$500 million". That needs real numeric parsing
    and isn't attempted here.
    """
    normalized = text.lower()
    normalized = re.sub(r"[\s,]", "", normalized).replace("$", "").replace("%", "")
    for word, abbrev in _UNIT_WORD_MAP.items():
        normalized = normalized.replace(word, abbrev)
    return normalized


def claim_present_near_verbatim(claim_text: str, doc_text: str) -> bool:
    """Substring check after _normalize_quantitative_text on both sides."""
    return _normalize_quantitative_text(claim_text) in _normalize_quantitative_text(doc_text)


def extract_quantitative_claim(claim_text: str) -> tuple[str, str] | tuple[None, None]:
    """
    Returns (claim_type, matched_substring) for the first CITATION_CHECK_PATTERNS
    entry that matches claim_text, or (None, None) if it has no numeric/
    date/%/TRL claim. Reused by faithfulness.py's cross-source corroboration
    step rather than duplicated.
    """
    for entry in CITATION_CHECK_PATTERNS:
        match = entry["pattern"].search(claim_text)
        if match:
            return entry["type"], match.group()
    return None, None


def verify_quantitative_grounding(section_text: str, retrieved_documents: list[dict]) -> list[dict]:
    """
    Stricter follow-on to check_citation_coverage(): for each sentence with
    BOTH a [Doc N] marker AND a numeric/date/%/TRL claim, resolves [Doc N]
    to retrieved_documents[N-1] and checks whether the matched claim
    substring appears near-verbatim in THAT specific document - not just
    that some citation marker is present. Does not replace
    check_citation_coverage, which stays as the sentence-level presence
    check; this is an additional, stricter pass, and is not itself a
    correctness check either (see module docstring).

    Args:
        section_text: The section text to check.
        retrieved_documents: Documents [Doc N] markers are resolved against,
            in the same order used to build faithfulness.py's judge context.

    Returns:
        One dict per (sentence, matched claim type) pair with a checkable
        claim: {"sentence", "claim_type", "claim_text", "doc_ref",
        "verbatim_match", "flagged"}. doc_ref is None (and verbatim_match
        False) if the sentence has no marker or the marker's index doesn't
        resolve to a retrieved document.
    """
    results = []

    for sentence in split_into_sentences(section_text):
        marker_match = CITATION_MARKER_PATTERN.search(sentence)
        doc_idx = None
        doc_text = None
        if marker_match:
            idx_match = _DOC_INDEX_PATTERN.search(marker_match.group())
            doc_idx = int(idx_match.group()) if idx_match else None
            if doc_idx and 0 < doc_idx <= len(retrieved_documents):
                doc_text = retrieved_documents[doc_idx - 1].get("text", "")
            else:
                doc_idx = None

        for entry in CITATION_CHECK_PATTERNS:
            claim_match = entry["pattern"].search(sentence)
            if not claim_match:
                continue

            claim_text = claim_match.group()
            verbatim = doc_text is not None and claim_present_near_verbatim(claim_text, doc_text)
            results.append({
                "sentence": sentence,
                "claim_type": entry["type"],
                "claim_text": claim_text,
                "doc_ref": doc_idx,
                "verbatim_match": verbatim,
                "flagged": not verbatim,
            })

    return results

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
        requires_citation = any(p.search(sentence) for p in CITATION_CHECK_PATTERNS)
        if not requires_citation:
            continue

        has_citation = bool(CITATION_MARKER_PATTERN.search(sentence))
        flagged_sentences.append({
            "sentence": sentence,
            "has_citation": has_citation,
            "flagged": not has_citation,
        })

    return flagged_sentences

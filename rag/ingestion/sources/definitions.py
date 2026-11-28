"""How each source is declared: what it provides, its trust tier and how often it runs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from rag.corpus.categories import TrustTier
from rag.corpus.document_types import DocumentType


# Values must match the CHECK constraints on corpus.sources.
class SourceType(str, Enum):
    """What a source provides."""

    DOCUMENTS = "documents"   # text that is chunked and searched
    FACTS = "facts"           # structured figures, e.g. XBRL financials
    TOOL = "tool"             # computed on demand, e.g. JPL delta-v


class Cadence(str, Enum):
    """How often a source is fetched."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ON_DEMAND = "on_demand"


@dataclass(frozen=True)
class SourceDefinition:
    """One source as declared in code; the registry pairs it with a fetcher."""

    source_name: str
    source_type: SourceType
    document_types: tuple[DocumentType, ...]
    trust_tier: TrustTier
    cadence: Cadence
    terms_note: str = ""   # usage terms to respect, e.g. "headlines and links only"
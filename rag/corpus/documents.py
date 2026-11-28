"""The document shapes every source produces, before chunking."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator

from rag.corpus.categories import CATEGORY_TRUST, Category, TrustTier
from rag.corpus.document_types import DocumentType, category_of


class Section(BaseModel):
    """One named part of a document, e.g. a 10-K's Item 1A or a patent's claims."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(pattern=r"^[a-z0-9_]+$")   # e.g. "item_1a", "claims", "abstract"
    text: str = Field(min_length=1)              # never empty

class SourceDocument(BaseModel):
    """One document as fetched from a source, before chunking."""

    model_config = ConfigDict(frozen=True)

    document_id: str = Field(pattern=r"^[a-z0-9_]+:\S+$")   # "<prefix>:<native id>", e.g. "techport:12345"
    source_name: str = Field(pattern=r"^[a-z0-9_]+$")       # registry name, matches corpus.sources
    document_type: DocumentType
    title: str = Field(min_length=1)
    url: str                                                # citation link
    published_at: datetime | None = None                    # timezone required
    sections: tuple[Section, ...] = Field(min_length=1)
    entities: tuple[str, ...] = ()                          # companies, programs, missions
    extra: dict[str, str | int | float | list[str]] = Field(default_factory=dict)   # type-specific fields

    @property
    def category(self) -> Category:
    
        """Derived from document_type, never set by the source."""
        return category_of(self.document_type)

    @property
    def trust_tier(self) -> TrustTier:
    
        """Decides which collection the document's chunks go into."""
        return CATEGORY_TRUST[self.category]
    
    @field_validator("url")
    @classmethod
    def _https_only(cls, value: str) -> str:
    
        """Citation links must be https."""
    
        if not value.startswith("https://"):
            raise ValueError("url must start with https://")
        return value

    @field_validator("published_at")
    @classmethod
    def _timezone_aware(cls, value: datetime | None) -> datetime | None:
    
        """Dates must carry a timezone stored in UTC so they sort and filter correctly."""
        if value is None:
            return None
        
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("published_at must include a timezone")
        return value.astimezone(timezone.utc)

    @field_validator("sections")
    @classmethod
    def _section_names_unique(cls, value: tuple[Section, ...]) -> tuple[Section, ...]:
    
        """Each section name appears once, so every section has its own parent_id."""
    
        names = [section.name for section in value]
        repeated = sorted({name for name in names if names.count(name) > 1})
        if repeated:
            raise ValueError(f"section names must be unique: {repeated}")
        return value
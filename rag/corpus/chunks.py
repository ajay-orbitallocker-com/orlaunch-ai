"""A searchable piece of a document: what gets embedded and written to the corpus."""

from __future__ import annotations

import hashlib

from pydantic import BaseModel, ConfigDict, Field, model_validator

from rag.corpus.documents import SourceDocument

class Chunk(BaseModel):
    """One searchable piece of a document section, ready to embed and write."""

    model_config = ConfigDict(frozen=True)

    document: SourceDocument                        # where it came from - carries title, url, entities
    section: str = Field(pattern=r"^[a-z0-9_]+$")   # name of the section it was cut from
    position: int = Field(ge=0)                     # order within the section, starting at 0
    header: str = Field(min_length=1)               # context for embedding - its never shown in the CDD
    text: str = Field(min_length=1)                 # the chunk itself; what the CDD quotes

    @model_validator(mode="after")
    def _section_belongs_to_document(self) -> Chunk:
        """The chunk's section must be one of its document's sections."""
    
        section_names = {section.name for section in self.document.sections}
    
        if self.section not in section_names:
            raise ValueError(f"section '{self.section}' is not in document {self.document.document_id}")
        return self

    @property
    def parent_id(self) -> str:
        """The section this chunk belongs to: "<document_id>:<section>"."""
        return f"{self.document.document_id}:{self.section}"

    @property
    def chunk_id(self) -> str:
        """Stable across runs: "<document_id>:<section>:<position>"."""
        return f"{self.parent_id}:{self.position}"

    @property
    def embedding_text(self) -> str:
        """Header plus chunk text; the only input to dense and BM25 embedding."""
        return f"{self.header}\n\n{self.text}"

    @property
    def chunk_hash(self) -> str:
        """SHA-256 of the embedding input; changes whenever the vectors would."""
        return hashlib.sha256(self.embedding_text.encode("utf-8")).hexdigest()
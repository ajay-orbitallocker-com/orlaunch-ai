"""Document types each source produces, and the evidence category each one belongs to."""

from __future__ import annotations

from enum import Enum

from rag.corpus.categories import Category

# Values are stored in Qdrant and Postgres: never rename one after ingest, add a new member instead.
class DocumentType(str, Enum):
    """The kind of document a chunk came from; decides its category and chunking."""

    TECHPORT_PROJECT = "techport_project"                 # NASA technology project record
    NTRS_REPORT = "ntrs_report"                           # NASA technical report
    ARXIV_ABSTRACT = "arxiv_abstract"                     # preprint title and abstract
    PATENT_GRANT = "patent_grant"                         # granted patent
    PATENT_APPLICATION = "patent_application"             # published patent application
    SEC_10K = "sec_10k"                                   # annual company filing
    SEC_10Q = "sec_10q"                                   # quarterly company filing
    SEC_8K = "sec_8k"                                     # material event filing
    CFR_SECTION = "cfr_section"                           # one section of federal regulations
    FEDERAL_REGISTER_NOTICE = "federal_register_notice"   # proposed or final rule notice
    FCC_PUBLIC_NOTICE = "fcc_public_notice"               # FCC space bureau notice
    NEWS_ITEM = "news_item"                               # headline, summary and link only

# Every document type's category; a category may have no document type yet (funding, planetary).
DOCUMENT_TYPE_CATEGORY: dict[DocumentType, Category] = {

    DocumentType.TECHPORT_PROJECT: Category.TECHNICAL,
    DocumentType.NTRS_REPORT: Category.TECHNICAL,
    DocumentType.ARXIV_ABSTRACT: Category.TECHNICAL,
    DocumentType.PATENT_GRANT: Category.PATENTS,
    DocumentType.PATENT_APPLICATION: Category.PATENTS,
    DocumentType.SEC_10K: Category.FINANCIAL,
    DocumentType.SEC_10Q: Category.FINANCIAL,
    DocumentType.SEC_8K: Category.FINANCIAL,
    DocumentType.CFR_SECTION: Category.REGULATORY,
    DocumentType.FEDERAL_REGISTER_NOTICE: Category.REGULATORY,
    DocumentType.FCC_PUBLIC_NOTICE: Category.REGULATORY,
    DocumentType.NEWS_ITEM: Category.MARKET,

}

def category_of(document_type: DocumentType) -> Category:
    
    """Evidence category for a document type."""
    return DOCUMENT_TYPE_CATEGORY[document_type]
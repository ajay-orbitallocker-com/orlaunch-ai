"""
Retrieve CDD sources: the documents a CDD cites, with one [Doc N] number per document.

Searches the whole corpus (no category filter) for each query. 
This module only assigns the numbers they use.
"""

from rag.retrieval.search import retrieve_top_k_documents


class CDDSourceRetriever:
    """Retrieves documents for CDD sections and numbers each one once."""

    def __init__(self, top_k: int):
        """Start with no documents; top_k is how many to fetch per query."""
        self.top_k = top_k
        self.documents: list[dict] = []      # every retrieved document, in [Doc N] order
        self._numbers: dict[str, int] = {}   # document key - its [Doc N] number

    def retrieve(self, queries: list[str]) -> list[tuple[int, dict]]:
        """Return (doc_number, doc) pairs for all queries, without repeats."""
        found: dict[int, dict] = {}
        for query in queries:
            for doc in retrieve_top_k_documents(query, top_k=self.top_k, category_filter=None):
                key = doc.get("url") or f"{doc.get('title', '')}|{doc.get('text', '')[:200]}"
                if key not in self._numbers:
                    self.documents.append(doc)
                    self._numbers[key] = len(self.documents)
                found[self._numbers[key]] = doc
        return list(found.items())

    def sources(self) -> dict[int, dict]:
        """Map each [Doc N] number to its source, for the PDF References section."""
        return {
            number: {
                "title": doc.get("title", "Untitled Document"),
                "url": doc.get("url", ""),
                "category": doc.get("category", "General"),
            }
            for number, doc in enumerate(self.documents, 1)
        }


def format_context(indexed_documents: list[tuple[int, dict]]) -> str:
    """Format documents as prompt context, each labelled with its [Doc N] number."""
    return "\n\n".join(
        f"[Doc {number}] {doc.get('title', 'Untitled Document')}\n{doc.get('text', '')}"
        for number, doc in indexed_documents
    )
def dedupe_preserving_rank(retrieved_docs: list[dict]) -> tuple[list[dict], int]:
    """
    Collapses retrieved chunks to one entry per source document id, keeping
    the first (highest-ranked) occurrence and dropping later chunks from the
    same document. Relevance is judged per source document, not per chunk,
    so multiple chunks from one relevant document must count as a single
    hit for Recall/Precision/etc., not several.

    Entries with no "id" (missing Chroma metadata) can't be matched against
    relevance judgments and are dropped; their count is returned so callers
    can surface it as a diagnostic instead of silently losing candidates.
    """
    deduped = []
    seen_ids = set()
    missing_id_count = 0

    for doc in retrieved_docs:
        doc_id = doc.get("id")
        if doc_id is None:
            missing_id_count += 1
            continue
        if doc_id in seen_ids:
            continue
        seen_ids.add(doc_id)
        deduped.append(doc)

    return deduped, missing_id_count

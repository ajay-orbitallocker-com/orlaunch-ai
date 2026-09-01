from chroma_config import client, EMBEDDING_MODEL, collection


def get_text_embedding(text: str) -> list[float]:
    """Generate embedding vector using OpenAI text-embedding-3-small."""
    response = client.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL
    )
    return response.data[0].embedding

def _query_top_k_documents(query_text: str, top_k: int, category_filter: str | None) -> list[dict]:
    """Runs the ChromaDB cosine similarity query and builds the document dict list.

    Args:
        query_text: The text to embed and search with.
        top_k: How many results to return.
        category_filter: If given, restricts results to this category.

    Returns:
        A list of dicts, one per matched chunk: {"id", "title", "category",
        "trl_current", "url", "similarity_score", "text"}, ranked by
        similarity (highest first).
    """
    query_vector = get_text_embedding(query_text)

    where_clause = {"category": category_filter} if category_filter else None

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        where=where_clause,
        include=["documents", "metadatas", "distances"]
    )

    retrieved = []
    if results and "documents" in results and results["documents"]:
        docs = results["documents"][0]
        metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
        dists = results["distances"][0] if "distances" in results else [0.0] * len(docs)

        for doc, meta, dist in zip(docs, metas, dists):
            # Cosine distance to similarity score: similarity = 1 - distance
            similarity_score = round(max(0.0, 1.0 - dist), 4)
            retrieved.append({
                "id": meta.get("id"),
                "title": meta.get("title", "Untitled Document"),
                "category": meta.get("category", "General"),
                "trl_current": meta.get("trl_current"),
                "url": meta.get("url", ""),
                "similarity_score": similarity_score,
                "text": doc
            })

    return retrieved


def retrieve_top_k_documents(query_text: str, top_k: int = 5, category_filter: str | None = None) -> list[dict]:
    """
    Perform cosine similarity search against ChromaDB.
    Returns top-K matching document chunks with metadata and similarity scores.
    """
    return _query_top_k_documents(query_text, top_k, category_filter)


def retrieve_top_k_documents_with_status(query_text: str, top_k: int = 5, category_filter: str | None = None) -> dict:
    """Runs the same retrieval as retrieve_top_k_documents(), plus retrieval status.

    Args:
        query_text: The text to embed and search with.
        top_k: How many results to return.
        category_filter: If given, restricts results to this category.

    Returns:
        A dict with keys "documents" (see retrieve_top_k_documents()) and
        "embedding_fallback_used". The embedding step has no fallback path
        (get_text_embedding() raises on failure rather than degrading), so
        "embedding_fallback_used" is always False; it's kept as a field so
        callers built against it don't need special-casing if a fallback
        is reintroduced later.
    """
    documents = _query_top_k_documents(query_text, top_k, category_filter)
    return {"documents": documents, "embedding_fallback_used": False}

def build_context_package(query_text: str, top_k: int = 5) -> dict:
    """
    Build the structured Context Package to pass directly to GPT-4o Mini:
    Idea -> Similarity Search -> Top-K Docs -> Context Package
    """
    documents = retrieve_top_k_documents(query_text, top_k=top_k)
    
    formatted_docs_text = []
    for idx, d in enumerate(documents, 1):
        trl_str = f" [TRL {d['trl_current']}]" if d.get("trl_current") is not None else ""
        formatted_docs_text.append(
            f"--- [Doc {idx}] {d['title']}{trl_str} (Relevance Score: {d['similarity_score']}) ---\n"
            f"Category: {d['category']}\n"
            f"Content: {d['text']}\n"
        )
        
    context_package = {
        "user_idea": query_text,
        "total_documents_retrieved": len(documents),
        "retrieved_documents": documents,
        "formatted_context_str": "\n".join(formatted_docs_text)
    }
    return context_package

if __name__ == "__main__":
    sample_idea = "A startup developing low-cost electric propulsion for CubeSat orbit maneuvering"
    print(f"Testing Retrieval Workflow for Idea: '{sample_idea}'")
    try:
        pkg = build_context_package(sample_idea, top_k=3)
        print(f"\nRetrieved {pkg['total_documents_retrieved']} relevant documents.")
        print("\nFormatted Context Package Sample:\n")
        print(pkg["formatted_context_str"])
    except Exception as e:
        print(f"Retrieval test error: {e}")

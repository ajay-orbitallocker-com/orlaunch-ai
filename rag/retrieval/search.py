from chroma_config import client, EMBEDDING_MODEL, collection
from rag.ingestion.config import get_default_categories


def get_text_embedding(text: str) -> list[float]:
    """Generate embedding vector using OpenAI text-embedding-3-small."""
    response = client.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL
    )
    return response.data[0].embedding


def build_where_clause(
    category_filter: str | list[str] | None = None,
    source_filter: str | list[str] | None = None,
    where: dict | None = None,
    **additional_filters
) -> dict | None:
    """
    Build a flexible ChromaDB where clause supporting:
    - Single strings or lists of categories/sources ($in for multiple)
    - Raw ChromaDB where query clauses
    - Arbitrary keyword metadata filters (e.g. trl_current=5)
    - Automatic $and combination of multiple conditions
    """
    conditions = []

    if where:
        conditions.append(where)

    if category_filter:
        if isinstance(category_filter, (list, tuple, set)):
            cats = list(category_filter)
            if len(cats) == 1:
                conditions.append({"category": cats[0]})
            elif len(cats) > 1:
                conditions.append({"category": {"$in": cats}})
        else:
            conditions.append({"category": category_filter})

    if source_filter:
        if isinstance(source_filter, (list, tuple, set)):
            srcs = list(source_filter)
            if len(srcs) == 1:
                conditions.append({"source": srcs[0]})
            elif len(srcs) > 1:
                conditions.append({"source": {"$in": srcs}})
        else:
            conditions.append({"source": source_filter})

    for key, val in additional_filters.items():
        if val is not None:
            if isinstance(val, (list, tuple, set)):
                vals = list(val)
                if len(vals) == 1:
                    conditions.append({key: vals[0]})
                elif len(vals) > 1:
                    conditions.append({key: {"$in": vals}})
            else:
                conditions.append({key: val})

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


def query_top_k_documents(
    query_text: str,
    top_k: int = 5,
    category_filter: str | list[str] | None = None,
    source_filter: str | list[str] | None = None,
    where: dict | None = None,
    **filters
) -> list[dict]:
    """
    Flexible similarity search against ChromaDB.

    Args:
        query_text: The text to embed and search with.
        top_k: How many results to return.
        category_filter: Restrict results to one or more categories.
        source_filter: Restrict results to one or more sources.
        where: Explicit ChromaDB where clause dictionary.
        **filters: Additional metadata filter key-values (e.g. trl_current=5).

    Returns:
        A list of dicts, one per matched chunk: {"id", "title", "category",
        "source", "trl_current", "url", "similarity_score", "text"}, ranked by
        similarity (highest first).
    """
    query_vector = get_text_embedding(query_text)
    where_clause = build_where_clause(
        category_filter=category_filter,
        source_filter=source_filter,
        where=where,
        **filters
    )

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
            similarity_score = round(max(0.0, 1.0 - dist), 4)
            retrieved.append({
                "id": meta.get("id"),
                "title": meta.get("title", "Untitled Document"),
                "category": meta.get("category", "General"),
                "source": meta.get("source", ""),
                "trl_current": meta.get("trl_current"),
                "url": meta.get("url", ""),
                "similarity_score": similarity_score,
                "text": doc
            })

    return retrieved


# Maintain retrieve_top_k_documents as alias for query_top_k_documents
retrieve_top_k_documents = query_top_k_documents


def retrieve_top_k_documents_with_status(
    query_text: str,
    top_k: int = 5,
    category_filter: str | list[str] | None = None,
    source_filter: str | list[str] | None = None,
    where: dict | None = None,
    **filters
) -> dict:
    """Runs query_top_k_documents() plus retrieval status metadata."""
    documents = query_top_k_documents(
        query_text=query_text,
        top_k=top_k,
        category_filter=category_filter,
        source_filter=source_filter,
        where=where,
        **filters
    )
    return {"documents": documents, "embedding_fallback_used": False}


def get_all_categories(db_collection=collection) -> list[str]:
    """
    Dynamically discover all unique categories from the vector store.
    Falls back to default categories if collection is unpopulated or empty.
    """
    try:
        data = db_collection.get(include=["metadatas"])
        if data and "metadatas" in data and data["metadatas"]:
            cats = {
                m.get("category")
                for m in data["metadatas"]
                if m and m.get("category")
            }
            if cats:
                return sorted(cats)
    except Exception as e:
        print(f"Warning: could not query categories dynamically: {e}")

    return get_default_categories()


def calculate_per_category_document_count(total_top_k: int, categories: list[str]) -> int:
    """
    Calculate the document limit allocated to each category to distribute
    the total top_k budget evenly across categories.
    """
    num_cats = len(categories)
    if num_cats <= 0:
        return total_top_k
    return max(1, total_top_k // num_cats) if total_top_k >= num_cats else 1


def retrieve_multi_category_documents(
    query_text: str,
    per_category_k: int = 2,
    categories: list[str] | None = None
) -> dict[str, list[dict]]:
    """
    Retrieve top-K matching documents across each category dynamically discovered or specified.
    """
    target_categories = categories or get_all_categories()
    results_by_cat = {}
    for cat in target_categories:
        results_by_cat[cat] = query_top_k_documents(
            query_text=query_text,
            top_k=per_category_k,
            category_filter=cat
        )
    return results_by_cat


def build_context_package(
    query_text: str,
    top_k: int = 5,
    per_category: bool = True,
    categories: list[str] | None = None
) -> dict:
    """
    Build the structured Context Package to pass directly to GPT-4o Mini:
    Idea -> Similarity Search -> Multi-Source Docs -> Context Package.

    Args:
        query_text: User venture idea or prompt.
        top_k: Total or per-category top documents to retrieve.
        per_category: If True, retrieves top matches per category so no
            data source is omitted from the context. If False, performs
            a single global cosine similarity search.
        categories: List of categories to retrieve when per_category=True.
    """
    if per_category:
        target_cats = categories or get_all_categories()
        per_cat_limit = calculate_per_category_document_count(top_k, target_cats)
        cat_map = retrieve_multi_category_documents(
            query_text, per_category_k=per_cat_limit, categories=target_cats
        )

        documents = []
        for cat in target_cats:
            documents.extend(cat_map.get(cat, []))
    else:
        documents = query_top_k_documents(query_text, top_k=top_k)

    formatted_docs_text = []
    for idx, d in enumerate(documents, 1):
        trl_str = f" [TRL {d['trl_current']}]" if d.get("trl_current") is not None else ""
        source_str = f" | Source: {d.get('source')}" if d.get("source") else ""
        formatted_docs_text.append(
            f"--- [Doc {idx}] {d['title']}{trl_str} (Relevance Score: {d['similarity_score']}) ---\n"
            f"Category: {d['category']}{source_str}\n"
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
        pkg = build_context_package(sample_idea, top_k=4, per_category=True)
        print(f"\nRetrieved {pkg['total_documents_retrieved']} relevant documents across categories.")
        print("\nFormatted Context Package Sample:\n")
        print(pkg["formatted_context_str"])
    except Exception as e:
        print(f"Retrieval test error: {e}")


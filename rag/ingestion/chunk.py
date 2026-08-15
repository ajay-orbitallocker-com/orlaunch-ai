import tiktoken

ENCODING = tiktoken.get_encoding("cl100k_base")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
CHUNK_STRIDE = CHUNK_SIZE - CHUNK_OVERLAP

def chunk_text(text: str) -> list[str]:
    """
    Sliding-window split: encode to tokens, slice into 500-token windows
    advancing by 400 tokens (100-token overlap), decode back to text.
    """
    if not text:
        return []
    tokens = ENCODING.encode(text)

    if len(tokens) <= CHUNK_SIZE:
        return [text]

    chunks = []
    start = 0

    while start < len(tokens):
        window = tokens[start : start + CHUNK_SIZE]
        chunks.append(ENCODING.decode(window))

        if start + CHUNK_SIZE >= len(tokens):
            break

        start += CHUNK_STRIDE

    return chunks

def chunk_document(doc: dict) -> list[dict]:
    """
    Take a standardized raw document dict and produce 500-token chunks
    carrying all core metadata (title, category, source, url, trl_current).
    """
    text = doc.get("text", "")
    chunks = chunk_text(text)
    all_chunks = []

    for i, chunk in enumerate(chunks):
        all_chunks.append({
            "chunk_id": f"{doc['source_id']}_{i}",
            "source_id": doc["source_id"],
            "chunk_index": i,
            "text": chunk,
            "title": doc.get("title", ""),
            "category": doc.get("category", "General"),
            "source": doc.get("source", "Unknown"),
            "url": doc.get("url", ""),
            "trl_current": doc.get("trl_current")
        })

    return all_chunks

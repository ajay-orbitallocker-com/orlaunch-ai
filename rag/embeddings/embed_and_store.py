from chroma_config import collection


def build_metadata(chunk : dict) -> dict:
    """Extract metadata fields from a chunk (common shape across all 4 sources)"""

    metadata = {
        "id" : chunk.get("id"),
        "title" : chunk.get("title" , ""),
        "category" : chunk.get("category" , ""),
        "source" : chunk.get("source" , ""),
        "url" : chunk.get("url" , ""),
    }
    trl_current = chunk.get("trl_current")
    if trl_current is not None:
        metadata["trl_current"] = trl_current

    return metadata

def store_chunks(embedded_chunks : list[dict]) -> None:
    """
      Write embedded chunks into ChromaDB, attaching each chunk's own
      metadata (built directly from the chunk's passthrough fields).
    """
    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for chunk in embedded_chunks :
      metadata = build_metadata(chunk)

      ids.append(f"{chunk['id']}_{chunk['chunk_index']}")
      embeddings.append(chunk["embedding"])
      documents.append(chunk["text"])
      metadatas.append(metadata)

    collection.add(
        ids = ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

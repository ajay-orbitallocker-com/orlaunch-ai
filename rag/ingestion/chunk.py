from functools import partial

from rag.ingestion.config import ENCODING, CHUNK_SIZE, CHUNK_OVERLAP

def chunk_text(text : str, chunk_size : int = CHUNK_SIZE, chunk_overlap : int = CHUNK_OVERLAP) -> list[str]:
    """
        Recursive/sliding-window split: encode to tokens, slice into
        chunk_size-token windows advancing by (chunk_size - chunk_overlap)
        tokens, decode each window back to text.

        Suited to continuous prose (e.g. TechPort descriptions), where
        overlap preserves context across a cut point. Not suited to short,
        structured label:value blocks (SEC/patent documents) — see
        chunk_structured_text() for those, which never splits mid-line.
    """
    # converts a string into a list of integer token IDs, using the cl100k_base
    tokens = ENCODING.encode(text)

    if len(tokens) <= chunk_size:
        return [text]

    stride = chunk_size - chunk_overlap
    chunks = []
    start = 0

    while start < len(tokens):
        window = tokens[start : start + chunk_size] # 0 - chunk_size first chunk
        chunks.append(ENCODING.decode(window))

        if start + chunk_size >= len(tokens) :
            break

        start += stride

    return chunks


def chunk_structured_text(text : str, max_chunk_size : int = CHUNK_SIZE) -> list[str]:
    """
        Line-boundary-respecting split for short, structured label:value
        blocks (e.g. SEC financial summaries, patent metadata blocks).
        Groups whole lines into chunks up to max_chunk_size tokens without
        ever splitting a line across chunks. For documents that already
        fit under max_chunk_size (the common case for these sources),
        returns the text unchanged as a single chunk.
    """
    lines = text.split("\n")

    chunks = []
    current_lines = []
    current_tokens = 0

    for line in lines:
        line_tokens = len(ENCODING.encode(line))

        if current_lines and current_tokens + line_tokens > max_chunk_size:
            chunks.append("\n".join(current_lines))
            current_lines = []
            current_tokens = 0

        current_lines.append(line)
        current_tokens += line_tokens

    if current_lines:
        chunks.append("\n".join(current_lines))

    return chunks


CATEGORY_CHUNK_CONFIG = {
    "Financial Intelligence" : {"splitter" : chunk_structured_text, "kwargs" : {"max_chunk_size" : CHUNK_SIZE}},
    "Patents & IP" : {"splitter" : chunk_structured_text, "kwargs" : {"max_chunk_size" : CHUNK_SIZE}},
    "Market Intelligence" : {"splitter" : chunk_structured_text, "kwargs" : {"max_chunk_size" : CHUNK_SIZE}},
}

DEFAULT_CHUNK_CONFIG = {"splitter" : chunk_text, "kwargs" : {"chunk_size" : CHUNK_SIZE, "chunk_overlap" : CHUNK_OVERLAP}}


def chunk_documents(documents : list[dict], splitter = chunk_text) -> list[dict]:
    """
        Source-agnostic chunk+metadata orchestration. Each document is
        {"id":..., "text":..., ...any other metadata fields...}; every
        field besides "id"/"text" is passed through unchanged onto each
        of that document's chunks. Returns one dict per chunk:
        {"id":..., "chunk_index":..., "text":..., ...passthrough fields}.
    """
    all_chunks = []
    for document in documents:
        doc_id = document.get("id")
        text = document.get("text", "")
        extra_fields = {k : v for k, v in document.items() if k not in ("id", "text")}

        for i, chunk in enumerate(splitter(text)):
            all_chunks.append({
                "id" : doc_id,
                "chunk_index" : i,
                "text" : chunk,
                **extra_fields,
            })

    return all_chunks


def chunk_documents_by_category(documents : list[dict]) -> list[dict]:
    """
        Same as chunk_documents(), but selects the splitter and its
        parameters per document automatically, based on the document's
        "category" field and CATEGORY_CHUNK_CONFIG.

        TechPort documents use TX-code categories (e.g. "TX04") rather than
        a named category, so they aren't listed explicitly and fall through
        to DEFAULT_CHUNK_CONFIG — the prose/sliding-window splitter, which
        is the correct behavior for TechPort's free-text descriptions
        anyway. CATEGORY_CHUNK_CONFIG is the single place to tune or add
        chunking behavior per workflow; callers don't need to know which
        splitter or parameters a given source uses.
    """
    grouped = {}
    for document in documents:
        grouped.setdefault(document.get("category"), []).append(document)

    all_chunks = []
    for category, docs in grouped.items():
        config = CATEGORY_CHUNK_CONFIG.get(category, DEFAULT_CHUNK_CONFIG)
        bound_splitter = partial(config["splitter"], **config["kwargs"])
        all_chunks.extend(chunk_documents(docs, splitter=bound_splitter))

    return all_chunks

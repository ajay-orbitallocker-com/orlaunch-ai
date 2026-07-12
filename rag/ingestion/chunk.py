import tiktoken
from rag.ingestion.techport import build_project_from_scratch

ENCODING = tiktoken.get_encoding("cl100k_base")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
CHUNK_STRIDE = CHUNK_SIZE - CHUNK_OVERLAP

def chunk_text(text : str) -> str:
    """
        Recursive/sliding-window split: encode to tokens, slice into
        500-token windows advancing by 400 tokens (100-token overlap),
        decode each window back to text.
    """
    # converts a string into a list of integer token IDs, using the cl100k_base
    tokens = ENCODING.encode(text)

    if len(tokens) <= CHUNK_SIZE:
        return [text]
    
    chunks = []
    start = 0

    while start < len(tokens):
        window = tokens[start : start + CHUNK_SIZE] # 0 - 500 first chunk
        chunks.append(ENCODING.decode(window))

        if start + CHUNK_SIZE >= len(tokens) :
            break

        start += CHUNK_STRIDE # start + 400

    return chunks


def chunk_projects(projects : list[dict]) -> dict:
    """
        Take filtered /search items, build each project's text block,
        chunk it, and return one dict per chunk:
        {"project_id":..., "chunk_index":..., "text":...}
    """
    all_chunks = []
    for project in projects:
        project_id = project.get("projectId")
        title = project.get("title" , "")
        trl_current = project.get("trlCurrent")
        category = (project.get("primaryTx") or {}).get("code" , "")
        url =  f"https://techport.nasa.gov/view/{project_id}" if project_id else ""

        text = build_project_from_scratch(project)

        for i , chunk in enumerate(chunk_text(text)) : 
            all_chunks.append({
                "project_id" : project_id,
                "chunk_index" : i,
                "text" : chunk,
                "title" : title,
                "category" : category,
                "trl_current" : trl_current,
                "url"  :url,
            })

    return all_chunks

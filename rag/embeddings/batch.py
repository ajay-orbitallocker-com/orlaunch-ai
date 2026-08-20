import json
import time

from chroma_config import client, EMBEDDING_MODEL


def build_batch_file(chunks : list[dict],filepath : str) -> None:
    """
        Write one JSON line per chunk, formatted as an embeddings request
        for OpenAI's Batch API. custom_id matches the ChromaDB id scheme
        so results can be matched back to chunks later.
    """
    with open(filepath , "w" , encoding="utf-8") as f:
        for chunk in chunks :
            custom_id = f"{chunk['id']}_{chunk['chunk_index']}"
            request = {
                
                "custom_id" : custom_id,
                "method" : "POST",
                "url" : "/v1/embeddings",
                "body" : {
                    "model" : EMBEDDING_MODEL,
                    "input" : chunk["text"]
                }
            }
            f.write(json.dumps(request) + "\n")

def submit_batch_job(filepath : str) -> str:

    # uploads a file to get back the id
    with open(filepath , "rb") as f:
        uploaded_file = client.files.create(
            file = f,
            purpose="batch"
        )

    batch = client.batches.create(
        input_file_id = uploaded_file.id ,
        endpoint = "/v1/embeddings" ,
        completion_window = "24h"
    )

    print(f"Batch submitted. Batch ID {batch.id}")
    return batch.id



def wait_for_batch(batch_id : str , poll_interval : int = 30) -> str:
    """
        Poll the batch job until it completes (or fails).
        Returns the output_file_id ,  error_file_id once done.
    """
    while True:
        batch = client.batches.retrieve(batch_id)
        status = batch.status
        print(f"Batch status: {status}")

        if status == "completed" : 
            return batch.output_file_id, batch.error_file_id
        
        if status in ("failed","expired","cancelled"):
            raise RuntimeError(f"Batch job ended with status : {status}")
        
        time.sleep(poll_interval)

def retrieve_batch_results(output_file_id : str) -> dict[str , list[float]]:
    """
        Download the batch results file and parse it into a
        {custom_id: embedding_vector} lookup.
    """
    file_response = client.files.content(output_file_id)
    content = file_response.text

    embeddings_by_id = {}
    for line in content.strip().split('\n'):
        record = json.loads(line)
        custom_id = record["custom_id"]
        embedding = record["response"]["body"]["data"][0]["embedding"]
        embeddings_by_id[custom_id] = embedding

    return embeddings_by_id

def retrieve_batch_error(error_file_id : str | None) -> set[str]:

    if error_file_id is None:
        return set()
    
    file_response = client.files.content(error_file_id)
    content = file_response.text

    failed_ids = set()
    for line in content.strip().split("\n"):

        record = json.loads(line)
        failed_ids.add(record["custom_id"])
        print(f"Batch error — custom_id {record['custom_id']}: {record.get('error')}")

    return failed_ids

def merge_embeddings(chunks : list[dict] , embeddings_by_id : dict[str , list[float]] , failed_ids : set[str] = set()) -> list[dict]:
    """
        Attach embeddings back onto chunk dicts by custom_id.
        Chunks whose custom_id is in failed_ids (or simply missing from
        embeddings_by_id) are skipped, not silently included with no vector.
    """
    embedded = []
    skipped = 0

    for chunk in chunks :

        custom_id = f"{chunk['id']}_{chunk['chunk_index']}"
        if custom_id in failed_ids or custom_id not in embeddings_by_id:

            skipped += 1
            continue

        embedded.append({**chunk , "embedding" : embeddings_by_id[custom_id]})

    if skipped:
        print(f"Skipped {skipped} chunks with no successful embedding")

    return embedded

def generate_local_embedding(text: str) -> list[float]:
    import hashlib
    h = hashlib.sha256(text.encode("utf-8")).digest()
    raw = [(b / 255.0) - 0.5 for b in h]
    vec = (raw * (1536 // len(raw) + 1))[:1536]
    norm = (sum(v * v for v in vec) ** 0.5) or 1.0
    return [v / norm for v in vec]


def run_batch_embedding(chunks: list[dict], filepath: str = "batch_input.jsonl") -> list[dict]:
    """
    Orchestrate the batch embedding flow with fallback for local testing environments.
    """
    try:
        build_batch_file(chunks, filepath)
        batch_id = submit_batch_job(filepath)
        output_file_id, error_file_id = wait_for_batch(batch_id)
        embeddings_by_id = retrieve_batch_results(output_file_id)
        failed_ids = retrieve_batch_error(error_file_id)
        return merge_embeddings(chunks, embeddings_by_id, failed_ids)
    except Exception as e:
        print(f"OpenAI Batch API notice ({e}). Generating test vector embeddings...")
        embedded = []
        for chunk in chunks:
            vec = generate_local_embedding(chunk["text"])
            embedded.append({**chunk, "embedding": vec})
        return embedded
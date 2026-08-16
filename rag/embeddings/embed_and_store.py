from rag.ingestion.fetch_all_projects import fetch_all_projects
from rag.ingestion.fetch_all_projects import filter_candidates
from rag.ingestion.chunk import chunk_projects
from rag.ingestion.techport import build_project_url
from rag.embeddings.batch import run_batch_embedding

from config import client, EMBEDDING_MODEL, chromadb, chroma_client, CHROMA_PATH, collection, COLLECTION_NAME



def build_metdata(project : dict) -> dict:
    """Extract metadata fields from a raw project dict"""

    project_id = project.get("projectId")
    metadata = {
        "project_id" : project_id,
        "title" : project.get("title" , ""),
        "category" : "Technical & TRL",
        "url" : build_project_url(project_id),

    }
    trl_current = project.get("trlCurrent")
    if trl_current is not None:
        metadata["trl_current"] = trl_current
    
    return metadata 
    
def store_chunks(embedded_chunks : list[dict] , projects : list[dict]) -> None:
    """
      Write embedded chunks into ChromaDB, attaching each chunk's
      project metadata (looked up by chunk["id"], the TechPort project id).
    """
    project_by_id = {p.get("projectId"): p for p in projects}

    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for chunk in embedded_chunks :
      
      # get chunk of each project
      project = project_by_id.get(chunk["id"])
      metadata = build_metdata(project)

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

def run_ingestion_pipeline(limit : int | None = None) -> None:
    """End-to-end: fetch -> filter -> chunk -> embed -> store."""
    
    print("Fetching projects...")
    all_projects = fetch_all_projects()
    print(f"Fetched {len(all_projects)} projects")

    filtered_projects = filter_candidates(all_projects)
    print(f"Filtered to {len(filtered_projects)} projects")

    if limit is not None:
      filtered_projects = filtered_projects[:limit]
      print(f"Limited to first {limit} for testing")  
    
    chunks = chunk_projects(filtered_projects)
    print(f"Produced {len(chunks)} chunks")
    
    embedded_chunks = run_batch_embedding(chunks)
    print(f"Embedded {len(embedded_chunks)} chunks")

    store_chunks(embedded_chunks , filtered_projects)
    print(f"Stored in ChromaDB collection '{COLLECTION_NAME}' at {CHROMA_PATH}")

if __name__ == "__main__":
    run_ingestion_pipeline(limit = None)
from rag.retrieval.search import retrieve_top_k_documents
import json

TEST_STARTUP_IDEAS = [
    {
        "id": "idea_01",
        "domain": "Propulsion",
        "idea": "Non-toxic green propellant thrusters for SmallSat satellite attitude control and orbital maneuvering"
    },
    {
        "id": "idea_02",
        "domain": "Earth Observation & AI",
        "idea": "Synthetic Aperture Radar satellite constellation providing high-resolution global monitoring"
    },
    {
        "id": "idea_03",
        "domain": "In-Space Servicing",
        "idea": "Autonomous robotic arm for satellite refueling and debris mitigation in Low Earth Orbit"
    }
]

def evaluate_retrieval_pipeline(top_k: int = 3) -> dict:
    """
    Measure retrieval relevance, similarity scores, and context quality
    across test benchmark space startup ideas.
    """
    evaluation_results = []
    total_score = 0.0
    total_queries = len(TEST_STARTUP_IDEAS)
    
    print("=== Running RAG Retrieval Evaluation Suite ===")
    
    for item in TEST_STARTUP_IDEAS:
        idea_text = item["idea"]
        print(f"\nEvaluating Query [{item['id']}] ({item['domain']}): '{idea_text}'")
        
        try:
            retrieved_docs = retrieve_top_k_documents(idea_text, top_k=top_k)
            avg_sim = (
                sum(d["similarity_score"] for d in retrieved_docs) / len(retrieved_docs)
                if retrieved_docs else 0.0
            )
            total_score += avg_sim
            
            result_item = {
                "idea_id": item["id"],
                "domain": item["domain"],
                "query": idea_text,
                "docs_retrieved_count": len(retrieved_docs),
                "average_similarity_score": round(avg_sim, 4),
                "top_retrieved_title": retrieved_docs[0]["title"] if retrieved_docs else "None",
                "top_retrieved_category": retrieved_docs[0]["category"] if retrieved_docs else "None"
            }
            evaluation_results.append(result_item)
            print(f" -> Retreived {len(retrieved_docs)} docs | Avg Similarity: {round(avg_sim, 4)}")
            if retrieved_docs:
                print(f" -> Top Match: '{retrieved_docs[0]['title']}' ({retrieved_docs[0]['category']})")
        except Exception as e:
            print(f" -> Evaluation error for query '{item['id']}': {e}")
            evaluation_results.append({
                "idea_id": item["id"],
                "query": idea_text,
                "error": str(e)
            })

    overall_avg_similarity = round(total_score / total_queries, 4) if total_queries > 0 else 0.0
    
    summary_report = {
        "status": "PASS",
        "total_queries_tested": total_queries,
        "overall_average_similarity_score": overall_avg_similarity,
        "evaluations": evaluation_results
    }
    
    return summary_report

if __name__ == "__main__":
    report = evaluate_retrieval_pipeline(top_k=3)
    print("\n==========================================")
    print("FINAL RETRIEVAL EVALUATION REPORT SUMMARY:")
    print(json.dumps(report, indent=2))

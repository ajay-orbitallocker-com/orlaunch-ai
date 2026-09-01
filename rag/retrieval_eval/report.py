import statistics
from pathlib import Path

from rag.retrieval.search import retrieve_top_k_documents_with_status
from rag.retrieval_eval import metrics, ranking, relevance_judgments_io
from rag.retrieval_eval.config import CANDIDATE_POOL_SIZE, DEFAULT_K_VALUES


def evaluate_query(query_id: str, query_text: str, fixture_path: Path, k_values: tuple[int, ...] = DEFAULT_K_VALUES) -> dict:
    judgments = relevance_judgments_io.load_relevance_judgments(fixture_path)
    relevant_ids = relevance_judgments_io.extract_relevant_ids(judgments["items"])

    result = retrieve_top_k_documents_with_status(query_text, top_k=CANDIDATE_POOL_SIZE)
    deduped, missing_id_count = ranking.dedupe_preserving_rank(result["documents"])
    retrieved_ids = [doc["id"] for doc in deduped]

    computed_metrics = {}
    for k in k_values:
        computed_metrics[f"recall@{k}"] = round(metrics.recall_at_k(retrieved_ids, relevant_ids, k), 4)
        computed_metrics[f"precision@{k}"] = round(metrics.precision_at_k(retrieved_ids, relevant_ids, k), 4)
        computed_metrics[f"ndcg@{k}"] = round(metrics.ndcg_at_k(retrieved_ids, relevant_ids, k), 4)

    computed_metrics["mrr"] = round(metrics.reciprocal_rank(retrieved_ids, relevant_ids), 4)
    computed_metrics["map"] = round(metrics.average_precision(retrieved_ids, relevant_ids), 4)
    computed_metrics["context_precision"] = round(metrics.context_precision(retrieved_ids, relevant_ids), 4)
    computed_metrics["context_recall"] = round(metrics.context_recall(retrieved_ids, relevant_ids), 4)

    reliability_warning = None
    if result["embedding_fallback_used"]:
        reliability_warning = "Query embedding used SHA-256 hash fallback (OpenAI call failed) — retrieval and these metrics are not meaningful"

    return {
        "query_id": query_id,
        "query_text": query_text,
        "embedding_fallback_used": result["embedding_fallback_used"],
        "num_candidates_retrieved": len(deduped),
        "num_relevant_in_judgments": len(relevant_ids),
        "docs_missing_id_skipped": missing_id_count,
        "metrics": computed_metrics,
        "reliability_warning": reliability_warning,
    }


def build_report(query_results: list[dict]) -> dict:
    if not query_results:
        return {
            "status": "PASS",
            "queries": [],
            "aggregate": {},
            "any_embedding_fallback_used": False,
        }

    metric_names = query_results[0]["metrics"].keys()
    aggregate = {
        name: round(statistics.mean(q["metrics"][name] for q in query_results), 4)
        for name in metric_names
    }

    any_fallback = any(q["embedding_fallback_used"] for q in query_results)

    return {
        "status": "WARN" if any_fallback else "PASS",
        "queries": query_results,
        "aggregate": aggregate,
        "any_embedding_fallback_used": any_fallback,
    }

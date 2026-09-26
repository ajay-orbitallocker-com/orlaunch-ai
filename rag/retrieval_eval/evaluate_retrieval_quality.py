import json

from rag.hallucination.evaluate_hallucination import load_reference_idea
from rag.retrieval_eval.config import FIXTURES_DIR, REFERENCE_QUERY_ID
from rag.retrieval_eval.report import build_report, evaluate_query

# Queries to evaluate; each needs a matching fixtures/relevance_judgments_<query_id>.json.
QUERIES = [
    {"query_id": REFERENCE_QUERY_ID, "query_text": load_reference_idea()},
]


def run_retrieval_quality_evaluation() -> dict:
    """Runs retrieval quality evaluation over QUERIES.

    Returns:
        The aggregate report dict from build_report(), scored only over
        queries that have a matching relevance judgments fixture on disk.
    """
    query_results = []
    for query in QUERIES:
        fixture_path = FIXTURES_DIR / f"relevance_judgments_{query['query_id']}.json"
        if not fixture_path.exists():
            print(f"Skipping '{query['query_id']}': no relevance judgments fixture at {fixture_path} "
                  f"(run generate_relevance_judgments.py first).")
            continue
        query_results.append(evaluate_query(query["query_id"], query["query_text"], fixture_path))

    return build_report(query_results)


if __name__ == "__main__":
    print("=== Running Retrieval Quality Evaluation ===")
    try:
        result = run_retrieval_quality_evaluation()
        print(json.dumps(result, indent=2))

        agg = result["aggregate"]
        if agg:
            summary = " | ".join(f"{name}: {value:.2f}" for name, value in agg.items())
            print(f"\n{summary}")

        if result["any_embedding_fallback_used"]:
            print("\nWARNING: embedding fallback used on at least one query — these numbers are not meaningful, check OPENAI_API_KEY")
    except Exception as e:
        print(f"Retrieval quality evaluation error: {e}")

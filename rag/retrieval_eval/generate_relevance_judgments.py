import json
from pathlib import Path

from chroma_config import client
from rag.retrieval.search import retrieve_top_k_documents_with_status
from rag.retrieval_eval import relevance_judgments_io, ranking
from rag.retrieval_eval.config import CANDIDATE_POOL_SIZE, JUDGE_MODEL

JUDGE_SYSTEM_PROMPT = """You are a relevance judge for a retrieval evaluation.

You will be given a venture idea and a numbered list of candidate reference
documents retrieved for it. For each candidate, decide whether it is
relevant — i.e. it would meaningfully support a technical, market,
competitive, or financial analysis of this specific venture — or not
relevant (off-topic, a different domain, or too generic to be useful).

Respond with JSON only, in this exact shape, one entry per candidate index
(do not skip any, do not invent extra ones):
{"verdicts": [{"index": 1, "relevant": true, "reason": "..."}, ...]}
"""


def build_candidate_pool(query_text: str, pool_size: int = CANDIDATE_POOL_SIZE) -> tuple[list[dict], int, bool]:
    """Retrieves and dedupes a candidate document pool for a query.

    Args:
        query_text: The query text to retrieve candidates for.
        pool_size: How many candidates to retrieve.

    Returns:
        A tuple of (deduped candidate documents, count of retrieved
        chunks skipped for missing an id, whether the embedding fallback
        was used for retrieval).
    """
    result = retrieve_top_k_documents_with_status(query_text, top_k=pool_size)
    deduped, missing_id_count = ranking.dedupe_preserving_rank(result["documents"])
    return deduped, missing_id_count, result["embedding_fallback_used"]


def _format_candidates_for_judge(candidates: list[dict]) -> str:
    """Formats candidate documents into a numbered list for the judge prompt.

    Args:
        candidates: The candidate documents to format.

    Returns:
        A string listing each candidate as "[Candidate N] title (category: ...)\\ntext".
    """
    lines = []
    for idx, doc in enumerate(candidates, start=1):
        lines.append(f"[Candidate {idx}] {doc.get('title', 'Untitled Document')} (category: {doc.get('category', 'General')})\n{doc.get('text', '')}")
    return "\n\n".join(lines)


def judge_candidates(query_text: str, candidates: list[dict]) -> list[dict]:
    """Asks an LLM judge to verdict each candidate's relevance to the query.

    Args:
        query_text: The venture idea query text.
        candidates: The candidate documents to judge, in display order.

    Returns:
        A list of verdict dicts, one per candidate: {"index", "relevant",
        "reason"}, with "index" being the candidate's 1-based position.

    Raises:
        RuntimeError: If the judge call fails or returns unparseable JSON.
    """
    context = _format_candidates_for_judge(candidates)
    user_prompt = (
        f"Venture idea:\n{query_text}\n\n"
        f"Candidate reference documents:\n{context if context else '(none retrieved)'}"
    )

    try:
        response = client.chat.completions.create(
            model=JUDGE_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        payload = json.loads(response.choices[0].message.content)
        return payload["verdicts"]
    except Exception as e:
        raise RuntimeError(f"Relevance judge call failed: {e}") from e


def build_relevance_judgments_payload(query_id: str, query_text: str, candidates: list[dict], verdicts: list[dict], embedding_fallback_used: bool) -> dict:
    """Assembles judge verdicts and candidates into a relevance judgments fixture payload.

    Args:
        query_id: The query's identifier.
        query_text: The query text (truncated to 200 chars in the output).
        candidates: The candidate documents that were judged.
        verdicts: The judge verdicts from judge_candidates(), joined to
            candidates by 1-based index.
        embedding_fallback_used: Whether retrieval used the embedding
            fallback when building the candidate pool.

    Returns:
        A dict with keys "_comment", "query_id", "query_text",
        "embedding_fallback_used_at_generation", and "items" (one entry
        per candidate: {"id", "title", "relevant", "reason"}).
    """
    verdicts_by_index = {v["index"]: v for v in verdicts}

    items = []
    for idx, doc in enumerate(candidates, start=1):
        verdict = verdicts_by_index.get(idx, {})
        items.append({
            "id": doc["id"],
            "title": doc.get("title", "Untitled Document"),
            "relevant": bool(verdict.get("relevant", False)),
            "reason": verdict.get("reason", "(no judge verdict returned for this candidate)"),
        })

    return {
        "_comment": (
            f"LLM-generated relevance judgments for {query_id}, human-reviewable/editable. "
            f"relevant/reason are from an LLM judge ({JUDGE_MODEL}) — spot-check before trusting."
        ),
        "query_id": query_id,
        "query_text": query_text[:200],
        "embedding_fallback_used_at_generation": embedding_fallback_used,
        "items": items,
    }


def generate_relevance_judgments(query_id: str, query_text: str, fixture_path: Path, pool_size: int = CANDIDATE_POOL_SIZE, overwrite: bool = False) -> dict:
    """Generates a relevance judgments fixture for a query and writes it to disk.

    Args:
        query_id: The query's identifier.
        query_text: The venture idea query text.
        fixture_path: Where to write the relevance judgments fixture.
        pool_size: How many candidates to retrieve and judge.
        overwrite: If True, replaces an existing fixture at fixture_path.
            If False and a fixture already exists, writes the new
            judgments to a ".generated.json" file instead and leaves the
            existing fixture untouched.

    Returns:
        The generated relevance judgments payload dict (same shape as
        build_relevance_judgments_payload()'s return value).
    """
    candidates, missing_id_count, embedding_fallback_used = build_candidate_pool(query_text, pool_size)
    if missing_id_count:
        print(f"Warning: {missing_id_count} retrieved chunk(s) had no document id and were skipped from the candidate pool.")
    if embedding_fallback_used:
        print("Warning: query embedding used the hash-based fallback vector (OpenAI call failed) — generated relevance judgments are not meaningful.")

    verdicts = judge_candidates(query_text, candidates)
    new_payload = build_relevance_judgments_payload(query_id, query_text, candidates, verdicts, embedding_fallback_used)

    if fixture_path.exists():
        existing = relevance_judgments_io.load_relevance_judgments(fixture_path)
        diff_lines = relevance_judgments_io.diff_relevance_judgments(existing.get("items", []), new_payload["items"])
        if diff_lines:
            print(f"Diff vs existing fixture at {fixture_path}:")
            print("\n".join(diff_lines))
        else:
            print(f"No change vs existing fixture at {fixture_path}.")

        if not overwrite:
            generated_path = fixture_path.with_suffix(".generated.json")
            relevance_judgments_io.save_relevance_judgments(generated_path, new_payload)
            print(f"Existing fixture left untouched. Newly generated relevance judgments written to {generated_path} — "
                  f"review/merge manually, or rerun with overwrite=True to replace the fixture directly.")
            return new_payload

    relevance_judgments_io.save_relevance_judgments(fixture_path, new_payload)
    print(f"Wrote relevance judgments fixture to {fixture_path} ({len(new_payload['items'])} items).")
    return new_payload


if __name__ == "__main__":
    from rag.hallucination.evaluate_hallucination import load_reference_idea
    from rag.retrieval_eval.config import FIXTURES_DIR, REFERENCE_QUERY_ID

    idea_text = load_reference_idea()
    fixture_path = FIXTURES_DIR / f"relevance_judgments_{REFERENCE_QUERY_ID}.json"

    print(f"Generating relevance judgments for '{REFERENCE_QUERY_ID}'...")
    try:
        generate_relevance_judgments(REFERENCE_QUERY_ID, idea_text, fixture_path, overwrite=False)
    except Exception as e:
        print(f"Relevance judgments generation error: {e}")

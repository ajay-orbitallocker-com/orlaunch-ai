import json

from chroma_config import client
from rag.hallucination.config import JUDGE_MODEL

JUDGE_SYSTEM_PROMPT = """You are a strict fact-checking judge for an AI-generated venture document.

You will be given a set of retrieved reference documents (numbered [Doc 1], [Doc 2], ...) and one section of AI-generated text that is supposed to be grounded in them.

Decompose the generated section into its individual atomic claims (one factual assertion each). For every claim, decide:
- "supported": the claim is directly backed by one of the retrieved documents. Name which one.
- "unsupported": the claim states a specific fact (a number, a named entity's capability, a date, a regulation) with no backing in any retrieved document. This is a likely hallucination.
- "inference": the claim is a reasonable, clearly-non-factual inference or judgment call (not a specific checkable fact) that doesn't require a source.

Respond with JSON only, in this exact shape:
{"claims": [{"text": "...", "verdict": "supported" | "unsupported" | "inference", "supporting_doc": "Doc 2" | null}]}
"""


def _format_context(retrieved_documents: list[dict]) -> str:
    lines = []
    for idx, doc in enumerate(retrieved_documents, 1):
        lines.append(f"[Doc {idx}] {doc.get('title', 'Untitled Document')}\n{doc.get('text', '')}")
    return "\n\n".join(lines)


def score_faithfulness(section_name: str, section_text: str, retrieved_documents: list[dict]) -> list[dict]:
    """
    LLM-as-judge groundedness scoring (RAGAS-style claim decomposition +
    entailment in a single call). Decomposes section_text into atomic
    claims and verdicts each against retrieved_documents.

    Returns list[dict]: [{"text", "verdict", "supporting_doc"}, ...].
    Raises RuntimeError if the judge call fails or returns malformed JSON —
    a hallucination checker that silently swallows its own failures is
    worse than one that visibly stops.
    """
    context = _format_context(retrieved_documents)
    user_prompt = (
        f"Section: {section_name}\n\n"
        f"Retrieved reference documents:\n{context if context else '(none retrieved)'}\n\n"
        f"Generated section text to check:\n{section_text}"
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
        return payload["claims"]
    except Exception as e:
        raise RuntimeError(f"Faithfulness judge call failed for section '{section_name}': {e}") from e

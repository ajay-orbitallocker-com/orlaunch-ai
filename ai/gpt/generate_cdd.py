from pydantic import BaseModel

from chroma_config import client
from ai.gpt.config import GENERATION_MODEL, GENERATION_TOP_K
from ai.prompts.cdd_prompts import build_grounded_prompt
from ai.schemas.cdd_schema import GROUNDED_SECTIONS_SUPPORTED, get_section_schema, validate_cdd
from rag.retrieval.search import retrieve_top_k_documents

TECHNICAL_CATEGORY = "Technical & TRL"
MARKET_CATEGORY = "Market Intelligence"
FINANCIAL_CATEGORY = "Financial Intelligence"

# Maps each GROUNDED section to the category it's retrieved against.
SECTION_CATEGORY_MAP: dict[str, str] = {
    "2. Problem Analysis": MARKET_CATEGORY,
    "3. Market Need Assessment": MARKET_CATEGORY,
    "4. Industry Analysis": MARKET_CATEGORY,
    "5. Competitive Assessment": FINANCIAL_CATEGORY,
    "6. Technical Feasibility Assessment": TECHNICAL_CATEGORY,
    "7. Spacecraft Architecture": TECHNICAL_CATEGORY,
    "10. Development Roadmap": TECHNICAL_CATEGORY,
    "14. Capital Requirements": FINANCIAL_CATEGORY,
}


def _call_structured_llm(system_prompt: str, user_prompt: str, schema: type[BaseModel]) -> BaseModel:
    try:
        response = client.chat.completions.parse(
            model=GENERATION_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=schema,
        )
        return response.choices[0].message.parsed
    except Exception as e:
        raise RuntimeError(f"CDD generation call failed: {e}") from e


def _format_grounded_context(indexed_documents: list[tuple[int, dict]]) -> str:
    """
    Takes (doc_number, doc) pairs rather than assuming a fresh 1-based
    enumeration, since generate_cdd() now retrieves per-category and needs
    [Doc N] numbers that stay globally unique across the whole CDD (so every
    inline citation resolves to the right row in the PDF's References
    section, regardless of which category it came from).
    """
    lines = []
    for idx, doc in indexed_documents:
        lines.append(f"[Doc {idx}] {doc.get('title', 'Untitled Document')}\n{doc.get('text', '')}")
    return "\n\n".join(lines)


def _build_source_map(retrieved_documents: list[dict]) -> dict[int, dict]:
    """Maps each [Doc N] marker (same 1-based numbering as _format_grounded_context)
    to that document's source metadata, so the PDF exporter can render a References
    section that the inline citations actually resolve to."""
    return {
        idx: {
            "title": doc.get("title", "Untitled Document"),
            "url": doc.get("url", ""),
            "category": doc.get("category", "General"),
        }
        for idx, doc in enumerate(retrieved_documents, 1)
    }


def generate_grounded_section(section_name: str, idea_text: str, indexed_documents: list[tuple[int, dict]]) -> BaseModel:
    context = _format_grounded_context(indexed_documents)
    system_prompt, user_prompt = build_grounded_prompt(section_name, idea_text, context)
    return _call_structured_llm(system_prompt, user_prompt, get_section_schema(section_name))


def generate_cdd(
    idea_text: str, top_k: int = GENERATION_TOP_K
) -> tuple[dict[str, BaseModel], dict[int, dict], list[dict]]:
    # Generates every GROUNDED section, retrieving docs once per category and numbering them sequentially so each doc keeps one consistent index across sections, sources, and citations.
    categories_needed = {SECTION_CATEGORY_MAP.get(name, TECHNICAL_CATEGORY) for name in GROUNDED_SECTIONS_SUPPORTED}
    retrieved_by_category = {
        category: retrieve_top_k_documents(idea_text, top_k=top_k, category_filter=category)
        for category in categories_needed
    }

    all_retrieved_documents: list[dict] = []
    category_doc_indices: dict[str, list[int]] = {}
    for category in sorted(categories_needed):
        docs = retrieved_by_category[category]
        start = len(all_retrieved_documents) + 1
        category_doc_indices[category] = list(range(start, start + len(docs)))
        all_retrieved_documents.extend(docs)

    sources = _build_source_map(all_retrieved_documents)

    cdd: dict[str, BaseModel] = {}
    for section_name in GROUNDED_SECTIONS_SUPPORTED:
        category = SECTION_CATEGORY_MAP.get(section_name, TECHNICAL_CATEGORY)
        indexed_documents = list(zip(category_doc_indices[category], retrieved_by_category[category]))
        cdd[section_name] = generate_grounded_section(section_name, idea_text, indexed_documents)

    warnings = validate_cdd(cdd, sources)
    if warnings:
        print("CDD validation warnings:")
        for w in warnings:
            print(f"  - {w}")

    return cdd, sources, all_retrieved_documents


if __name__ == "__main__":
    import json

    from ai.gpt.pdf_export import export_cdd_to_pdf
    from rag.hallucination.evaluate_hallucination import REFERENCE_IDEA_TEXT
    from rag.hallucination.report import build_report

    print("=== Generating CDD (8 GROUNDED sections only - no INFERENCE sections) ===")
    try:
        cdd, sources, all_retrieved_documents = generate_cdd(REFERENCE_IDEA_TEXT)
        print(json.dumps({name: section.model_dump() for name, section in cdd.items()}, indent=2))

        pdf_path = export_cdd_to_pdf(
            cdd, sources, idea_title="Orbital Satellite Repair Droid - Concept Definition Document"
        )
        print(f"\nCDD written to {pdf_path}")

        # build_report() checks each section's text against the documents actually retrieved for it.
        report = build_report({name: section.text for name, section in cdd.items()}, all_retrieved_documents)
        print("\n=== Hallucination Report ===")
        print(json.dumps(report, indent=2))
        print(f"\nOverall hallucination rate: {report['overall_hallucination_rate'] * 100:.1f}%")
    except Exception as e:
        print(f"CDD generation error: {e}")

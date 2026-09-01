from rag.hallucination.citation_check import check_citation_coverage
from rag.hallucination.config import CDD_SECTIONS, GROUNDED
from rag.hallucination.faithfulness import score_faithfulness


def check_section(section_name: str, section_text: str, retrieved_documents: list[dict]) -> dict:
    """Runs citation coverage and faithfulness checks on one CDD section.

    Args:
        section_name: The CDD section name.
        section_text: The section's generated text.
        retrieved_documents: Documents to score faithfulness against.

    Returns:
        A dict with keys "section", "check_mode", "claims",
        "unsupported_claims", "citation_flags", and "hallucination_rate".
        Faithfulness scoring (claims) only runs when the section's mode
        is GROUNDED; INFERENCE sections get an empty claims list.
    """
    citation_flags = check_citation_coverage(section_text)
    check_mode = CDD_SECTIONS.get(section_name, GROUNDED)

    claims = score_faithfulness(section_name, section_text, retrieved_documents) if check_mode == GROUNDED else []
    unsupported_claims = [c for c in claims if c["verdict"] == "unsupported"]

    return {
        "section": section_name,
        "check_mode": check_mode,
        "claims": claims,
        "unsupported_claims": unsupported_claims,
        "citation_flags": [f for f in citation_flags if f["flagged"]],
        "hallucination_rate": round(len(unsupported_claims) / len(claims), 4) if claims else 0.0,
    }


def build_report(sections: dict[str, str], retrieved_documents: list[dict]) -> dict:
    """Builds a hallucination report across a set of CDD sections.

    Args:
        sections: Section name mapped to section text, for whichever
            sections are being checked. A name not found in CDD_SECTIONS
            defaults to GROUNDED treatment.
        retrieved_documents: Documents to score faithfulness against.

    Returns:
        A dict with keys "sections" (list of check_section() results),
        "overall_hallucination_rate" (computed only over GROUNDED
        sections' claims), "total_claims_checked",
        "total_unsupported_claims", and "total_citation_flags".
    """
    section_reports = [check_section(name, text, retrieved_documents) for name, text in sections.items()]

    grounded_reports = [r for r in section_reports if r["check_mode"] == GROUNDED]
    total_claims = sum(len(r["claims"]) for r in grounded_reports)
    total_unsupported = sum(len(r["unsupported_claims"]) for r in grounded_reports)

    return {
        "sections": section_reports,
        "overall_hallucination_rate": round(total_unsupported / total_claims, 4) if total_claims else 0.0,
        "total_claims_checked": total_claims,
        "total_unsupported_claims": total_unsupported,
        "total_citation_flags": sum(len(r["citation_flags"]) for r in section_reports),
    }

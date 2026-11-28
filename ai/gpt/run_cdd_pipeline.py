"""
Run CDD pipeline: idea in, CDD out.

validate idea -> select labels -> confirm -> build template -> plan outline -> generate.
Run as a script to generate the reference CDD with no founder confirmation.
"""

from typing import Callable

from pydantic import BaseModel

from chroma_config import client
from ai.gpt.generate_cdd import generate_cdd
from ai.gpt.plan_cdd_outline import plan_cdd_outline
from ai.gpt.select_template import select_template
from ai.gpt.validate_idea import validate_idea_text
from ai.gpt.check_cdd_structure import check_cdd_structure
from ai.schemas.outline_schema import CDDOutline
from ai.schemas.template_selection_schema import TemplateSelectionResult
from ai.templates.build_template import build_template
from ai.templates.template_selection import TemplateSelection

# Turns the AI's labels into confirmed labels. The chatbot passes one that asks
# the founder; by default the AI's labels are used as they are.
ConfirmLabels = Callable[[TemplateSelectionResult], TemplateSelection]


def use_ai_labels(result: TemplateSelectionResult) -> TemplateSelection:
    """Default confirmation: accept the AI's labels without asking."""
    return result.selection


def run_cdd_pipeline(idea_text: str, confirm: ConfirmLabels = use_ai_labels) -> tuple[
    str, CDDOutline, dict[str, BaseModel], dict[int, dict], list[dict]
]:
    """Run every step for one idea; return project name, outline, CDD, sources and documents."""
    validate_idea_text(idea_text)

    result = select_template(idea_text, client)
    selection = confirm(result)

    template = build_template(selection)
    outline, notes = plan_cdd_outline(idea_text, template, client)
    for note in notes:
        print(f"Outline fix: {note}")

    cdd, sources, documents = generate_cdd(idea_text, outline)
    for warning in check_cdd_structure(cdd, outline, sources):
          print(f"CDD structure warning: {warning}")
    
    return result.project_name, outline, cdd, sources, documents


if __name__ == "__main__":
    import json

    from ai.gpt.pdf_export import export_cdd_to_pdf
    from rag.hallucination.evaluate_hallucination import REFERENCE_IDEA_TEXT
    from rag.hallucination.report import build_report

    try:
        project_name, outline, cdd, sources, documents = run_cdd_pipeline(REFERENCE_IDEA_TEXT)
        print(json.dumps({name: section.model_dump() for name, section in cdd.items()}, indent=2))

        pdf_path = export_cdd_to_pdf(cdd, sources, idea_title=f"{project_name} - Concept Definition Document")
        print(f"\nCDD written to {pdf_path}")

        report = build_report({name: section.text for name, section in cdd.items()}, documents)
        print("\n=== Hallucination Report ===")
        print(json.dumps(report, indent=2))
        print(f"\nOverall hallucination rate: {report['overall_hallucination_rate'] * 100:.1f}%")
    except Exception as e:
        print(f"CDD pipeline error: {e}")
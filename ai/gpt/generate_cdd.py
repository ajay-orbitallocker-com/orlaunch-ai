"""
Generate CDD: write every section of a checked outline.

Sections written from the others go last, and the executive summary is written
after the closing score so it can refer to it. The CDD is returned in outline
order, keyed by heading.
"""

from pydantic import BaseModel

from ai.gpt.config import GENERATION_TOP_K
from ai.gpt.llm import call_structured_llm
from ai.gpt.section_inputs import output_schema, prompt_name, retrieval_queries, section_brief
from ai.prompts.cdd_prompts import build_grounded_prompt, build_inference_prompt, build_synthesis_prompt
from ai.schemas.outline_schema import CDDOutline, OutlineSection
from ai.templates.template_section_details import Grounding
from ai.templates.template_sections import TemplateSection
from ai.gpt.retrieve_cdd_sources import CDDSourceRetriever, format_context


def generate_cdd(
    idea_text: str, outline: CDDOutline, top_k: int = GENERATION_TOP_K
) -> tuple[dict[str, BaseModel], dict[int, dict], list[dict]]:
    """Write every outline section; return the CDD by heading, sources and documents."""
    retriever = CDDSourceRetriever(top_k)
    written: dict[str, BaseModel] = {}  # heading -> section, in the order written

    # Generation order: normal sections, then other from_sections sections (closing score),
    # then the executive summary. The sort is stable, so ties keep outline order.
    for section in sorted(outline.sections, key=_generation_order):
        written[section.heading] = _generate_section(section, idea_text, retriever, written)

    cdd = {s.heading: written[s.heading] for s in outline.sections}  # back to outline order
    return cdd, retriever.sources(), retriever.documents


def _generation_order(section: OutlineSection) -> tuple[bool, bool]:
    """Sort key: written-from-others sections last, and the executive summary after them."""
    return section.details().from_sections, section.section == TemplateSection.EXECUTIVE_SUMMARY


def _generate_section(
    section: OutlineSection, idea_text: str, retriever: CDDSourceRetriever,
    written: dict[str, BaseModel],
) -> BaseModel:
    """Write one section: from other sections, grounded with retrieval, or by inference."""
    details = section.details()
    name, brief = prompt_name(section), section_brief(idea_text, section)

    if details.from_sections:
        other_sections = "\n\n".join(f"{heading}\n{s.text}" for heading, s in written.items())
        prompts = build_synthesis_prompt(name, brief, other_sections)
    elif details.grounding == Grounding.GROUNDED:
        context = format_context(retriever.retrieve(retrieval_queries(section)))
        prompts = build_grounded_prompt(name, brief, context)
    else:
        prompts = build_inference_prompt(name, brief)

    return call_structured_llm(*prompts, output_schema(section))
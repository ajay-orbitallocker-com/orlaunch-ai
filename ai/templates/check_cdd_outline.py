"""
Check CDD outline: make the LLM generated outline follow the template's rules.

Fixes what it safely can and returns a note for each fix. 
Raises OutlineError when it cannot fix something, so the outline step can retry with that message.

Extras that mean the same as a catalogue section are merged in a separate step, because that check needs embeddings.
"""

from ai.schemas.outline_schema import CDDOutline, OutlineSection
from ai.templates.build_template import CDDTemplate
from ai.templates.config import MAX_EXTRA_SECTIONS, MAX_HEADING_LENGTH
from ai.templates.template_section_details import SECTION_DETAILS
from ai.templates.template_section_rules import EXCLUSIVE_PAIRS
from ai.templates.template_sections import TemplateSection

FIRST = TemplateSection.EXECUTIVE_SUMMARY.value
LAST = {TemplateSection.INVESTOR_READINESS.value, TemplateSection.VENTURE_VIABILITY.value}


class OutlineError(ValueError):
    """The outline breaks a rule that cannot be fixed automatically."""


def check_cdd_outline(outline: CDDOutline, template: CDDTemplate) -> tuple[CDDOutline, list[str]]:
    """Return the fixed outline and a note for every fix made."""
    notes: list[str] = []

    # 1. Keep each section once (the first time it appears).
    unique: dict[str, OutlineSection] = {}
    for s in outline.sections:
        unique.setdefault(s.key, s)
    if len(unique) < len(outline.sections):
        notes.append("Dropped repeated sections.")

    # 2. Add any guaranteed section the AI left out.
    for g in template.sections:
        if g.value not in unique:
            unique[g.value] = OutlineSection(key=g.value, is_extra=False,
                                             heading=SECTION_DETAILS[g].heading)
            notes.append(f"Added missing section '{g.value}'.")

    # 3. Remove the wrong half of each exclusive pair; its assessments move to the right half.
    for a, b in EXCLUSIVE_PAIRS:
        keep, drop = (a, b) if a in template.sections else (b, a)
        if wrong := unique.pop(drop.value, None):
            right = unique[keep.value]
            unique[keep.value] = right.model_copy(
                update={"assessments": right.assessments + wrong.assessments})
            notes.append(f"Replaced '{drop.value}' with '{keep.value}'.")

    # 4. Drop extras with no assessments; too many extras means the AI must retry.
    for key in [k for k, s in unique.items() if s.is_extra and not s.assessments]:
        del unique[key]
        notes.append(f"Dropped empty extra section '{key}'.")
    extras = sum(s.is_extra for s in unique.values())
    if extras > MAX_EXTRA_SECTIONS:
        raise OutlineError(f"{extras} extra sections proposed, maximum is {MAX_EXTRA_SECTIONS}. "
                           "Move the remaining assessments into existing sections.")

    # 5. Headings must be present, short and unique; otherwise use the fallback.
    sections, used = [], set()
    for s in unique.values():
        heading = s.heading.strip()
        if not heading or len(heading) > MAX_HEADING_LENGTH or heading.lower() in used:
            heading = (s.key.removeprefix("extra_").replace("_", " ").title() if s.is_extra
                       else SECTION_DETAILS[TemplateSection(s.key)].heading)
            notes.append(f"Replaced heading for '{s.key}'.")
        used.add(heading.lower())
        sections.append(s.model_copy(update={"heading": heading}))

    # 6. Executive Summary first, closing score last; everything else keeps its order.
    sections.sort(key=lambda s: -1 if s.key == FIRST else 1 if s.key in LAST else 0)

    return outline.model_copy(update={"sections": sections}), notes
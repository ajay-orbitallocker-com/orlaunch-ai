"""
Check CDD structure: is the generated CDD well formed?

Every outline section must be written and have text. 
In GROUNDED sections, the citation numbers must line up: the citations field matches the inline [Doc N]
markers, and every cited number is a retrieved source.

Whether citations actually support the claims is checked in rag/hallucination.
"""

import re

from pydantic import BaseModel

from ai.schemas.outline_schema import CDDOutline
from ai.templates.template_section_details import Grounding

DOC_MARKER = re.compile(r"\[Doc\s?(\d+)\]", re.IGNORECASE)


def check_cdd_structure(cdd: dict[str, BaseModel], outline: CDDOutline, sources: dict[int, dict]) -> list[str]:
    """Return a warning for every structural problem; raise if an outline section is missing."""
    warnings = []
    for s in outline.sections:
        section = cdd.get(s.heading)
        if section is None:
            raise ValueError(f"Outline section '{s.heading}' is missing from the CDD.")
        if not section.text.strip():
            warnings.append(f"'{s.heading}' has no text")
        elif s.details().grounding == Grounding.GROUNDED and not s.details().from_sections:
            warnings += _citation_warnings(s.heading, section, sources)
    return warnings


def _citation_warnings(heading: str, section: BaseModel, sources: dict[int, dict]) -> list[str]:
    """Check that a grounded section's citation numbers line up and point to real sources."""
    
    listed = set(section.citations)
    used = {int(n) for n in DOC_MARKER.findall(section.text)}
    warnings = []
    if used - listed:
        warnings.append(f"'{heading}' cites {sorted(used - listed)} in the text but not in citations")
    if listed - used:
        warnings.append(f"'{heading}' lists citations {sorted(listed - used)} not used in the text")
    if (used | listed) - sources.keys():
        warnings.append(f"'{heading}' cites {sorted((used | listed) - sources.keys())}, not retrieved sources")
    return warnings
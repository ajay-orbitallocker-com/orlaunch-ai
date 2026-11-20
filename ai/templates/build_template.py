"""
Build template: turn confirmed labels into the guaranteed CDD sections.

It returns the minimum sections every CDD for this venture must have. 
The AI outline step then adds assessments, any extra sections, the final order and the headings.
"""

from dataclasses import dataclass

from ai.templates.template_label_conditions import LabelCondition, get_conditions
from ai.templates.template_section_rules import EXCLUSIVE_PAIRS, SECTION_RULES
from ai.templates.template_sections import TemplateSection
from ai.templates.template_selection import TemplateSelection


@dataclass(frozen=True)
class CDDTemplate:
    """The guaranteed floor for one venture, before the AI plans the outline."""

    conditions: frozenset[LabelCondition]  # passed to the outline step as context
    sections: tuple[TemplateSection, ...]   # catalogue order; the AI sets the final order


def build_template(selection: TemplateSelection) -> CDDTemplate:
    """Return the conditions and guaranteed sections for the confirmed labels."""
    conditions = get_conditions(selection)

    # Keep every section whose rule is satisfied. A section without a rule
    # raises KeyError, so a new section can't be forgotten silently.
    sections = tuple(
        section for section in TemplateSection
        if SECTION_RULES[section].is_included(conditions)
    )

    _check_exclusive_pairs(sections)
    return CDDTemplate(conditions=frozenset(conditions), sections=sections)


def _check_exclusive_pairs(sections: tuple[TemplateSection, ...]) -> None:
    """Exactly one section of each exclusive pair must be present."""
    for first, second in EXCLUSIVE_PAIRS:
        if (first in sections) == (second in sections):
            raise ValueError(
                f"Expected exactly one of {first.value} and {second.value}."
            )
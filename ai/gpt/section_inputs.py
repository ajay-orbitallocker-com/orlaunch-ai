"""
Section inputs: what each outline section needs before it is generated.

- The name its prompt uses (base template name for the 15 base sections, else the heading).
- The output schema (existing schema for the 15 base sections, else GenericSection).
- The section brief (heading, purpose, assessments) added to the idea text.
- The retrieval queries (its assessments, or its purpose if it has none).
"""

from pydantic import BaseModel

from ai.schemas.outline_schema import OutlineSection
from ai.schemas.cdd_schema import SECTION_SCHEMAS , GroundedSection , InferenceSection
from ai.templates.template_sections import TemplateSection as S
from ai.templates.template_section_details import Grounding

# Section names from the base template (the original 15-section CDD).
# Existing prompts and schemas are keyed by these names.
BASE_TEMPLATE_SECTION_NAMES: dict[S, str] = {
    S.EXECUTIVE_SUMMARY: "1. Executive Summary",
    S.PROBLEM_ANALYSIS: "2. Problem Analysis",
    S.MARKET_NEED: "3. Market Need Assessment",
    S.INDUSTRY_ANALYSIS: "4. Industry Analysis",
    S.COMPETITIVE_ASSESSMENT: "5. Competitive Assessment",
    S.TECHNICAL_FEASIBILITY: "6. Technical Feasibility Assessment",
    S.SYSTEM_ARCHITECTURE: "7. Spacecraft Architecture",
    S.MISSION_ARCHITECTURE: "8. Mission Architecture",
    S.RISK: "9. Risk Assessment",
    S.DEVELOPMENT_ROADMAP: "10. Development Roadmap",
    S.MANUFACTURING_STRATEGY: "11. Manufacturing Strategy",
    S.COMMERCIALIZATION: "12. Commercialization Strategy",
    S.TEAM_STRUCTURE: "13. Team Structure",
    S.CAPITAL_REQUIREMENTS: "14. Capital Requirements",
    S.INVESTOR_READINESS: "15. Investor Readiness Score",
}


def base_template_name(section: OutlineSection) -> str | None:
    """The section's base template name, or None if it isn't one of the 15 base sections."""
    return None if section.is_extra else BASE_TEMPLATE_SECTION_NAMES.get(section.section)


def prompt_name(section: OutlineSection) -> str:
    """Base template name for the 15 base sections, otherwise the heading."""
    return base_template_name(section) or section.heading

def output_schema(section: OutlineSection) -> type[BaseModel]:
    """The section's own schema if it has one, otherwise the grounded or inference schema."""
    if not section.is_extra and section.section in SECTION_SCHEMAS:
        return SECTION_SCHEMAS[section.section]
    return GroundedSection if section.details().grounding == Grounding.GROUNDED else InferenceSection

def section_brief(idea_text: str, section: OutlineSection) -> str:
    """Idea text plus the section's heading, purpose and assessments."""
    questions = "\n".join(f"- {a}" for a in section.assessments) or "- (no specific questions)"
    return (
        f"{idea_text}\n\n<section_brief>\n"
        f"Heading: {section.heading}\n"
        f"Purpose: {section.details().purpose}\n"
        f"Answer these questions:\n{questions}\n"
        f"</section_brief>"
    )


def retrieval_queries(section: OutlineSection) -> list[str]:
    """The section's assessments, or its purpose if it has none."""
    return section.assessments or [section.details().purpose]
import re

from pydantic import BaseModel

from rag.hallucination.config import CDD_SECTIONS, CITATION_CHECK_PATTERNS, CITATION_MARKER_PATTERN, GROUNDED

# The GROUNDED sections this generation module can currently produce.
GROUNDED_SECTIONS_SUPPORTED = [
    "2. Problem Analysis",
    "3. Market Need Assessment",
    "4. Industry Analysis",
    "5. Competitive Assessment",
    "6. Technical Feasibility Assessment",
    "7. Spacecraft Architecture",
    "10. Development Roadmap",
    "14. Capital Requirements",
]


# Structured output schemas, one per CDD section.


class GroundedSection(BaseModel):
    text: str
    citations: list[int] = []


class InferenceSection(BaseModel):
    text: str


class Risk(BaseModel):
    category: str
    description: str


class Milestone(BaseModel):
    trl_start: int
    trl_target: int
    description: str


class FinancialBenchmark(BaseModel):
    company: str
    metric: str
    value: str
    fiscal_year: str


class ProblemAnalysisSection(GroundedSection):
    challenges: list[str] = []


class MarketNeedSection(GroundedSection):
    demand_signals: list[str] = []


class IndustryAnalysisSection(GroundedSection):
    trends: list[str] = []


class CompetitiveAssessmentSection(GroundedSection):
    competitors: list[FinancialBenchmark] = []


class CapitalRequirementsSection(GroundedSection):
    benchmarks: list[FinancialBenchmark] = []


class TechnicalFeasibilitySection(GroundedSection):
    trl_current: int
    trl_target: int
    precedents: list[str] = []


class SpacecraftArchitectureSection(GroundedSection):
    subsystems: list[str] = []


class MissionArchitectureSection(InferenceSection):
    mission_phases: list[str] = []


class RiskAssessmentSection(InferenceSection):
    risks: list[Risk] = []


class DevelopmentRoadmapSection(GroundedSection):
    milestones: list[Milestone] = []


class CommercializationStrategySection(InferenceSection):
    revenue_streams: list[str] = []


class TeamStructureSection(InferenceSection):
    roles: list[str] = []


class InvestorReadinessSection(InferenceSection):
    score: int
    key_gaps: list[str] = []


# Section name mapped to its schema class.
SECTION_SCHEMAS: dict[str, type[BaseModel]] = {
    "2. Problem Analysis": ProblemAnalysisSection,
    "3. Market Need Assessment": MarketNeedSection,
    "4. Industry Analysis": IndustryAnalysisSection,
    "5. Competitive Assessment": CompetitiveAssessmentSection,
    "6. Technical Feasibility Assessment": TechnicalFeasibilitySection,
    "7. Spacecraft Architecture": SpacecraftArchitectureSection,
    "8. Mission Architecture": MissionArchitectureSection,
    "9. Risk Assessment": RiskAssessmentSection,
    "10. Development Roadmap": DevelopmentRoadmapSection,
    "12. Commercialization Strategy": CommercializationStrategySection,
    "13. Team Structure": TeamStructureSection,
    "14. Capital Requirements": CapitalRequirementsSection,
    "15. Investor Readiness Score": InvestorReadinessSection,
}


def get_section_schema(section_name: str) -> type[BaseModel]:
    """Looks up the schema class for a CDD section.

    Args:
        section_name: The CDD section name.

    Returns:
        The section's schema class from SECTION_SCHEMAS if listed there,
        otherwise GroundedSection or InferenceSection depending on the
        section's mode in CDD_SECTIONS.
    """
    if section_name in SECTION_SCHEMAS:
        return SECTION_SCHEMAS[section_name]
    return GroundedSection if CDD_SECTIONS.get(section_name) == GROUNDED else InferenceSection


def validate_cdd(cdd: dict[str, BaseModel], sources: dict[int, dict] | None = None) -> list[str]:
    """Checks generated CDD sections for shape and citation issues.

    Args:
        cdd: Section name mapped to section model.
        sources: Doc number mapped to source metadata, or None.

    Returns:
        A list of warning strings, empty if no issues were found. Never
        raises. For GROUNDED sections, cross-checks the `citations` field
        against inline [Doc N] markers in `text`, and, when `sources` is
        given, flags any citation number not present in `sources`.
    """
    warnings = []
    for section_name, section in cdd.items():
        if section_name not in CDD_SECTIONS:
            warnings.append(f"'{section_name}' is not a recognized CDD section")
            continue
        text = section.text
        if not isinstance(text, str) or not text.strip():
            warnings.append(f"'{section_name}' has no text")
            continue
        if CDD_SECTIONS[section_name] == GROUNDED:
            needs_citation = any(p.search(text) for p in CITATION_CHECK_PATTERNS)
            has_citation = bool(CITATION_MARKER_PATTERN.search(text))
            if needs_citation and not has_citation:
                warnings.append(f"'{section_name}' has a checkable claim but no [Doc N] citation anywhere")

            declared = set(getattr(section, "citations", []))
            in_text = {int(m) for m in re.findall(r"\[Doc\s?(\d+)\]", text, re.IGNORECASE)}
            if in_text - declared:
                warnings.append(
                    f"'{section_name}' cites {sorted(in_text - declared)} inline but omits them from citations"
                )
            if declared - in_text:
                warnings.append(
                    f"'{section_name}' declares citations {sorted(declared - in_text)} not used inline in text"
                )
            if sources is not None:
                invalid = declared - set(sources.keys())
                if invalid:
                    warnings.append(
                        f"'{section_name}' cites {sorted(invalid)}, which are not in the retrieved sources"
                    )
    return warnings

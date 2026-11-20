"""
Template section rules: when each CDD section is included.
Each section either is always included, requires a label condition, or
excludes one. 
Opposites use excludes, so exactly one section of each pair is
included (Capital Requirements / Budget Assessment, Investor Readiness /
Venture Viability, market sections / Stakeholder Analysis).
"""

from dataclasses import dataclass

from ai.templates.template_label_conditions import LabelCondition
from ai.templates.template_sections import TemplateSection


@dataclass(frozen=True)
class SectionRule:
    """Conditions a section needs (requires) or must not have (excludes).
    A rule with neither means the section is always included."""

    requires: frozenset[LabelCondition] = frozenset()
    excludes: frozenset[LabelCondition] = frozenset()

    def is_included(self, conditions: set[LabelCondition]) -> bool:
        return self.requires <= conditions and not (self.excludes & conditions)


ALWAYS = SectionRule()


def requires(*conditions: LabelCondition) -> SectionRule:
    return SectionRule(requires=frozenset(conditions))


def excludes(*conditions: LabelCondition) -> SectionRule:
    return SectionRule(excludes=frozenset(conditions))


SECTION_RULES: dict[TemplateSection, SectionRule] = {
    
    # Always included
    TemplateSection.EXECUTIVE_SUMMARY: ALWAYS,
    TemplateSection.TECHNICAL_FEASIBILITY: ALWAYS,
    TemplateSection.RISK: ALWAYS,
    TemplateSection.DEVELOPMENT_ROADMAP: ALWAYS,
    TemplateSection.TEAM_STRUCTURE: ALWAYS,

    # Commercial ventures, or the opposite
    TemplateSection.PROBLEM_ANALYSIS: requires(LabelCondition.COMMERCIAL),
    TemplateSection.MARKET_NEED: requires(LabelCondition.COMMERCIAL),
    TemplateSection.INDUSTRY_ANALYSIS: requires(LabelCondition.COMMERCIAL),
    TemplateSection.COMPETITIVE_ASSESSMENT: requires(LabelCondition.COMMERCIAL),
    TemplateSection.COMMERCIALIZATION: requires(LabelCondition.COMMERCIAL),
    TemplateSection.STAKEHOLDER_ANALYSIS: excludes(LabelCondition.COMMERCIAL),

    # What is being built and where
    TemplateSection.SCIENTIFIC_VALUE: requires(LabelCondition.SCIENCE),
    TemplateSection.SYSTEM_ARCHITECTURE: requires(LabelCondition.HARDWARE),
    TemplateSection.MISSION_ARCHITECTURE: requires(LabelCondition.HARDWARE),
    TemplateSection.MANUFACTURING_STRATEGY: requires(LabelCondition.PRODUCIBLE),
    TemplateSection.ORBITAL_MECHANICS: requires(LabelCondition.TRAJECTORY_CRITICAL),
    TemplateSection.TARGET_BODY_OPPORTUNITY: requires(LabelCondition.TARGET_BODIES),

    # Cost: exactly one
    TemplateSection.BUDGET_ASSESSMENT: requires(LabelCondition.PRIMARILY_GRANT_FUNDED),
    TemplateSection.CAPITAL_REQUIREMENTS: excludes(LabelCondition.PRIMARILY_GRANT_FUNDED),
    TemplateSection.FUNDING_STRATEGY: requires(LabelCondition.GRANTS_OR_MIXED_FUNDING),

    # Closing score: exactly one
    TemplateSection.INVESTOR_READINESS: requires(LabelCondition.INVESTOR_AUDIENCE),
    TemplateSection.VENTURE_VIABILITY: excludes(LabelCondition.INVESTOR_AUDIENCE),

    
}

# Sections that must never appear together.
EXCLUSIVE_PAIRS: tuple[tuple[TemplateSection, TemplateSection], ...] = (
    (TemplateSection.CAPITAL_REQUIREMENTS, TemplateSection.BUDGET_ASSESSMENT),
    (TemplateSection.INVESTOR_READINESS, TemplateSection.VENTURE_VIABILITY),
)
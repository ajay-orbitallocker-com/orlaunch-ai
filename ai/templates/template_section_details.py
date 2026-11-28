"""
Template section details: what each CDD section is for and how it is checked.

For every section: a fallback heading, its purpose (the question it answers),
whether it is GROUNDED or INFERENCE, and whether it is written from the other
sections instead of from retrieval.

GROUNDED: answers must trace to retrieved documents.
INFERENCE: reasoned from the idea; factual claims inside still need citations.
"""

from dataclasses import dataclass
from enum import Enum

from ai.templates.template_sections import TemplateSection as S


class Grounding(str, Enum):
    GROUNDED = "grounded"
    INFERENCE = "inference"


@dataclass(frozen=True)
class SectionDetails:
    heading: str                 # fallback when the AI heading is invalid
    purpose: str                 # the question this section answers
    grounding: Grounding
    from_sections: bool = False  # True: summarises other sections, no retrieval, written last


G, I = Grounding.GROUNDED, Grounding.INFERENCE


SECTION_DETAILS: dict[S, SectionDetails] = {
    S.EXECUTIVE_SUMMARY: SectionDetails(
        "Executive Summary", "What is the venture and why does it matter?", I, from_sections=True),
    S.PROBLEM_ANALYSIS: SectionDetails(
        "Problem Analysis", "What industry problem does it solve?", G),
    S.MARKET_NEED: SectionDetails(
        "Market Need Assessment", "What evidence shows demand exists?", G),
    S.INDUSTRY_ANALYSIS: SectionDetails(
        "Industry Analysis", "What does the current industry landscape look like?", G),
    S.COMPETITIVE_ASSESSMENT: SectionDetails(
        "Competitive Assessment", "Which companies and technologies compete?", G),
    S.SCIENTIFIC_VALUE: SectionDetails(
        "Scientific Value Assessment", "Why does the mission matter scientifically?", G),
    S.TECHNICAL_FEASIBILITY: SectionDetails(
        "Technical Feasibility Assessment",
        "Can it be built, and which technologies exist versus are still needed?", G),
    S.ORBITAL_MECHANICS: SectionDetails(
        "Orbital Mechanics Assessment", "Is the trajectory physically feasible?", G),
    S.TARGET_BODY_OPPORTUNITY: SectionDetails(
        "Target Body Opportunity Analysis", "Which targets and trajectories are possible?", G),
    S.SYSTEM_ARCHITECTURE: SectionDetails(
        "System Architecture", "What are the main subsystems and how do they fit together?", G),
    S.MISSION_ARCHITECTURE: SectionDetails(
        "Mission Architecture", "What happens from launch to end of mission?", I),
    S.RISK: SectionDetails(
        "Risk Assessment", "What could stop it succeeding, and how likely and severe is it?", I),
    S.DEVELOPMENT_ROADMAP: SectionDetails(
        "Development Roadmap", "How does it mature from concept to operation?", G),
    S.MANUFACTURING_STRATEGY: SectionDetails(
        "Manufacturing Strategy", "How will it be produced and supplied?", I),
    S.COMMERCIALIZATION: SectionDetails(
        "Commercialization Strategy", "How will it generate revenue?", I),
    S.STAKEHOLDER_ANALYSIS: SectionDetails(
        "Stakeholder Analysis", "Who are the likely sponsors, partners and users?", G),
    S.TEAM_STRUCTURE: SectionDetails(
        "Team Structure", "Which disciplines and roles are required?", I),
    S.CAPITAL_REQUIREMENTS: SectionDetails(
        "Capital Requirements", "How much funding is needed, and for which phases?", G),
    S.BUDGET_ASSESSMENT: SectionDetails(
        "Budget Assessment", "What are the estimated costs by phase?", G),
    S.FUNDING_STRATEGY: SectionDetails(
        "Funding Strategy", "Which grants, programs and partners could fund it?", I),
    S.INVESTOR_READINESS: SectionDetails(
        "Investor Readiness Score", "How ready is it for investment, and why?", I,
        from_sections=True),
    S.VENTURE_VIABILITY: SectionDetails(
        "Venture Viability Assessment",
        "How feasible is it overall, as a mission and business?", I, from_sections=True),
}
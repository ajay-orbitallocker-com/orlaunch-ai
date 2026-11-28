"""
Template sections: one generic, stable name per CDD section.

Names stay neutral (no numbers, "Spacecraft" or "Comet") so one section can have
a different title and position in each base template. Generation, checks and
PDF export key on the name, never the title. Imports nothing from the project.

"""

from enum import Enum


class TemplateSection(str, Enum):
    """Generic name for a CDD section. Titles and order come from the base templates."""
    
    # Always included
    EXECUTIVE_SUMMARY = "executive_summary"
    TECHNICAL_FEASIBILITY = "technical_feasibility"  # also "Technology Readiness Assessment"
    RISK = "risk"
    DEVELOPMENT_ROADMAP = "development_roadmap"
    TEAM_STRUCTURE = "team_structure"

    # Commercial ventures
    PROBLEM_ANALYSIS = "problem_analysis"
    MARKET_NEED = "market_need"
    INDUSTRY_ANALYSIS = "industry_analysis"
    COMPETITIVE_ASSESSMENT = "competitive_assessment"
    COMMERCIALIZATION = "commercialization"

    # Not commercial
    STAKEHOLDER_ANALYSIS = "stakeholder_analysis"

    # Science is a goal
    SCIENTIFIC_VALUE = "scientific_value"

    # Builds hardware
    SYSTEM_ARCHITECTURE = "system_architecture"
    MISSION_ARCHITECTURE = "mission_architecture"

    # Needs a manufacturing plan
    MANUFACTURING_STRATEGY = "manufacturing_strategy"

    # Trajectory is a hard problem
    ORBITAL_MECHANICS = "orbital_mechanics"

    # Visits comets or asteroids
    TARGET_BODY_OPPORTUNITY = "target_body_opportunity"

    # Cost: exactly one of these
    CAPITAL_REQUIREMENTS = "capital_requirements"
    BUDGET_ASSESSMENT = "budget_assessment"

    # Grants or mixed funding
    FUNDING_STRATEGY = "funding_strategy"

    # Closing score: exactly one of these
    INVESTOR_READINESS = "investor_readiness"
    VENTURE_VIABILITY = "venture_viability"
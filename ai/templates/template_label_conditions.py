"""
Label conditions: yes/no facts worked out from the template labels.
"""

from enum import Enum

from ai.templates.template_labels import Audience, Domain, FundingPath, OfferingType, Segment
from ai.templates.template_selection import TemplateSelection


class LabelCondition(str, Enum):
    COMMERCIAL = "commercial"                    # not research-only, or commercial funding
    HARDWARE = "hardware"                        # builds and flies hardware
    SCIENCE = "science"                          # main goal is scientific return
    PRODUCIBLE = "producible"                    # needs a manufacturing plan
    TRAJECTORY_CRITICAL = "trajectory_critical"  # reaching the target is hard physics
    TARGET_BODIES = "target_bodies"              # visits comets or asteroids
    PRIMARILY_GRANT_FUNDED = "primarily_grant_funded"    # primary funding path is grants
    GRANTS_OR_MIXED_FUNDING = "grants_or_mixed_funding"  # grants anywhere, or several sources
    INVESTOR_AUDIENCE = "investor_audience"      # written for investors


# --- Label groups used by the questions below --------------------------------

COMMERCIAL_FUNDING = {FundingPath.VENTURE_CAPITAL, FundingPath.CONTRACTS, FundingPath.CORPORATE}

PRODUCIBLE_OFFERINGS = {OfferingType.PHYSICAL_PRODUCT, OfferingType.SERVICE}

NON_HARDWARE_SEGMENTS = {Segment.GROUND_SEGMENT, Segment.DOWNSTREAM_DATA}

TRAJECTORY_CRITICAL_DOMAINS = {Domain.CISLUNAR, Domain.SMALL_BODIES, Domain.DEEP_SPACE}


def get_conditions(selection: TemplateSelection) -> set[LabelCondition]:
    """Answer each question once and return the conditions that are true."""
    s = selection
    answers = {

        # Is it commercial? Anything but a research mission, or commercial main funding.
        LabelCondition.COMMERCIAL: s.offering_type != OfferingType.RESEARCH_MISSION or s.funding.primary in COMMERCIAL_FUNDING,
                
        # Does it build hardware? Any segment that is not purely ground or data.
        LabelCondition.HARDWARE: bool(s.segment.values - NON_HARDWARE_SEGMENTS),
        
        # Is science the goal?
        LabelCondition.SCIENCE: Segment.SCIENCE_EXPLORATION in s.segment.values,
        
        # Does it need a manufacturing plan?
        LabelCondition.PRODUCIBLE: s.offering_type in PRODUCIBLE_OFFERINGS,
        
        # Is the trajectory a hard problem? Any matching domain counts.
        LabelCondition.TRAJECTORY_CRITICAL: bool(s.domain.values & TRAJECTORY_CRITICAL_DOMAINS),
        
        # Does it visit comets or asteroids?
        LabelCondition.TARGET_BODIES: Domain.SMALL_BODIES in s.domain.values,
        
        # Is it mainly grant funded? Only the primary funding path counts.
        LabelCondition.PRIMARILY_GRANT_FUNDED: s.funding.primary == FundingPath.GRANTS_AGENCY,
        
        # Does the funding need explaining? Grants, or more than one source.
        LabelCondition.GRANTS_OR_MIXED_FUNDING: FundingPath.GRANTS_AGENCY in s.funding.values or s.funding.is_mixed,
        
        # Is it written for investors?
        LabelCondition.INVESTOR_AUDIENCE: s.audience == Audience.INVESTORS,
    }
    return {condition for condition, is_true in answers.items() if is_true}
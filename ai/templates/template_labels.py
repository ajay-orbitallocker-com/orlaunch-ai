from enum import Enum

class Domain(str , Enum):
    """Where the venture primarily operates (operating regime)."""

    TERRESTRIAL = "terrestrial"
    SUBORBITAL  = "suborbital"
    EARTH_ORBIT = "earth_orbit"
    CISLUNAR = "cislunar"
    LUNAR_SURFACE = "lunar_surface"
    SMALL_BODIES = "small_bodies"
    DEEP_SPACE = "deep_space"
    OTHER = "other"
    UNKNOWN = "unknown"

class Segment(str , Enum):
    """What part of the space industry the venture is in """

    LAUNCH_SERVICES = "launch_services"
    SPACECRAFT_HARDWARE = "spacecraft_hardware"
    IN_SPACE_SERVICES = "in_space_services"
    IN_SPACE_INFRASTRUCTURE = "in_space_infrastructure"
    IN_SPACE_RESOURCES = "in_space_resources"
    SCIENCE_EXPLORATION = "science_exploration"
    HUMAN_SPACEFLIGHT = "human_spaceflight"
    GROUND_SEGMENT = "ground_segment"
    DOWNSTREAM_DATA = "downstream_data"
    OTHER = "other"
    UNKNOWN = "unknown"

class FundingPath(str , Enum):
    """Who pays to build it. Multi-value: several values = mixed funding."""
    VENTURE_CAPITAL = "venture_capital"
    GRANTS_AGENCY = "grants_agency"
    CONTRACTS = "contracts"
    CORPORATE = "corporate"
    SELF_FUNDED = "self_funded"
    UNKNOWN = "unknown"

class OfferingType(str , Enum):
    """The form of what is delivered"""

    PHYSICAL_PRODUCT = "physical_product"
    SERVICE = "service"
    PLATFORM = "platform"
    SOFTWARE = "software"
    DATA_PRODUCT = "data_product"
    RESEARCH_MISSION = "research_mission"
    OTHER = "other"
    UNKNOWN = "unknown"


class Audience(str,Enum):
    """Who the CDD is written for. Decides the scoring rubric and tone."""
    INVESTORS = "investors"
    FUNDING_AGENCY = "funding_agency"
    INTERNAL_PLANNING = "internal_planning"
    PARTNERS = "partners"
    UNKNOWN = "unknown"


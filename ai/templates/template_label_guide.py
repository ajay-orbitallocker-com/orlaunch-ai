"""
Template label guide: what each label means, for the AI that picks the labels.

One definition per enum member, plus one rule per label type for the cases the
AI tends to get wrong. 
"""

from enum import Enum

from ai.templates.template_labels import Audience, Domain, FundingPath, OfferingType, Segment

LABEL_RULES: dict[type[Enum], str] = {
    Segment: "Judge by what the venture is FOR, not how it gets there.",
    Domain: "List every place it operates. Primary is the main one.",
    OfferingType: "Judge by what value is delivered and to whom. Ignore what is built: "
                  "most ventures build a spacecraft.",
    FundingPath: "Infer from the concept and the founder's open questions, not from lists of "
                 "documents they ask for. Several values means mixed funding.",
    Audience: "If not stated, follow the primary funding path: venture capital -> investors, "
              "grants -> funding_agency.",
}

LABEL_GUIDE: dict[Enum, str] = {
    # Domain: where it operates
    Domain.TERRESTRIAL: "On the ground: ground stations, data processing, test facilities.",
    Domain.SUBORBITAL: "Flights that reach space without going into orbit.",
    Domain.EARTH_ORBIT: "Any Earth orbit (LEO, MEO, GEO, HEO).",
    Domain.CISLUNAR: "Between Earth and the Moon, including lunar orbit.",
    Domain.LUNAR_SURFACE: "On the Moon's surface.",
    Domain.SMALL_BODIES: "Asteroids, comets and other small bodies.",
    Domain.DEEP_SPACE: "Interplanetary transit or the outer Solar System.",
    Domain.OTHER: "Clear, but none of the above.",
    Domain.UNKNOWN: "The idea does not say where it operates.",

    # Segment: what part of the space industry
    Segment.LAUNCH_SERVICES: "Getting payloads to space: launch vehicles, rideshare, upper stages.",
    Segment.SPACECRAFT_HARDWARE: "Building spacecraft, buses or components for others.",
    Segment.IN_SPACE_SERVICES: "Services to other space assets: servicing, refuelling, inspection, "
                               "debris removal, logistics.",
    Segment.IN_SPACE_INFRASTRUCTURE: "Long-lived infrastructure in space: stations, depots, power, relays.",
    Segment.IN_SPACE_RESOURCES: "Extracting or making things in space: mining, manufacturing.",
    Segment.SCIENCE_EXPLORATION: "Main goal is scientific return or exploration.",
    Segment.HUMAN_SPACEFLIGHT: "Carrying or supporting humans: habitats, tourism, crew systems.",
    Segment.GROUND_SEGMENT: "Ground stations, mission operations, tracking services.",
    Segment.DOWNSTREAM_DATA: "Applications built on space data: Earth observation analytics, "
                             "satcom applications, positioning.",
    Segment.OTHER: "Clear, but none of the above.",
    Segment.UNKNOWN: "The idea does not make the segment clear.",

    # Offering type: what value is delivered
    OfferingType.PHYSICAL_PRODUCT: "Sells hardware the customer owns or operates.",
    OfferingType.SERVICE: "Sells an operation performed for paying customers.",
    OfferingType.PLATFORM: "Shared capability used by many customers.",
    OfferingType.SOFTWARE: "Sells software or autonomy capability.",
    OfferingType.DATA_PRODUCT: "Sells data or analytics.",
    OfferingType.RESEARCH_MISSION: "Delivers scientific knowledge; no paying customer.",
    OfferingType.OTHER: "Clear, but none of the above.",
    OfferingType.UNKNOWN: "The idea does not make the offering clear.",

    # Funding path: who pays to build it
    FundingPath.VENTURE_CAPITAL: "Private investors expecting a commercial return.",
    FundingPath.GRANTS_AGENCY: "Government agencies, science programmes, research grants.",
    FundingPath.CONTRACTS: "Paid development or service contracts.",
    FundingPath.CORPORATE: "An existing company's own budget or venture arm.",
    FundingPath.SELF_FUNDED: "The founders' own money or revenue.",
    FundingPath.UNKNOWN: "The idea does not say who funds development.",

    # Audience: who reads the CDD
    Audience.INVESTORS: "Written to support fundraising.",
    Audience.FUNDING_AGENCY: "Written for an agency or grant review panel.",
    Audience.INTERNAL_PLANNING: "Written for the founding team's own planning.",
    Audience.PARTNERS: "Written for prospective industrial or research partners.",
    Audience.UNKNOWN: "The idea does not say who will read it.",
}
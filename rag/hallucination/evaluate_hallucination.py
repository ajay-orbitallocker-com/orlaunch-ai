import json
from pathlib import Path

from rag.hallucination.report import build_report
from rag.retrieval.search import build_context_package

MOCK_CDD_PATH = Path(__file__).resolve().parent / "fixtures" / "mock_cdd_satellite_repair.json"

# The reference idea text used to evaluate hallucination checking against the mock CDD.
REFERENCE_IDEA_TEXT = """Project Name

Orbital Satellite Repair Droid

Concept Description

I want to create a robotic spacecraft that can be launched into orbit and perform repairs on satellites that have become damaged, malfunctioning, or partially inoperable.

The spacecraft should be capable of operating semi-autonomously while still allowing oversight from ground control when required.

After launch, the vehicle should be able to determine its position in orbit, identify a target satellite, calculate an intercept trajectory, and safely rendezvous with the satellite.

Once it reaches the target, the spacecraft should be capable of inspecting the satellite to identify faults or damage. It should then physically attach itself to the satellite and perform repairs.

The repair system could include robotic arms, grappling mechanisms, tool attachments, replacement components, electrical interfaces, or other technologies needed to restore functionality.

The spacecraft should be capable of carrying replacement parts and should ideally be adaptable to work on different satellite types and manufacturers.

After completing a repair mission, the spacecraft should either:

Move to another customer satellite
Return to a servicing depot
Refuel in orbit
Re-enter the atmosphere safely
Move to a designated disposal orbit
The goal is to reduce satellite losses, extend mission lifetimes, and create a new commercial servicing industry in space.

The spacecraft should be designed around modular principles so components can be upgraded or replaced as technology evolves.

I would also like the system to be designed for large-scale production so that fleets of servicing vehicles can eventually be deployed.

Potential capabilities may include:

Satellite inspection
Fault diagnosis
Component replacement
Refueling
Battery replacement
Solar array servicing
Antenna repair
Sensor replacement
Orbital relocation assistance
Debris mitigation support
I am unsure of:

Which repair operations are realistically possible in orbit
Which satellite types would be compatible
How docking and attachment would work
What regulations would apply
What propulsion systems should be used
How the business model would operate
Whether servicing depots would be needed
How autonomous the spacecraft could legally be
What level of AI would be practical
Which customers would be most likely to buy the service
I would like the concept developed into a complete space venture including:

Technical feasibility analysis
Market opportunity assessment
Spacecraft architecture
Mission architecture
Regulatory assessment
Development roadmap
Manufacturing strategy
Team structure
Financial projections
Funding strategy
Business plan
Investor pitch deck"""


def load_reference_idea() -> str:
    """Returns the reference idea text.

    Returns:
        The REFERENCE_IDEA_TEXT string.
    """
    return REFERENCE_IDEA_TEXT


def load_mock_cdd() -> dict:
    """Loads the mock CDD fixture.

    Returns:
        The fixture's sections as a dict, with "_comment"-style keys
        dropped.
    """
    raw = json.loads(MOCK_CDD_PATH.read_text(encoding="utf-8"))
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def run_hallucination_evaluation(top_k: int = 5) -> dict:
    """Runs the hallucination check against the mock CDD.

    Args:
        top_k: Number of documents to retrieve for context.

    Returns:
        The hallucination report dict from build_report().
    """
    idea_text = load_reference_idea()
    print(f"Retrieving context for reference idea (Orbital Satellite Repair Droid, {len(idea_text)} chars)...")

    context_package = build_context_package(idea_text, top_k=top_k)
    retrieved_documents = context_package["retrieved_documents"]
    print(f"Retrieved {len(retrieved_documents)} documents to check the mock CDD against.\n")

    mock_cdd = load_mock_cdd()
    return build_report(mock_cdd, retrieved_documents)


if __name__ == "__main__":
    print("=== Running Hallucination Check Evaluation ===")
    try:
        result = run_hallucination_evaluation()
        print(json.dumps(result, indent=2))
        print(f"\nOverall hallucination rate: {result['overall_hallucination_rate'] * 100:.1f}%")
        print(f"Total citation flags: {result['total_citation_flags']}")
    except Exception as e:
        print(f"Hallucination evaluation error: {e}")

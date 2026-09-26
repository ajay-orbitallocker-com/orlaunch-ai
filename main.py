"""
Starter entry point: take the sample unstructured venture idea and run it
against the stored RAG data, comparing broad (unfiltered) retrieval to
category-filtered (metadata-scoped) retrieval, to see what's actually
grounded per category.

Requires a populated ChromaDB collection (run
rag.ingestion.ingest_all.run_ingestion_pipeline_all() first) and a working
OPENAI_API_KEY (see chroma_config.py).
"""

from rag.retrieval.search import retrieve_top_k_documents, build_context_package

# Hardcoded user input
SAMPLE_IDEA_TEXT = """
Project Name

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

CATEGORIES = [
    "Technical & TRL",
    "Financial Intelligence",
    "Patents & IP",
    "Market Intelligence",
]


def run_semantic_comparison(query_text: str, top_k: int = 5) -> None:
    print("=== Query (user idea text, first 300 chars) ===")
    print(query_text[:300] + ("..." if len(query_text) > 300 else ""))
    print()

    print("=== Cross-category retrieval (no metadata filter) ===")
    package = build_context_package(query_text, top_k=top_k)
    print(f"Retrieved {package['total_documents_retrieved']} documents across all categories.\n")
    print(package["formatted_context_str"])

    print("=== Per-category retrieval (metadata-filtered) ===")
    for category in CATEGORIES:
        docs = retrieve_top_k_documents(query_text, top_k=top_k, category_filter=category)
        print(f"\n--- {category}: {len(docs)} matches ---")
        for doc in docs:
            print(f"  [{doc['similarity_score']}] {doc['title']}")


if __name__ == "__main__":
    run_semantic_comparison(SAMPLE_IDEA_TEXT, top_k=5)

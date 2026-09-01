import re

JUDGE_MODEL = "gpt-4o-mini"

GROUNDED = "GROUNDED"    # must trace back to a retrieved document
INFERENCE = "INFERENCE"  # inferred, with no retrievable ground truth

# The 15 CDD sections, tagged as GROUNDED or INFERENCE.
CDD_SECTIONS = {
    "1. Executive Summary": INFERENCE,
    "2. Problem Analysis": GROUNDED,
    "3. Market Need Assessment": GROUNDED,
    "4. Industry Analysis": GROUNDED,
    "5. Competitive Assessment": GROUNDED,
    "6. Technical Feasibility Assessment": GROUNDED,
    "7. Spacecraft Architecture": GROUNDED,
    "8. Mission Architecture": INFERENCE,
    "9. Risk Assessment": INFERENCE,
    "10. Development Roadmap": GROUNDED,
    "11. Manufacturing Strategy": INFERENCE,
    "12. Commercialization Strategy": INFERENCE,
    "13. Team Structure": INFERENCE,
    "14. Capital Requirements": GROUNDED,
    "15. Investor Readiness Score": INFERENCE,
}

# Patterns matching specific, checkable claims that require a citation.
CITATION_CHECK_PATTERNS = [
    re.compile(r"\$\s?\d[\d,.]*\s?(?:billion|million|bn|m|k)?", re.IGNORECASE),  # dollar figures
    re.compile(r"\bTRL\s?\d\b", re.IGNORECASE),                                  # TRL levels
    re.compile(r"\b\d{1,3}(?:\.\d+)?\s?%"),                                      # percentages
    re.compile(r"\b(19|20)\d{2}\b"),                                             # years
]

CITATION_MARKER_PATTERN = re.compile(r"\[Doc\s?\d+\]", re.IGNORECASE)

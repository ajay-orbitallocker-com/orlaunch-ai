"""
Outline schema: the CDD outline the AI plans for one venture.

The LLM fills this in during the outline step , which assessments the venture
needs, which section each one goes to, any extra sections, the order and the
headings. 
Rules about the whole outline (every guaranteed section present,
anchors, caps) are checked separately in ai/templates/check_cdd_outline.py.

"""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ai.templates.template_section_details import SECTION_DETAILS, Grounding, SectionDetails
from ai.templates.template_sections import TemplateSection

EXTRA_PREFIX = "extra_"


class OutlineSection(BaseModel):
    """One section of the planned outline: a catalogue section or an AI-created extra section."""

    model_config = ConfigDict(frozen=True)

    key: str                         # catalogue value (e.g. "market_need") or "extra_<name>"
    is_extra: bool
    heading: str
    assessments: list[str] = Field(default_factory=list)  # venture-specific questions

    # Only for extra sections. Catalogue sections take these from SECTION_DETAILS.
    purpose: str | None = None
    grounding: Grounding | None = None
    grounding_reason: str | None = None
    reason: str | None = None        # which capability of the venture needs this section

    @model_validator(mode="after")
    def check_key(self) -> "OutlineSection":
        if self.is_extra:
            if not self.key.startswith(EXTRA_PREFIX):
                raise ValueError(f"Extra section keys must start with '{EXTRA_PREFIX}'.")
            if not self.purpose:
                raise ValueError("Extra sections must state their purpose.")
        else:
            TemplateSection(self.key)  # raises ValueError if not a catalogue section
        return self

    @property
    def section(self) -> TemplateSection | None:
        """The catalogue section, or None for an extra section."""
        return None if self.is_extra else TemplateSection(self.key)

    def details(self) -> SectionDetails:
        """One lookup for both kinds. Extras with no grounding default to GROUNDED."""
        if self.is_extra:
            return SectionDetails(
                heading=self.heading,
                purpose=self.purpose,
                grounding=self.grounding or Grounding.GROUNDED,
            )
        return SECTION_DETAILS[self.section]


class CDDOutline(BaseModel):
    """The full outline, in final order."""

    model_config = ConfigDict(frozen=True)

    capabilities: list[str]          # what the venture must be able to do
    sections: list[OutlineSection]   # final order, first to last
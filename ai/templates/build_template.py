from pydantic import BaseModel , ConfigDict , model_validator
from ai.templates.template_labels import Domain , Segment , OfferingType , FundingPath , Audience

class Selection(BaseModel):
    
    model_config = ConfigDict(frozen=True)

    @property
    def values(self) -> frozenset[Domain]:
        """
        Primary and secondary together, for matching sections.
        """
        return frozenset({self.primary , *self.secondary})
    @property
    def is_mixed(self) -> bool:
        """True when more than one value is selected."""
        return len(self.values) > 1   
    
    @model_validator(mode = "after")
    def check_values(self):
        """Runs automatically after the object is created and rejects bad input."""

        # the primary domain should not also be listed as secondary.
        if self.primary in self.secondary or len(self.secondary) != len(set(self.secondary)):
            raise ValueError("Each value may appear only once across primary and secondary.")

        # Unknown domain
        if Domain.UNKNOWN in self.values and len(self.values) > 1:
            raise ValueError("UNKNOWN cannot be combined with other domains.")

        return self

class SegmentSelection(Selection):
    """What the venture is for. Satellite: IN_SPACE_SERVICES."""

    primary : Segment
    secondary : tuple[Segment , ...] = ()

class DomainSelection(Selection):
    """Where the venture operates. Comet: DEEP_SPACE + (SMALL_BODIES,)."""
    
     # The main place the venture operates.
    primary : Domain
    secondary : tuple[Domain , ...] = ()

class FundingSelection(Selection):
    """Who pays to build it. Comet: GRANTS_AGENCY + (VENTURE_CAPITAL,)."""
    
    primary: FundingPath
    secondary: tuple[FundingPath, ...] = ()

class TemplateSelection(BaseModel):
    """The confirmed labels that decide which CDD template is built."""

    model_config = ConfigDict(frozen=True)

    segment: SegmentSelection       
    domain: DomainSelection         
    offering_type: OfferingType     
    funding: FundingSelection       
    audience: Audience              
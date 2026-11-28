"""
Template selection schema: what the AI returns when it reads a founder's idea.

The labels (TemplateSelection), a short project name, and how confident the AI
is about each label. Low or medium confidence is what the chatbot asks the
founder to confirm.

Privacy: project_name comes from the founder's idea, so keep this in the session.
TemplateSelection on its own holds labels only.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict

from ai.templates.template_selection import TemplateSelection


class Confidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LabelConfidence(BaseModel):
    """How sure the AI is about each label."""

    model_config = ConfigDict(frozen=True)

    segment: Confidence
    domain: Confidence
    offering_type: Confidence
    funding: Confidence
    audience: Confidence


class TemplateSelectionResult(BaseModel):
    """The AI's reading of the idea: labels, project name and confidence."""

    model_config = ConfigDict(frozen=True)

    project_name: str
    selection: TemplateSelection
    confidence: LabelConfidence

    def needs_confirmation(self) -> list[str]:
        """Labels the founder should confirm: anything not high confidence."""
        return [name for name, level in self.confidence if level != Confidence.HIGH]
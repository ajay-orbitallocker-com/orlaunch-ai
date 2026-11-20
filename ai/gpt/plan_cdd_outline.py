"""
Plan CDD outline: ask the AI to plan the outline, then check it.

If the outline breaks a rule that can't be fixed automatically, the AI is asked
again with the reason. The client is passed in so tests can use a fake one.
"""

from openai import OpenAI

from ai.gpt.config import OUTLINE_MAX_ATTEMPTS, OUTLINE_MODEL
from ai.prompts.outline_prompts import build_outline_messages
from ai.schemas.outline_schema import CDDOutline
from ai.templates.build_template import CDDTemplate
from ai.templates.check_cdd_outline import OutlineError, check_cdd_outline
from ai.templates.template_section_rules import EXCLUSIVE_PAIRS
from ai.templates.template_sections import TemplateSection


def plan_cdd_outline(idea: str, template: CDDTemplate, client: OpenAI) -> tuple[CDDOutline, list[str]]:
    """Return the checked outline and the notes of any automatic fixes."""
    optional = _optional_sections(template)
    feedback = None

    for _ in range(OUTLINE_MAX_ATTEMPTS):
        response = client.chat.completions.parse(
            model=OUTLINE_MODEL,
            messages=build_outline_messages(idea, template, optional, feedback),
            response_format=CDDOutline,
        )
        outline = response.choices[0].message.parsed
        if outline is None:
            raise OutlineError("The model returned no outline.")
        try:
            return check_cdd_outline(outline, template)
        except OutlineError as error:
            feedback = str(error)  # tell the AI what to fix on the next attempt

    raise OutlineError(f"No valid outline after {OUTLINE_MAX_ATTEMPTS} attempts: {feedback}")


def _optional_sections(template: CDDTemplate) -> list[TemplateSection]:
    """Catalogue sections the AI may add: not already required, not the excluded half of a pair."""
    excluded = {b if a in template.sections else a for a, b in EXCLUSIVE_PAIRS}
    return [s for s in TemplateSection if s not in template.sections and s not in excluded]
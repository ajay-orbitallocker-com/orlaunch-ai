"""
Select template: the AI reads the founder's idea and picks the template labels.

The result's labels go to build_template(). In the chatbot, the founder confirms
any label that is not high confidence before that happens. If the AI returns
labels that break a rule (for example "unknown" combined with another value),
it is asked again with the reason.
"""

from openai import OpenAI
from pydantic import ValidationError

from ai.gpt.config import TEMPLATE_SELECTION_MAX_ATTEMPTS, TEMPLATE_SELECTION_MODEL
from ai.prompts.template_prompts import build_template_messages
from ai.schemas.template_selection_schema import TemplateSelectionResult


def select_template(idea: str, client: OpenAI) -> TemplateSelectionResult:
    """Return the labels, project name and confidence for one idea."""
    feedback = None
    for _ in range(TEMPLATE_SELECTION_MAX_ATTEMPTS):
        try:
            response = client.chat.completions.parse(
                model=TEMPLATE_SELECTION_MODEL,
                messages=build_template_messages(idea, feedback),
                response_format=TemplateSelectionResult,
            )
        except ValidationError as error:
            feedback = str(error)  # tell the AI which rule it broke
            continue
        result = response.choices[0].message.parsed
        if result is None:
            raise ValueError("The model returned no labels.")
        return result

    raise ValueError(f"No valid labels after {TEMPLATE_SELECTION_MAX_ATTEMPTS} attempts: {feedback}")
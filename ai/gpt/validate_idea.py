"""
Validate idea: the query-routing gate.

Confirms the text is a genuine venture idea before any template selection,
outline planning or generation runs, so a rejected idea costs one LLM call.
"""

from ai.gpt.llm import call_structured_llm
from ai.prompts.cdd_prompts import build_query_routing_prompt
from ai.schemas.cdd_schema import IdeaValidationResult


def validate_idea_text(idea_text: str) -> None:
    """Raise ValueError if the text is empty or not a venture idea."""
    if not idea_text or not idea_text.strip():
        raise ValueError("Idea text is empty.")

    system_prompt, user_prompt = build_query_routing_prompt(idea_text)
    result = call_structured_llm(system_prompt, user_prompt, IdeaValidationResult)
    if not result.is_venture_idea:
        raise ValueError(f"Idea text rejected by query routing: {result.reason}")
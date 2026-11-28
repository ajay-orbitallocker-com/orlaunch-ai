"""LLM call shared by the generation modules: one prompt in, one structured object out."""

from pydantic import BaseModel

from chroma_config import client
from ai.gpt.config import GENERATION_MODEL


def call_structured_llm(system_prompt: str, user_prompt: str, schema: type[BaseModel]) -> BaseModel:
    """Send one system and user prompt, return the reply parsed into the given schema."""
    try:
        response = client.chat.completions.parse(
            model=GENERATION_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=schema,
        )
        return response.choices[0].message.parsed
    except Exception as e:
        raise RuntimeError(f"LLM call failed: {e}") from e
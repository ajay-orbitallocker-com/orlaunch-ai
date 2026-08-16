"""
Shared text processing and document formatting utilities for ingestion.
"""
from bs4 import BeautifulSoup


def strip_html(text: str) -> str:
    """Minimal HTML-to-text cleanup for descriptions and benefits fields."""
    if not text:
        return ""
    return BeautifulSoup(text, "html.parser").get_text(separator=" ", strip=True)


def format_field_line(label: str, value: str | int | float | None) -> str:
    """Format a single key-value line if value is present."""
    if value is None or str(value).strip() == "":
        return ""
    return f"{label}: {value}"


def build_document_text(title: str, category: str, source: str, fields: dict) -> str:
    """
    Build a standardized labeled-field text block for vector embeddings across ingestion modules.
    """
    lines = [
        f"Title: {title}",
        f"Category: {category}",
        f"Source: {source}"
    ]
    for label, val in fields.items():
        line = format_field_line(label, val)
        if line:
            lines.append(line)
    return "\n".join(lines)

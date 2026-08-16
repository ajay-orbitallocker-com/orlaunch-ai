from bs4 import BeautifulSoup


def strip_html(text: str) -> str:
    """Minimal HTML-to-text cleanup for description/benefits fields."""

    if not text:
        return ""

    return BeautifulSoup(text, "html.parser").get_text(separator=" ", strip=True)


def format_field_line(label: str, value) -> str | None:
    """Format a single 'Label : value' line, or None if value is empty."""

    if not value:
        return None

    return f"{label} : {value}"


def build_document_text(lines: list[str]) -> str:
    """Join already-formatted label lines into one text block."""

    return "\n".join(lines)

import re
from datetime import datetime
from pathlib import Path

from fpdf import FPDF
from pydantic import BaseModel

OUTPUTS_DIR = Path(__file__).resolve().parent.parent.parent / "outputs"

# Matches a "[Doc N]" citation marker and captures the number N.
_DOC_CITATION_PATTERN = re.compile(r"\[Doc\s?(\d+)\]", re.IGNORECASE)

# Matches a "## Subheading" markdown line and captures the heading text.
_SUBHEADING_PATTERN = re.compile(r"^##\s+(.+)$")

# Maps non-latin-1 characters (smart quotes, en/em dashes, ellipsis) to latin-1 equivalents for PDF rendering.
_UNICODE_REPLACEMENTS = {
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "…": "...",
}


def _sanitize(text: str) -> str:
    """Replaces unicode punctuation and re-encodes to latin-1 for PDF rendering.

    Args:
        text: Raw text string.

    Returns:
        The text with unicode punctuation replaced and re-encoded to
        latin-1, with unsupported characters dropped.
    """
    for src, dst in _UNICODE_REPLACEMENTS.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", "replace").decode("latin-1")


def _write_line_with_citations(pdf: FPDF, line: str, link_ids: dict[int, int], h: int) -> None:
    """Writes one line, replacing [Doc N] markers with clickable [N] links.

    Args:
        pdf: The FPDF document being written to.
        line: One sanitized line of text.
        link_ids: Doc number mapped to internal link id.
        h: Line height.

    Returns:
        None. Writes the line into the PDF at the current position.
    """
    pos = 0
    for match in _DOC_CITATION_PATTERN.finditer(line):
        if match.start() > pos:
            pdf.write(h, line[pos:match.start()])
        doc_num = int(match.group(1))
        pdf.write(h, f"[{doc_num}]", link=link_ids.get(doc_num, ""))
        pos = match.end()
    if pos < len(line):
        pdf.write(h, line[pos:])
    pdf.ln(h)
    pdf.set_x(pdf.l_margin)


def _write_body_with_citations(pdf: FPDF, text: str, link_ids: dict[int, int], h: int = 6) -> None:
    """Writes section body text, rendering subheadings and citation links.

    Args:
        pdf: The FPDF document being written to.
        text: Unsanitized section body text.
        link_ids: Doc number mapped to internal link id.
        h: Line height.

    Returns:
        None. Writes each line into the PDF, rendering "## Subheading"
        lines in bold and all other lines via _write_line_with_citations.
    """
    sanitized = _sanitize(text)
    body_font = pdf.font_family, pdf.font_style, pdf.font_size_pt

    for line in sanitized.split("\n"):
        heading_match = _SUBHEADING_PATTERN.match(line.strip())
        if heading_match:
            pdf.ln(1)
            pdf.set_font("Helvetica", "B", 12)
            pdf.write(h, heading_match.group(1))
            pdf.ln(h)
            pdf.set_x(pdf.l_margin)
            pdf.set_font(*body_font)
            continue
        if not line.strip():
            continue
        _write_line_with_citations(pdf, line, link_ids, h)


def _write_field_label(pdf: FPDF, label: str, h: int) -> None:
    """Writes a bold field label on its own line.

    Args:
        pdf: The FPDF document being written to.
        label: The field label string.
        h: Line height.

    Returns:
        None. Writes "Label:" in bold on its own line.
    """
    pdf.set_font("Helvetica", "B", 11)
    pdf.write(h, _sanitize(f"{label}:"))
    pdf.ln(h)
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "", 11)


def _write_table_field(pdf: FPDF, label: str, rows: list[dict], h: int) -> None:
    """Writes a labeled field as a table, one column per key.

    Args:
        pdf: The FPDF document being written to.
        label: The field label string.
        rows: A list of dicts with matching keys.
        h: Line height.

    Returns:
        None. Writes the label, then renders the rows as a table.
    """
    _write_field_label(pdf, label, h)
    headers = [k.replace("_", " ").title() for k in rows[0].keys()]
    table_rows = [headers] + [[_sanitize(str(v)) for v in row.values()] for row in rows]
    pdf.set_font("Helvetica", "", 9)
    with pdf.table(table_rows, text_align="LEFT", line_height=5, col_widths=None):
        pass
    pdf.set_font("Helvetica", "", 11)
    pdf.set_x(pdf.l_margin)


def _write_bulleted_field(pdf: FPDF, label: str, items: list, h: int) -> None:
    """Writes a labeled field as a bulleted list.

    Args:
        pdf: The FPDF document being written to.
        label: The field label string.
        items: A list of items.
        h: Line height.

    Returns:
        None. Writes the label, then each item as a "- item" bullet line.
    """
    _write_field_label(pdf, label, h)
    for item in items:
        pdf.write(h, _sanitize(f"-  {item}"))
        pdf.ln(h)
        pdf.set_x(pdf.l_margin)


def _write_extra_fields(pdf: FPDF, section: BaseModel, h: int = 6) -> None:
    """Writes a section's structured fields beyond text and citations.

    Args:
        pdf: The FPDF document being written to.
        section: The section model.
        h: Line height.

    Returns:
        None. Writes every field of the section except text/citations: a
        table for list-of-dict fields, a bulleted list for list fields, or
        a "Label: value" line for scalars.
    """
    for field_name, value in section.model_dump().items():
        if field_name in ("text", "citations") or value in (None, "", []):
            continue
        label = field_name.replace("_", " ").title()
        if isinstance(value, list) and value and isinstance(value[0], dict):
            _write_table_field(pdf, label, value, h)
        elif isinstance(value, list):
            _write_bulleted_field(pdf, label, value, h)
        else:
            pdf.set_font("Helvetica", "B", 11)
            pdf.write(h, _sanitize(f"{label}: "))
            pdf.set_font("Helvetica", "", 11)
            pdf.write(h, _sanitize(str(value)))
            pdf.ln(h)
            pdf.set_x(pdf.l_margin)


def export_cdd_to_pdf(
    cdd: dict[str, BaseModel],
    sources: dict[int, dict] | None = None,
    idea_title: str = "Concept Definition Document",
    output_path: Path | None = None,
) -> Path:
    """Writes the generated CDD sections to a PDF file.

    Args:
        cdd: Section name mapped to section model.
        sources: Doc number mapped to {title, url, category}, or None.
        idea_title: The document's title.
        output_path: Where to write the PDF, or None to generate a
            timestamped path under OUTPUTS_DIR.

    Returns:
        The Path of the written PDF file, containing each section (ordered
        by its leading section number) with its text, citations linked to
        a References section when sources is given, and any extra
        structured fields.
    """
    if output_path is None:
        OUTPUTS_DIR.mkdir(exist_ok=True)
        output_path = OUTPUTS_DIR / f"cdd_{datetime.now():%Y%m%d_%H%M%S}.pdf"

    ordered_sections = sorted(cdd.items(), key=lambda kv: int(kv[0].split(".")[0]))

    pdf = FPDF()
    pdf.add_page()
    link_ids: dict[int, int] = {doc_num: pdf.add_link() for doc_num in sources} if sources else {}

    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 10, _sanitize(idea_title))
    pdf.set_x(pdf.l_margin)
    pdf.ln(4)

    for section_name, section in ordered_sections:
        pdf.set_font("Helvetica", "B", 13)
        pdf.multi_cell(0, 8, _sanitize(section_name))
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "", 11)
        _write_body_with_citations(pdf, section.text, link_ids)
        pdf.set_x(pdf.l_margin)
        _write_extra_fields(pdf, section)
        pdf.ln(4)

    if sources:
        pdf.set_font("Helvetica", "B", 13)
        pdf.multi_cell(0, 8, _sanitize("References"))
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "", 11)
        for doc_num in sorted(sources):
            src = sources[doc_num]
            pdf.set_link(link_ids[doc_num], y=pdf.get_y())
            label = f"[{doc_num}] {src.get('title', 'Untitled Document')}"
            if src.get("category"):
                label += f" ({src['category']})"
            pdf.write(6, _sanitize(label))
            pdf.ln(6)
            pdf.set_x(pdf.l_margin)
            if src.get("url"):
                pdf.write(6, _sanitize(src["url"]), link=src["url"])
                pdf.ln(6)
                pdf.set_x(pdf.l_margin)
        pdf.ln(4)

    pdf.output(str(output_path))
    return output_path

from rag.ingestion.utils import strip_html

TECHPORT_BASE_URL = "https://techport.nasa.gov/api"

def _build_document_lines(title, trl_begin, trl_current, trl_end, description, benefits) -> str:
    """
        Build the labeled-field text block for a TechPort project.
        Takes the raw fetch_project() dict (top-level, nested under 'project').
    """
    
    lines = [f"Title : {title}"]
    trl_parts = []
    if trl_current is not None:
        trl_parts.append(f"current : {trl_current}")
    if trl_begin is not None:
        trl_parts.append(f"start : {trl_begin}")
    if trl_end is not None:
        trl_parts.append(f"target : {trl_end}")
    if trl_parts:
        lines.append(f"TRL : {'. '.join(trl_parts)}")
    
    if description:
        lines.append(f"Description : {description}")
    
    if benefits:
        lines.append(f"Benefits : {benefits}")
    
    return "\n".join(lines)

def build_project_document(item: dict) -> str:
    """Build the labeled-field text block for a TechPort project."""
    data = item.get("project", item)
    return _build_document_lines(
        title=data.get("title", ""),
        trl_begin=data.get("trlBegin"),
        trl_current=data.get("trlCurrent"),
        trl_end=data.get("trlEnd"),
        description=strip_html(data.get("description", "")),
        benefits=strip_html(data.get("benefits", "")),
    )
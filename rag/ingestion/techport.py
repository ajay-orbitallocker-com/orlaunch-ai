import requests
from bs4 import BeautifulSoup


TECHPORT_BASE_URL = "https://techport.nasa.gov/api"


def fetch_project(project_id : int) -> dict:
    """GET /api/projects/{id}, return the raw project dict."""
    response = requests.get(f"{TECHPORT_BASE_URL}/projects/{project_id}")
    response.raise_for_status()
    return response.json()

def strip_html(text : str) ->str:
    """Minimal HTML-to-text cleanup for description/benefits fields."""

    if not text:
        return ""
    
    return  BeautifulSoup(text , "html.parser").get_text(separator = " " , strip = True)

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
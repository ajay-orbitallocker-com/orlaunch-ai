import requests

from rag.ingestion.utils import strip_html, format_field_line, build_document_text
from rag.ingestion.config import USER_AGENT
from rag.ingestion.sources.techport.config import (
    TECHPORT_BASE_URL, TECHPORT_VIEW_URL, UPDATED_SINCE, CANDIDATE_TX_PREFIXES
)


def fetch_all_projects() -> list[dict]:
    """GET /api/projects/search, return the list of result records."""

    response = requests.get (f"{TECHPORT_BASE_URL}/projects/search",
            params={'updatedSince' : UPDATED_SINCE},
             headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    data = response.json()
    return data["results"]

def filter_candidates(projects : list[dict]) -> list[dict]:

    matches = []
    for project in projects:

        description = (project.get("description") or "").lower()
        benefits = (project.get("benefits") or "").lower()
        if not (description or benefits):
            continue


        primary_code = (project.get("primaryTx") or {}).get("code" , "") or ""
        if primary_code.startswith(CANDIDATE_TX_PREFIXES):
            matches.append(project)


    return matches


def build_project_url(project_id) -> str:
    """Public TechPort view-page URL for a project, or '' if no id."""
    return f"{TECHPORT_VIEW_URL}/{project_id}" if project_id else ""


def fetch_project(project_id : int) -> dict:
    """GET /api/projects/{id}, return the raw project dict."""
    response = requests.get(f"{TECHPORT_BASE_URL}/projects/{project_id}", headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return response.json()

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

    description_line = format_field_line("Description", description)
    if description_line:
        lines.append(description_line)

    benefits_line = format_field_line("Benefits", benefits)
    if benefits_line:
        lines.append(benefits_line)

    return build_document_text(lines)

def build_project(project : dict) -> str:
    data = project["project"]

    return _build_document_lines(
        title=data.get("title", ""),
        trl_begin=data.get("trlBegin"),
        trl_current=data.get("trlCurrent"),
        trl_end=data.get("trlEnd"),
        description=strip_html(data.get("description", "")),
        benefits=strip_html(data.get("benefits", "")),
    )


def build_project_from_scratch(item : dict) -> str:

    return _build_document_lines(
        title = item.get("title" , ""),
        trl_begin = item.get("trlBegin"),
        trl_current = item.get("trlCurrent"),
        trl_end = item.get("trlEnd"),
        description = strip_html(item.get("description" , "")),
        benefits = strip_html(item.get("benefits" , "")),
    )


def build_techport_documents(projects : list[dict]) -> list[dict]:
    """
    TechPort's fetch_all-style adapter for the multi-source ingestion pipeline
    (rag/ingestion/ingest_all.py). Converts raw TechPort project dicts into the
    common document shape every source is expected to return, so ingest_all.py
    can call this the same way it calls the other sources' fetch_all_x()
    functions instead of hand-building TechPort documents inline.

    Takes:
        projects : list of raw project dicts, as returned by
            fetch_all_projects() (optionally narrowed by filter_candidates()
            and/or sliced for a techport_limit).

    Returns:
        list[dict], one per project, shaped:
        {"id", "text", "title", "category", "source", "trl_current", "url"}.
        "category" is fixed to "Technical & TRL" to match the domain-label
        convention the other 3 sources (SEC/patents/RSS) use, so
        chunk_documents_by_category() and downstream category filtering
        stay consistent across all sources.
    """
    documents = []
    for project in projects:
        project_id = project.get("projectId")
        documents.append({
            "id" : project_id,
            "text" : build_project_from_scratch(project),
            "title" : project.get("title", ""),
            "category" : "Technical & TRL",
            "source" : "NASA TechPort",
            "trl_current" : project.get("trlCurrent"),
            "url" : build_project_url(project_id),
        })
    return documents

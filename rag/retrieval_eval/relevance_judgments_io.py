import json
from pathlib import Path


def load_relevance_judgments(fixture_path: Path) -> dict:
    """Loads the relevance judgments fixture, dropping "_comment"-style keys that aren't real fields."""
    raw = json.loads(fixture_path.read_text(encoding="utf-8"))
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def save_relevance_judgments(fixture_path: Path, payload: dict) -> None:
    fixture_path.parent.mkdir(parents=True, exist_ok=True)
    fixture_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def extract_relevant_ids(judgment_items: list[dict]) -> set[str]:
    return {item["id"] for item in judgment_items if item.get("relevant")}


def diff_relevance_judgments(old_items: list[dict], new_items: list[dict]) -> list[str]:
    """Human-readable added/removed/changed-relevance lines between two relevance judgment item lists."""
    old_by_id = {item["id"]: item for item in old_items}
    new_by_id = {item["id"]: item for item in new_items}

    lines = []
    for doc_id in sorted(set(new_by_id) - set(old_by_id)):
        item = new_by_id[doc_id]
        lines.append(f"  + added {doc_id!r} (relevant={item.get('relevant')}) — {item.get('title', '')}")

    for doc_id in sorted(set(old_by_id) - set(new_by_id)):
        item = old_by_id[doc_id]
        lines.append(f"  - removed {doc_id!r} (was relevant={item.get('relevant')}) — {item.get('title', '')}")

    for doc_id in sorted(set(old_by_id) & set(new_by_id)):
        old_relevant = old_by_id[doc_id].get("relevant")
        new_relevant = new_by_id[doc_id].get("relevant")
        if old_relevant != new_relevant:
            lines.append(f"  ~ changed {doc_id!r}: relevant {old_relevant} -> {new_relevant}")

    return lines

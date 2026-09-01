from pathlib import Path

from rag.hallucination.config import JUDGE_MODEL  # noqa: F401 (re-exported for use as the relevance judgments judge model)

CANDIDATE_POOL_SIZE = 15
DEFAULT_K_VALUES = (3, 5)
REFERENCE_QUERY_ID = "satellite_repair_droid"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

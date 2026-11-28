"""Evidence categories, and the trust level that decides which collection each goes into."""

from __future__ import annotations

from enum import Enum

class TrustTier(str, Enum):
    """How far a source can be relied on """

    PRIMARY = "primary"   # official records, research, filings 
    NEWS = "news"         # journalism and press releases

class Category(str, Enum):
    """Retrieval searches each one separately."""

    TECHNICAL = "technical"     # TechPort, NTRS, arXiv
    PATENTS = "patents"         # granted patents and applications
    FINANCIAL = "financial"     # company filings
    FUNDING = "funding"         # contracts, grants, SBIR awards
    REGULATORY = "regulatory"   # regulations, rule notices, FCC actions
    MARKET = "market"           # news headlines and summaries
    PLANETARY = "planetary"     # mission reports and science papers

    # Every category's trust tier, so each chunk lands in the right collection.
CATEGORY_TRUST: dict[Category, TrustTier] = {
    Category.TECHNICAL: TrustTier.PRIMARY,
    Category.PATENTS: TrustTier.PRIMARY,
    Category.FINANCIAL: TrustTier.PRIMARY,
    Category.FUNDING: TrustTier.PRIMARY,
    Category.REGULATORY: TrustTier.PRIMARY,
    Category.MARKET: TrustTier.NEWS,
    Category.PLANETARY: TrustTier.PRIMARY,
}
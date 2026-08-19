import requests
import hashlib
import xml.etree.ElementTree as ET
from rag.ingestion.config import USER_AGENT
from rag.ingestion.sources.rss_market.config import RSS_FEEDS
from rag.ingestion.utils import strip_html, format_field_line, build_document_text

MARKET_REPAIR_KEYWORDS = [
    "servicing", "repair", "debris", "docking", "rpo", "osam",
    "robotics", "astroscale", "clearspace", "spacelogistics",
    "northrop", "life extension", "refueling", "in-space servicing"
]

def fetch_rss_feed(feed_info: dict, max_items: int = 10) -> list[dict]:
    """Fetch and parse space industry news items from RSS feeds matching repair droid focus."""
    headers = {"User-Agent": USER_AGENT}
    items = []

    try:
        response = requests.get(feed_info["url"], headers=headers, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            channel = root.find("channel")
            if channel is not None:
                for elem in channel.findall("item"):
                    title = elem.findtext("title", "")
                    link = elem.findtext("link", "")
                    pub_date = elem.findtext("pubDate", "")
                    description_raw = elem.findtext("description", "")

                    clean_desc = strip_html(description_raw) if description_raw else ""
                    combined = f"{title} {clean_desc}".lower()

                    # Filter for relevant servicing / satellite market news
                    if any(kw in combined for kw in MARKET_REPAIR_KEYWORDS):
                        if title and (clean_desc or link):
                            stable_id = f"NEWS_{hashlib.sha256(link.encode('utf-8')).hexdigest()[:12]}"
                            lines = [
                                format_field_line("Title", title),
                                format_field_line("Source", f"{feed_info['name']} News"),
                                format_field_line("Category", "Market Intelligence & Sector Trends"),
                                format_field_line("Publication Date", pub_date),
                                format_field_line("Summary", clean_desc)
                            ]
                            lines = [line for line in lines if line is not None]
                            doc_text = build_document_text(lines)

                            items.append({
                                "id": stable_id,
                                "title": title,
                                "text": doc_text,
                                "category": "Market Intelligence",
                                "source": feed_info["name"],
                                "url": link
                            })
                            if len(items) >= max_items:
                                break
    except Exception as e:
        print(f"Error fetching RSS feed {feed_info['name']}: {e}")

    return items

def fetch_all_market_news() -> list[dict]:
    """Fetch market news across all RSS sources."""
    results = []
    for feed in RSS_FEEDS:
        results.extend(fetch_rss_feed(feed, max_items=10))
    return results

if __name__ == "__main__":
    articles = fetch_all_market_news()
    print(f"Successfully fetched {len(articles)} market intelligence news items.")
    if articles:
        print("Sample Market News Item:\n", articles[0]["text"])

import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

RSS_FEEDS = [
    {"name": "SpaceNews", "url": "https://spacenews.com/feed/"},
    {"name": "Payload Space", "url": "https://payloadspace.com/feed/"}
]

def fetch_rss_feed(feed_info: dict, max_items: int = 10) -> list[dict]:
    """Fetch and parse space industry news items from RSS feeds."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    items = []
    
    try:
        response = requests.get(feed_info["url"], headers=headers, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            channel = root.find("channel")
            if channel is not None:
                for elem in channel.findall("item")[:max_items]:
                    title = elem.findtext("title", "")
                    link = elem.findtext("link", "")
                    pub_date = elem.findtext("pubDate", "")
                    description_raw = elem.findtext("description", "")
                    
                    clean_desc = BeautifulSoup(description_raw, "html.parser").get_text(strip=True) if description_raw else ""
                    
                    if title and (clean_desc or link):
                        doc_text = f"Title: {title}\nSource: {feed_info['name']} News\nCategory: Market Intelligence & Sector Trends\nDate: {pub_date}\nSummary: {clean_desc}"
                        items.append({
                            "source_id": f"NEWS_{hash(link)}",
                            "title": title,
                            "text": doc_text,
                            "category": "Market Intelligence",
                            "source": feed_info["name"],
                            "url": link
                        })
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

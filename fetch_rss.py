# fetch_rss.py
import os
import feedparser
import re
from dotenv import load_dotenv

load_dotenv()

RSS_FEEDS = {
    "CoinDesk": os.getenv("RSS_COINDESK"),
    "CoinTelegraph": os.getenv("RSS_COINTELEGRAPH"),
    "Decrypt": os.getenv("RSS_DECRYPT")
}

# --- UPGRADED FUNCTION ---
def fetch_token_headlines(token_name_or_symbol: str = None, max_articles: int = 2):
    """
    Fetches headlines. If a token is provided, it filters for that token.
    If no token is provided, it fetches the latest general headlines.
    """
    found_articles = []

    for source_name, feed_url in RSS_FEEDS.items():
        if not feed_url:
            continue

        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            article = {
                "source": source_name,
                "title": entry.get("title", "").strip(),
                "published": entry.get("published", "").strip(),
                "link": entry.get("link", "").strip()
            }
            
            # If no token is specified, just add the latest articles and move on.
            if not token_name_or_symbol:
                found_articles.append(article)
                continue

            # If a token IS specified, filter by it.
            token = token_name_or_symbol.lower()
            summary = entry.get("summary", "")
            combined_text = f"{article['title']} {summary}".lower()

            if re.search(rf"\b\${token}\b", combined_text) or token in combined_text:
                found_articles.append(article)

    # Sort by published date if available, otherwise keep order. A bit of safety.
    try:
        found_articles.sort(key=lambda x: feedparser._parse_date(x['published']), reverse=True)
    except Exception:
        pass # If parsing fails, just use the feed order.

    return found_articles[:max_articles]

# Example usage
if __name__ == "__main__":
    token = input("Enter token name or symbol (e.g., pepe): ")
    headlines = fetch_token_headlines(token)
    if not headlines:
        print("No recent headlines found.")
    else:
        for h in headlines:
            print(f" {h['title']} — {h['source']} ({h['published']})")
            print(f" {h['link']}\n")


from world_bot.tools.rss import fetch_rss_news
from world_bot.storage import persist_articles


def fetch_and_store_news(max_articles_per_feed: int = 10) -> dict:
    """Fetch news from configured RSS feeds and persist it in SQLite."""
    result = fetch_rss_news(
        max_articles_per_feed=max_articles_per_feed
    )

    saved = persist_articles(result["articles"])

    return {
        "fetched": result["article_count"],
        "processed": saved,
        "errors": result["errors"],
    }


from pathlib import Path
from urllib.request import Request, urlopen
import re
from html import unescape

import feedparser
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = PROJECT_ROOT / "config" / "feeds.yaml"


def load_config() -> dict:
    """Load feed configuration from YAML."""
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    if not isinstance(config.get("feeds"), list):
        raise ValueError("Config must contain a 'feeds' list.")

    return config


def clean_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    return " ".join(unescape(value).split())


def fetch_rss_news(
    feed_names: list[str] | None = None,
    max_articles_per_feed: int = 10,
) -> dict:
    """Fetch articles from configured RSS feeds.

    Args:
        feed_names: Optional feed names to fetch, e.g. ["bbc_world"].
            If omitted, fetch all enabled feeds.
        max_articles_per_feed: Maximum articles per feed (1-30).
    """
    if not 1 <= max_articles_per_feed <= 30:
        return {"articles": [], "errors": [
            "max_articles_per_feed must be between 1 and 30."
        ]}

    config = load_config()
    feeds = {
        feed["name"]: feed
        for feed in config["feeds"]
        if feed.get("enabled", True)
    }

    selected_names = feed_names or list(feeds)
    unknown = [name for name in selected_names if name not in feeds]

    if unknown:
        return {
            "articles": [],
            "errors": [f"Unknown or disabled feeds: {unknown}"],
        }

    timeout = config.get("defaults", {}).get(
        "request_timeout_seconds", 15
    )
    articles = []
    errors = []
    seen_urls = set()

    for name in selected_names:
        feed_config = feeds[name]

        try:
            request = Request(
                feed_config["url"],
                headers={"User-Agent": "WorldBot/0.1 RSS reader"},
            )

            with urlopen(request, timeout=timeout) as response:
                content = response.read(5_000_000)

            parsed = feedparser.parse(content)

            if parsed.bozo and not parsed.entries:
                errors.append(f"{name}: feed could not be parsed")
                continue

            count = 0
            for entry in parsed.entries:
                link = entry.get("link", "").strip()

                if not link or link in seen_urls:
                    continue

                seen_urls.add(link)
                articles.append({
                    "source": name,
                    "perspective": feed_config.get(
                        "perspective", "unclassified"
                    ),
                    "title": clean_html(entry.get("title", "")),
                    "url": link,
                    "published_at": (
                        entry.get("published")
                        or entry.get("updated")
                        or ""
                    ),
                    "summary": clean_html(
                        entry.get("summary", "")
                    )[:2000],
                })

                count += 1
                if count >= max_articles_per_feed:
                    break

        except Exception as exc:
            errors.append(f"{name}: {type(exc).__name__}: {exc}")

    return {
        "articles": articles,
        "article_count": len(articles),
        "feeds_requested": selected_names,
        "errors": errors,
    }

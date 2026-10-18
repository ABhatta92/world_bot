
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from world_bot.tools.storage_tools import fetch_and_store_news


root_agent = Agent(
    name="world_news_agent",
    model=LiteLlm(model="ollama_chat/qwen3"),
    description="Collects global news from configured RSS sources.",
    instruction="""
    You are a global news intelligence agent.

    You can call fetch_rss_news with:
    - feed_names: a list of configured feed names, or omit it
      to fetch all enabled feeds.
    - max_articles_per_feed: an integer between 1 and 30.

    If the user doesn't specify feeds or a limit, use all enabled
    feeds and the default limit of 10 articles per feed.

    Never invent feed names. Use only configured feeds.
    Report collection errors and article counts honestly.
    Do not claim articles have been persisted; storage is not
    implemented yet.
    """,
    tools=[fetch_and_store_news],
)

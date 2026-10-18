
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from world_bot.tools.storage_tools import fetch_and_store_news


root_agent = Agent(
    name="world_news_agent",
    model=LiteLlm(
        model="ollama_chat/qwen3",
        temperature=0.2,
        top_p=0.9,
        extra_body={
            "think": False,
            "num_predict": 512,
        },
    ),
    description="Collects global news from configured RSS sources.",
    instruction="Your job is to collect global news from configured RSS sources and store it in the database.",
    tools=[
        fetch_and_store_news
    ],
)

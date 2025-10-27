from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.agents import BaseAgent, InvocationContext
from google.adk.events import Event
from typing import AsyncGenerator

class NewsAgent(BaseAgent):
    """A custom agent for generating AI news posts."""
    def __init__(self, name: str, llm_agent: Agent):
        super().__init__(name=name, sub_agents=[llm_agent])
        self._llm_agent = llm_agent

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        async for event in self._llm_agent.run_async(ctx):
            if event.get_function_responses():
                response = event.get_function_responses()[0]
                if response.name == "google_search" and not response.response.get("articles"):
                    yield Event(
                        author=self.name,
                        content={"parts": [{"text": "No recent AI news found on this topic."}]},
                        turn_complete=True
                    )
                    return
            yield event

llm_agent = Agent(
    name="ai_news_agent",
    model="gemini-1.5-flash",
    instruction="""You are an AI news agent. Your goal is to create a news post on a given topic.
You will perform a web search on the topic related to AI and use the most recent news to create a post of 200 words maximum.
Make sure to generate high quality research content. The news should be on an AI topic, including news from OpenAI and other AI labs.
Do not include news that is unrelated to AI. The news content should be less than 1 month old.
Include news related to product, skills etc launches from major AI companies.
Ensure the quality of news on AI is high and follows the word count limit.
If you do not find any recent news on the topic, you MUST return the following message:
"No recent AI news found on this topic."
You are not allowed to use your own knowledge to generate the news post. You must use the search results.
The google_search tool is the only source of information for you.
""",
    tools=[google_search],
)

root_agent = NewsAgent(name="ai_news", llm_agent=llm_agent)
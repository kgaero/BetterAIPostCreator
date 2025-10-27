import unittest
import asyncio
from unittest.mock import patch

from google.adk.agents import InvocationContext, Agent
from google.adk.sessions import InMemorySessionService
from google.adk.events import Event
from google.genai.types import FunctionCall, FunctionResponse, Content, Part

from agents.ai_news.agent import NewsAgent


class TestAINewsAgent(unittest.IsolatedAsyncioTestCase):

    async def test_generate_news_post_with_no_recent_news(self):
        # Arrange
        mock_llm_agent = Agent(name="mock_llm_agent", model="gemini-1.5-flash")

        async def mock_run_async_impl(ctx):
            yield Event(
                author=mock_llm_agent.name,
                content={
                    "parts": [{"function_call": FunctionCall(name="google_search", args={"query": "unheard of AI topic"})}]
                }
            )
            yield Event(
                author="tool",
                content={
                    "parts": [{"function_response": FunctionResponse(name="google_search", response={"articles": []})}]
                }
            )

        agent = NewsAgent(name="ai_news", llm_agent=mock_llm_agent)
        session_service = InMemorySessionService()
        session_id = "test-session-id"
        app_name = "test-app"
        user_id = "test-user"
        session = await session_service.create_session(session_id=session_id, app_name=app_name, user_id=user_id)
        event = Event(author="user", content=Content(parts=[Part(text="unheard of AI topic")]))
        await session_service.append_event(session, event)
        session = await session_service.get_session(session_id=session_id, app_name=app_name, user_id=user_id)
        ctx = InvocationContext(
            session_service=session_service,
            invocation_id="test-invocation-id",
            agent=agent,
            session=session
        )

        # Act
        final_response = ""
        with patch.object(mock_llm_agent, '_run_async_impl', new=mock_run_async_impl):
            async for event in agent.run_async(ctx):
                if event.is_final_response():
                    final_response = "".join(part.text for part in event.content.parts if part.text)

        # Assert
        self.assertEqual("No recent AI news found on this topic.", final_response)

    async def test_generate_news_post_with_recent_news(self):
        # Arrange
        mock_llm_agent = Agent(name="mock_llm_agent", model="gemini-1.5-flash")
        expected_news_post = "Here is a great news post about recent AI developments."

        async def mock_run_async_impl(ctx):
            yield Event(
                author=mock_llm_agent.name,
                content={
                    "parts": [{"function_call": FunctionCall(name="google_search", args={"query": "recent AI news"})}]
                }
            )
            yield Event(
                author="tool",
                content={
                    "parts": [{"function_response": FunctionResponse(name="google_search", response={"articles": [{"title": "New AI model released", "snippet": "A new AI model was released today."}]})}]
                }
            )
            yield Event(
                author=mock_llm_agent.name,
                content={"parts": [{"text": expected_news_post}]},
                turn_complete=True
            )

        agent = NewsAgent(name="ai_news", llm_agent=mock_llm_agent)
        session_service = InMemorySessionService()
        session_id = "test-session-id"
        app_name = "test-app"
        user_id = "test-user"
        session = await session_service.create_session(session_id=session_id, app_name=app_name, user_id=user_id)
        event = Event(author="user", content=Content(parts=[Part(text="recent AI news")]))
        await session_service.append_event(session, event)
        session = await session_service.get_session(session_id=session_id, app_name=app_name, user_id=user_id)
        ctx = InvocationContext(
            session_service=session_service,
            invocation_id="test-invocation-id",
            agent=agent,
            session=session
        )

        # Act
        final_response = ""
        with patch.object(mock_llm_agent, '_run_async_impl', new=mock_run_async_impl):
            async for event in agent.run_async(ctx):
                if event.is_final_response():
                    final_response = "".join(part.text for part in event.content.parts if part.text)

        # Assert
        self.assertEqual(expected_news_post, final_response)


if __name__ == '__main__':
    unittest.main()

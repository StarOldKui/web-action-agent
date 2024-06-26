import asyncio
import os
from typing import Annotated, Literal
from typing import TypedDict

import nest_asyncio
from amazoncaptcha import AmazonCaptcha
from langchain_community.tools.playwright.utils import (
    create_async_playwright_browser,
)
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langgraph.checkpoint import MemorySaver
from langgraph.graph import END, StateGraph, MessagesState
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.prebuilt import ToolNode
from playwright_stealth import stealth_sync
from typing_extensions import TypedDict
import streamlit as st

from app.amazon_web_agent.tools.amazon_web_agent_toolkit import PlayWrightBrowserToolkit
from utils.chat_model_env_util import ChatModelUtil
from utils.logger_util import LoggerUtil

amazon_email = os.getenv("AMAZON_EMAIL")
amazon_password = os.getenv("AMAZON_PASSWORD")

logger = LoggerUtil.get_logger()

nest_asyncio.apply()


async def async_solve_captcha(page):
    """
    Solve the captcha by extracting the captcha image URL,
    using AmazonCaptcha library to solve it, and submitting the solution.
    """
    # Get the captcha image URL
    captcha_url = await page.get_attribute('img[src*="captcha"]', "src")
    logger.info(f"Captcha URL: {captcha_url}")
    st.write(f"Captcha URL: {captcha_url}")

    # Solve the captcha using AmazonCaptcha library
    captcha = AmazonCaptcha.fromlink(captcha_url)
    solution = captcha.solve()
    logger.info(f"Captcha Solution: {solution}")
    st.write(f"Captcha Solution: {solution}")

    # Fill the captcha solution and submit the form
    await page.fill('input[name="field-keywords"]', solution)
    await page.click('span.a-button-inner > button[type="submit"]')


async def process_stream(app, inputs):
    last_response = None
    async for event in app.astream(
        inputs, config={"configurable": {"thread_id": 1}}, stream_mode="values"
    ):
        message = event.get("messages")
        if message:
            if isinstance(message, list):
                message = message[-1]
            if message.content:
                title = message.type.title() + " Message"
                response = f"{title}: {message.content}"

                logger.info(response)
                st.write(response)

                last_response = response
    return last_response


def amazon_web_agent_run(user_requirement: str):
    """
    Perform actions on Amazon Web Page

    Args:
        user_requirement (str): A prompt specifying the user requirement on how to perform the action on Amazon Web Page
    """
    # Build it with LangGraph

    # Browser
    browser = create_async_playwright_browser(headless=False)

    # LLM
    amazon_web_agent_llm = ChatModelUtil.create_llm()
    # Prompt
    amazon_web_agent_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are a specialized assistant responsible for performing actions on Amazon web pages.
                When a user requests content extraction from a specific web page, always use 'navigate_browser' to navigate to the page first.
                Ensure that the task is only considered complete after you have used 'extract_content' to extract the necessary content from the web page.
                Avoid inventing or using any invalid tools or functions.
                Note: The filename has already been logged, so do not mention the filename in your response.
                """,
            ),
            ("placeholder", "{messages}"),
        ]
    )
    # Tools
    amazon_web_agent_tools = PlayWrightBrowserToolkit.from_browser(
        async_browser=browser
    ).get_tools()
    # Runnable
    amazon_web_agent_runnable = (
        {"messages": RunnablePassthrough()}
        | amazon_web_agent_prompt
        | amazon_web_agent_llm.bind_tools(amazon_web_agent_tools)
    )

    # State
    class State(TypedDict):
        messages: Annotated[list[AnyMessage], add_messages]

    # Sign in node
    async def sign_in_node(state):
        # Launch the browser
        context = await browser.new_context()
        page = await context.new_page()

        # Apply stealth to avoid detection
        # await stealth_sync(page)

        # Open Amazon web page
        await page.goto("https://www.amazon.com")

        # Check if captcha is present
        if await page.is_visible('img[src*="captcha"]'):
            logger.info("Solving the captcha...")
            st.write("Solving the captcha...")
            await async_solve_captcha(page)

        # Open the login page
        await page.click("a#nav-link-accountList")

        # Continue with the login process
        logger.info("Sign in into Amazon")
        st.write("Sign in into Amazon")
        await page.fill("input[name='email']", amazon_email)
        await page.click("input[id='continue']")
        await page.fill("input[name='password']", amazon_password)
        await page.click("input[id='signInSubmit']")

        return {
            "messages": "The user has successfully signed in. Now proceed with the user request."
        }

    # Agent node
    def agent_node(state):
        messages = state["messages"]
        response = amazon_web_agent_runnable.invoke(messages)
        return {"messages": messages + [response]}

    # Tool node
    tool_node = ToolNode(amazon_web_agent_tools)

    workflow = StateGraph(MessagesState)

    workflow.add_node("sign_in_node", sign_in_node)
    workflow.add_node("agent_node", agent_node)
    workflow.add_node("tool_node", tool_node)

    workflow.set_entry_point("sign_in_node")

    workflow.add_edge("sign_in_node", "agent_node")

    def should_continue(state) -> Literal["tool_node", END]:
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tool_node"
        return END

    workflow.add_conditional_edges(
        "agent_node",
        should_continue,
    )

    workflow.add_edge("tool_node", "agent_node")

    # Initialize memory to persist state between graph runs
    checkpointer = MemorySaver()

    app = workflow.compile(checkpointer=checkpointer)

    inputs = {"messages": [HumanMessage(content=user_requirement)]}
    loop = asyncio.get_event_loop()
    last_response = loop.run_until_complete(process_stream(app, inputs))
    return last_response

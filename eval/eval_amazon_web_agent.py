import os
from typing import Annotated, Literal
from typing import TypedDict

import nest_asyncio
import streamlit as st
from amazoncaptcha import AmazonCaptcha
from langchain import hub
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
from typing_extensions import TypedDict

from app.amazon_web_agent.tools.amazon_web_agent_toolkit import PlayWrightBrowserToolkit
from utils.chat_model_env_util import ChatModelUtil
from utils.logger_util import LoggerUtil

amazon_email = os.getenv("AMAZON_EMAIL")
amazon_password = os.getenv("AMAZON_PASSWORD")

logger = LoggerUtil.get_logger()

nest_asyncio.apply()

# LangSmith
from langsmith import Client, evaluate
from langsmith.schemas import Example, Run

client = Client()
# Create a dataset
examples = [
    (
        "Show me my shopping cart info on Amazon",
        "I have extracted the shopping cart information from Amazon. The details have been saved in a JSON file.",
    )
]

dataset_name = "Amazon Web Agent Data"
if not client.has_dataset(dataset_name=dataset_name):
    dataset = client.create_dataset(dataset_name=dataset_name)
    inputs, outputs = zip(
        *[({"input": text}, {"output": label}) for text, label in examples]
    )
    client.create_examples(inputs=inputs, outputs=outputs, dataset_id=dataset.id)


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


def eval_amazon_web_agent_run():
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

    def predict_assistant(example: dict):
        """Invoke assistant for single tool call evaluation"""
        human_message = HumanMessage(content=example["input"])
        messages = [human_message]
        result = amazon_web_agent_runnable.invoke(messages)
        return {"response": result}

    def check_specific_tool_call(root_run: Run, example: Example) -> dict:
        """
        Check if the first tool call in the response matches the expected tool call.
        """
        # Exepected tool call
        expected_tool_call = 'navigate_browser'

        # Run
        response = root_run.outputs["response"]

        # Get tool call
        try:
            tool_call = getattr(response, 'tool_calls', [])[0]['name']
        except (IndexError, KeyError):
            tool_call = None

        score = 1 if tool_call == expected_tool_call else 0
        return {"score": score, "key": "single_tool_call"}

    experiment_results = evaluate(
        predict_assistant,
        data=dataset_name,
        evaluators=[check_specific_tool_call],
        experiment_prefix="check-single-tool",
        num_repetitions=1,
    )


if __name__ == "__main__":
    eval_amazon_web_agent_run()

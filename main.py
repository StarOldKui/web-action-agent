import streamlit as st
from langchain.agents import AgentExecutor
from langchain.agents import create_tool_calling_agent
from langchain.tools import StructuredTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.pydantic_v1 import BaseModel, Field

from app.amazon_web_agent.amazon_web_agent import amazon_web_agent_run
from utils.chat_model_env_util import ChatModelUtil
from utils.env_util import EnvLoader
from utils.logger_util import LoggerUtil

logger = LoggerUtil.get_logger()

# nest_asyncio.apply()


# Amazon web agent tool
class InvokeAmazonWebAgentInput(BaseModel):
    user_requirement: str = Field(
        ...,
        description="A prompt specifying the user requirement on what action to perform on Amazon Web Page",
    )


invoke_amazon_web_agent_tool = StructuredTool.from_function(
    func=amazon_web_agent_run,
    name="InvokeAmazonWebAgent",
    description="Perform actions on Amazon Web Page",
    args_schema=InvokeAmazonWebAgentInput,
)


def start_web_action_agent(user_input: str):
    web_agent_llm = ChatModelUtil.create_llm()
    web_agent_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are a specialized assistant tasked on performing actions on different web pages.
                You should delegate the task to the appropriate specialized assistant by invoking the corresponding tool. 
                You are not able to complete the task by your own. 
                Only the specialized assistants are given permission to do this for the user.
                The user is not aware of the different specialized assistants, so do not mention them; just quietly delegate through function calls.    
                """,
            ),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad", optional=True),
        ]
    )
    web_agent_tools = [invoke_amazon_web_agent_tool]
    web_agent = create_tool_calling_agent(
        web_agent_llm, web_agent_tools, web_agent_prompt
    )
    web_agent_executor = AgentExecutor(
        agent=web_agent, tools=web_agent_tools, verbose=True
    )

    web_agent_executor.invoke({"input": user_input})


if __name__ == "__main__":
    # Load environment variables
    EnvLoader()

    st.title("Web Agent")

    user_input = st.text_input("Enter your input here:")

    if st.button("Run Workflow"):
        with st.spinner("Running workflow..."):
            # Start running the web action agent
            start_web_action_agent(user_input)

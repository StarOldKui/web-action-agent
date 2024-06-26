import os
from enum import Enum, auto
from typing import Union

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI, AzureChatOpenAI

from utils.env_util import EnvLoader
from utils.logger_util import LoggerUtil

# Load environment variables
EnvLoader()

logger = LoggerUtil.get_logger()


class ModelType(Enum):
    """Enum to represent the model type."""

    ChatOpenAI = auto()
    AzureChatOpenAI = auto()


class ChatModelUtil:
    """Configuration class for chat model. Initialize the chat model based on environment variables."""

    _llm = None

    @classmethod
    def initialize_llm(cls):
        """
        Initializes the `llm` class variable using configuration parameters specified through environment variables.

        Key steps:
        - Loads environment variables to configure the chat model.
        - Determines the model type (e.g., ChatOpenAI, AzureChatOpenAI) based on the `LLM_MODEL_TYPE` environment variable.
        - Collects additional configuration parameters (if any) from environment variables prefixed with `LLM_`, and prepares them for model initialization.
        - Initializes the chat model instance with the specified configuration.

        Example Environment Variables:
        - LLM_MODEL_TYPE=ChatOpenAI
        - LLM_MODEL=gpt-3.5-turbo-1106
        - LLM_TEMPERATURE=0
        The method will:
        - Recognize the model type as ChatOpenAI.
        - Extract and convert the additional parameters into `kwargs`: `model="gpt-3.5-turbo-1106"` and `temperature=0`.
        - Use these parameters to initialize a ChatOpenAI model instance.
        """
        try:
            logger.info(f"Initializing llm")

            # Extract and process environment variables starting with "LLM_" to configure the model
            kwargs = {
                key[4:].lower(): cls._parse_env_value(value)
                for key, value in os.environ.items()
                if key.startswith("LLM_")
            }
            model_type = ModelType[kwargs.pop("model_type")]

            if model_type == ModelType.AzureChatOpenAI:
                cls._llm = AzureChatOpenAI(**kwargs)
            elif model_type == ModelType.ChatOpenAI:
                cls._llm = ChatOpenAI(**kwargs)
            else:
                raise ValueError(f"Unsupported model type: {model_type}")

            logger.info("LLM initialization complete.")
        except Exception as e:
            logger.error(f"Failed to initialize chat model due to error: {e}")
            raise

    @staticmethod
    def _parse_env_value(value: str) -> Union[str, int, float]:
        """Attempt to parse environment variable string value into int or float if applicable."""
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        # Return as string if not int or float
        return value

    @staticmethod
    def get_llm() -> BaseChatModel:
        if ChatModelUtil._llm is None:
            ChatModelUtil.initialize_llm()
        return ChatModelUtil._llm

    @classmethod
    def create_llm(cls) -> BaseChatModel:
        """
        Initialize a new LLM instance using configuration parameters specified through environment variables.

        Key steps:
        - Load environment variables to configure the chat model.
        - Determine the model type (e.g., ChatOpenAI, AzureChatOpenAI) based on the `LLM_MODEL_TYPE` environment variable.
        - Collect additional configuration parameters (if any) from environment variables prefixed with `LLM_`, and prepare them for model initialization.
        - Initialize the chat model instance with the specified configuration.

        Example Environment Variables:
        - LLM_MODEL_TYPE=ChatOpenAI
        - LLM_MODEL=gpt-3.5-turbo-1106
        - LLM_TEMPERATURE=0
        The method will:
        - Recognize the model type as ChatOpenAI.
        - Extract and convert the additional parameters into `kwargs`: `model="gpt-3.5-turbo-1106"` and `temperature=0`.
        - Use these parameters to initialize a ChatOpenAI model instance.
        """
        try:
            logger.info(f"Initializing llm")

            # Extract and process environment variables starting with "LLM_" to configure the model
            kwargs = {
                key[4:].lower(): cls._parse_env_value(value)
                for key, value in os.environ.items()
                if key.startswith("LLM_")
            }
            model_type = ModelType[kwargs.pop("model_type")]

            if model_type == ModelType.AzureChatOpenAI:
                return AzureChatOpenAI(**kwargs)
            elif model_type == ModelType.ChatOpenAI:
                return ChatOpenAI(**kwargs)
            else:
                raise ValueError(f"Unsupported model type: {model_type}")

        except Exception as e:
            logger.error(f"Failed to initialize chat model due to error: {e}")
            raise

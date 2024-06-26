import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from utils.logger_util import LoggerUtil

logger = LoggerUtil.get_logger()


class EnvLoader:
    """
    A singleton class for loading environment variables.

    This class ensures that environment variables are loaded only once,
    regardless of how many times the EnvLoader is instantiated.
    """

    _instance = None
    _is_loaded = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EnvLoader, cls).__new__(cls)
            if not cls._is_loaded:
                try:
                    # Current path
                    current_path = Path(os.getcwd())
                    # Env path
                    dotenv_path = cls._find_dotenv(current_path)

                    if dotenv_path:
                        load_dotenv(dotenv_path=dotenv_path)
                        logger.info(f"Environment variables loaded from: {dotenv_path}")
                    else:
                        raise ValueError("Couldn't find .env file.")

                    cls._is_loaded = True
                except Exception as e:
                    logger.error(f"Failed to load environment variables: {e}")

        return cls._instance

    @staticmethod
    def _find_dotenv(start_path: Path) -> Any | None:
        """Traverse up the file system to find a file named .env and return its path, including the current directory."""
        # Check the current directory first
        dotenv_path = start_path / ".env"
        if dotenv_path.exists():
            return dotenv_path

        # If not found, traverse up the file system
        for parent in start_path.parents:
            dotenv_path = parent / ".env"
            if dotenv_path.exists():
                return dotenv_path
        return None

    @staticmethod
    def list_env_variables() -> None:
        """List all environment variables."""
        for key, value in os.environ.items():
            print(f"{key}: {value}")

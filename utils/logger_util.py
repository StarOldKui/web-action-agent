import logging
import sys


class LoggerUtil:
    @staticmethod
    def get_logger():
        logger = logging.getLogger()

        # Used for local testing
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(stream=sys.stdout)],
        )

        # Get the logger for httpx
        httpx_logger = logging.getLogger("httpx")
        # Set the logging level to WARNING to suppress INFO logs
        httpx_logger.setLevel(logging.WARNING)

        return logger

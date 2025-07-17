import logging
import os

from dotenv import load_dotenv
from rich.logging import RichHandler

# load the .env file.
load_dotenv()


def setup_logging(name: str) -> logging.Logger:
    """
    Set up a logger with the specified name and logging level.
    If no level is provided, it defaults to INFO.
    """

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()  # Default log level

    logging.basicConfig(
        level=log_level,
        format="%(name)s %(message)s",
        handlers=[
            RichHandler(
                show_time=True, show_level=True, show_path=False, markup=True, rich_tracebacks=True
            )
        ],
    )

    return logging.getLogger(name)


logger = setup_logging("hive-cli")

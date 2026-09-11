import os
import logging
from dotenv import load_dotenv

# Load .env from project root
load_dotenv()

logger = logging.getLogger(__name__)


def get_openai_api_key() -> str:
    """
    Retrieves the OpenAI API key from environment variables.

    Returns:
        str: The OpenAI API key.

    Raises:
        ValueError: If OPENAI_API_KEY is missing or empty.
    """
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key or not api_key.strip() or api_key.strip() == "your_openai_api_key_here":
        raise ValueError(
            "Missing OPENAI_API_KEY. Please add your OpenAI API key to the .env file:\n"
            "OPENAI_API_KEY=your_openai_api_key_here"
        )

    return api_key.strip()

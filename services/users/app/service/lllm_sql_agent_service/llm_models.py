import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("GPT_KEY"), timeout=60.0, max_retries=2)
    return _client


def ask_ai(prompt: str) -> str:
    response = _get_client().chat.completions.create(
        model="gpt-5.4",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

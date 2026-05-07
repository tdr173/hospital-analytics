import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("GPT_KEY")

# 60s caps hung / slow requests. With max_retries=2 the client retries
# transient network errors twice before propagating.
client = OpenAI(api_key=api_key, timeout=60.0, max_retries=2)


def ask_ai(prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-5.4",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("GPT_KEY")

client = OpenAI(api_key=api_key)

def ask_ai(prompt: str):
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content
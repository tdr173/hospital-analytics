import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("GPT_KEY")

client = OpenAI(api_key=api_key)

def ask_ai(prompt: str):
    response = client.responses.create(
        model="gpt-5.2",
        input=prompt,
    )
    return response.output_text
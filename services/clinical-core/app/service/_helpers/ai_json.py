import json
import re


def parse_ai_json(raw: str) -> dict:
    stripped = re.sub(r"```(?:json)?\s*(.*?)\s*```", r"\1", raw, flags=re.DOTALL)
    return json.loads(stripped.strip())

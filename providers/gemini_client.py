from __future__ import annotations
import os
from google import genai


def make_gemini_invoke(model_name: str = "gemini-2.5-flash"):
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not set in environment")

    client = genai.Client(api_key=api_key)

    def invoke(prompt: str) -> str:
        response = client.models.generate_content(model=model_name, contents=prompt)
        return response.text

    return invoke
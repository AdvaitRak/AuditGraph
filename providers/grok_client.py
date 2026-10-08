from __future__ import annotations
import os
from groq import Groq


def make_groq_invoke(model_name: str = "llama-3.3-70b-versatile"):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set in environment")

    client = Groq(api_key=api_key)

    def invoke(prompt: str) -> str:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

    return invoke
from __future__ import annotations
import os
import google.generativeai as genai


def make_gemini_invoke(model_name: str = "gemini-2.5-flash"):
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not set in environment")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    def invoke(prompt: str) -> str:
        response = model.generate_content(prompt)
        return response.text

    return invoke
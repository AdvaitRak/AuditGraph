from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _env_int(name: str, default: int) -> int:
    return int(os.environ.get(name, default))


def _env_float(name: str, default: float) -> float:
    return float(os.environ.get(name, default))


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str | None
    gemini_model: str

   
    max_react_steps: int          
    max_files_to_fix: int         

    
    llm_max_retries: int          
    llm_min_interval_seconds: float  

    max_observation_chars: int  


def load_settings() -> Settings:
    return Settings(
        gemini_api_key=os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"),
        gemini_model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        max_react_steps=_env_int("MAX_REACT_STEPS", 8),
        max_files_to_fix=_env_int("MAX_FILES_TO_FIX", 3),
        llm_max_retries=_env_int("LLM_MAX_RETRIES", 4),
        llm_min_interval_seconds=_env_float("LLM_MIN_INTERVAL_SECONDS", 4.0),
        max_observation_chars=_env_int("MAX_OBSERVATION_CHARS", 3000),
    )
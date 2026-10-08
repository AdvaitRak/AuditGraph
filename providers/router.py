from __future__ import annotations
import logging
from typing import Callable

logger = logging.getLogger("auditgraph.providers.router")

Provider = tuple[str, Callable[[str], str]]


class AllProvidersFailedError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"All providers failed — {'; '.join(errors)}")


class ProviderRouter:
    def __init__(self, providers: list[Provider]):
        if not providers:
            raise ValueError("ProviderRouter needs at least one provider")
        self.providers = providers

    def invoke(self, prompt: str) -> str:
        errors: list[str] = []

        for name, invoke_fn in self.providers:
            try:
                response = invoke_fn(prompt)
                logger.info("provider=%s succeeded", name)
                return response
            except Exception as e:
                logger.warning("provider=%s failed: %s", name, e)
                errors.append(f"{name}: {type(e).__name__}: {e}")

        raise AllProvidersFailedError(errors)
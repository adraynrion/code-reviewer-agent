"""Langfuse configuration for the code review agent."""

import os
from typing import Any


# Mock tracer used when Langfuse is not configured
class MockTracer:
    def trace(self: "MockTracer", *args: Any, **kwargs: Any) -> "MockTracer":
        return self

    def end(self: "MockTracer", *args: Any, **kwargs: Any) -> None:
        pass

    def __call__(self: "MockTracer", *args: Any, **kwargs: Any) -> "MockTracer":
        return self


def configure_langfuse() -> Any:
    """Configure and return a Langfuse tracer.

    Returns:
        Langfuse tracer instance

    """
    langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if not langfuse_secret_key or not langfuse_public_key:
        # Return a mock tracer if Langfuse is not configured
        return MockTracer()

    try:
        from langfuse import Langfuse

        langfuse = Langfuse(
            public_key=langfuse_public_key,
            secret_key=langfuse_secret_key,
            host=langfuse_host,
        )

        return langfuse.trace
    except ImportError:
        # Return a mock tracer if Langfuse is not installed
        return MockTracer()

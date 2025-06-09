import base64
import os

import logfire
import nest_asyncio
from dotenv import load_dotenv
from opentelemetry import trace

load_dotenv()


def scrubbing_callback(match: logfire.ScrubMatch) -> str:
    """Preserve the Langfuse session ID.

    Args:
        match: The match object containing information about the value to be scrubbed

    Returns:
        str: The original value if it's a Langfuse session ID, otherwise an empty string

    """
    if (
        match.path == ("attributes", "langfuse.session.id")
        and match.pattern_match.group(0) == "session"
        and match.value is not None
    ):
        # Return the original value to prevent redaction.
        return str(match.value)
    return ""


# Configure Langfuse for agent observability
def configure_langfuse() -> trace.Tracer:
    LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
    LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
    LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "http://localhost:3002")
    LANGFUSE_AUTH = base64.b64encode(
        f"{LANGFUSE_PUBLIC_KEY}:{LANGFUSE_SECRET_KEY}".encode()
    ).decode()

    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"{LANGFUSE_HOST}/api/public/otel"
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {LANGFUSE_AUTH}"

    # Configure Logfire to work with Langfuse
    nest_asyncio.apply()
    logfire.configure(
        service_name="pydantic_ai_agent",
        send_to_logfire=False,
        scrubbing=logfire.ScrubbingOptions(callback=scrubbing_callback),
    )

    return trace.get_tracer("pydantic_ai_agent")

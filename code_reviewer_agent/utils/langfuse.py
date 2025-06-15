"""Langfuse configuration for the code review agent."""

import base64
import os

import logfire
from langfuse import Langfuse
from opentelemetry.trace import Tracer

from code_reviewer_agent.models.base_types import StringValidator
from code_reviewer_agent.models.pydantic_config_models import LangfuseConfig
from code_reviewer_agent.utils.rich_utils import print_success, print_warning


class LangfuseKey(StringValidator):
    pass


class LangfuseHost(StringValidator):
    pass


class LangfuseModel:
    """LangfuseModel singleton."""

    _instance = None

    _tracer = None
    _public_key = LangfuseKey()
    _secret_key = LangfuseKey()
    _host = LangfuseHost()
    _enabled = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(LangfuseModel, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, config: LangfuseConfig) -> None:
        self._public_key = config.public_key
        self._secret_key = config.secret_key
        self._host = config.host
        self._enabled = config.enabled

    @property
    def tracer(self) -> Tracer:
        if not self._tracer:
            raise ValueError(
                "Langfuse is not initialized. Please correctly initialize it first."
            )
        return self._tracer

    @property
    def public_key(self) -> LangfuseKey:
        return self._public_key

    @property
    def secret_key(self) -> LangfuseKey:
        return self._secret_key

    @property
    def host(self) -> LangfuseHost:
        return self._host

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        if not value:
            print_warning("Langfuse is now disabled.")
            self._tracer = None
            return

        try:
            if not self.public_key or not self.secret_key or not self.host:
                raise ValueError(
                    "Langfuse is not entirely configured. Missing public_key, secret_key or host."
                )

            # Define environment variables for OpenTelemetry
            auth = base64.b64encode(
                f"{self.public_key}:{self.secret_key}".encode()
            ).decode()
            os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"{self.host}/api/public/otel"
            os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {auth}"

            # Configure Logfire to work with Langfuse
            logfire.configure(
                service_name="pydantic_ai_agent",
                send_to_logfire=False,
                scrubbing=logfire.ScrubbingOptions(
                    callback=self.__class__.scrubbing_callback
                ),
            )

            client = Langfuse(
                public_key=self.public_key,
                secret_key=self.secret_key,
                host=self.host,
            )
            self._tracer = client.trace()
            print_success("Langfuse initialized successfully!")
        except ImportError as e:
            raise ImportError(f"Langfuse import failed: {str(e)}")
        except ValueError as e:
            raise ValueError(f"Langfuse configuration failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Langfuse initialization failed: {str(e)}")

    @staticmethod
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

"""Langfuse integration for the code review agent."""
import os
import json
from datetime import datetime, timezone
from langfuse import Langfuse
from typing import Dict, Any, Optional, Union, List

class LangfuseTracer:
    """A class to handle Langfuse tracing for the code review agent."""

    def __init__(self, public_key: Optional[str] = None, secret_key: Optional[str] = None, host: str = "https://cloud.langfuse.com"):
        """Initialize the Langfuse tracer.

        Args:
            public_key: Langfuse public key
            secret_key: Langfuse secret key
            host: Langfuse host URL
        """
        self.public_key = public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
        self.secret_key = secret_key or os.getenv("LANGFUSE_SECRET_KEY")
        self.host = host or os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        self.langfuse = self._init_langfuse()
        self.trace = None
        self.current_span = None

    def _init_langfuse(self):
        """Initialize the Langfuse client."""
        if not self.public_key or not self.secret_key:
            print("Warning: Langfuse credentials not provided. Langfuse tracing will be disabled.")
            return None

        try:
            return Langfuse(
                public_key=self.public_key,
                secret_key=self.secret_key,
                host=self.host,
            )
        except Exception as e:
            print(f"Warning: Failed to initialize Langfuse client: {e}")
            return None

    def start_trace(self, trace_id: str, name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start a new trace.

        Args:
            trace_id: Unique identifier for the trace
            name: Name of the trace
            metadata: Additional metadata

        Returns:
            The trace ID
        """
        if not self.langfuse:
            return trace_id

        try:
            trace = self.langfuse.trace(
                id=trace_id,
                name=name,
                metadata=metadata or {}
            )
            self.trace = trace
            return trace_id
        except Exception as e:
            print(f"Warning: Failed to start trace: {e}")
            return trace_id

    def start_span(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """Start a new span.

        Args:
            name: Name of the span
            metadata: Additional metadata for the span

        Returns:
            str: The span ID
        """
        if not self.langfuse or not self.trace:
            return None

        try:
            self.current_span = self.trace.span(
                CreateSpan(
                    name=name,
                    metadata=metadata or {},
                    start_time=datetime.now(timezone.utc),
                )
            )
            return self.current_span.id
        except Exception as e:
            print(f"Warning: Failed to start Langfuse span: {e}")
            return None

    def end_span(self, output: Any = None, metadata: Optional[Dict[str, Any]] = None):
        """End the current span.

        Args:
            output: Output of the span (will be converted to string if not already)
            metadata: Additional metadata to add to the span
        """
        if not self.langfuse or not self.current_span:
            return

        try:
            # Convert output to string if it's a dictionary or list
            if output is not None and not isinstance(output, str):
                try:
                    output = json.dumps(output, ensure_ascii=False)
                except (TypeError, ValueError):
                    output = str(output)

            self.current_span.end(
                output=output,
                metadata=metadata or {},
                end_time=datetime.now(timezone.utc),
            )
            self.current_span = None
        except Exception as e:
            print(f"Warning: Failed to end Langfuse span: {e}")

    def log_generation(
        self,
        model: str,
        input: Union[Dict[str, Any], str, List[Dict[str, Any]]],
        output: Union[Dict[str, Any], str],
        name: str = "llm-generation",
        metadata: Optional[Dict[str, Any]] = None,
        usage: Optional[Dict[str, int]] = None
    ) -> Optional[str]:
        """Log an LLM generation.

        Args:
            model: Name of the model used
            input: Input to the model
            output: Output from the model
            name: Name for this generation
            metadata: Additional metadata
            usage: Token usage information with keys: 'prompt_tokens', 'completion_tokens', 'total_tokens'

        Returns:
            The generation ID if successful, None otherwise
        """
        if not self.langfuse or not self.trace:
            return None

        try:
            # Convert input to string if it's a dictionary or list
            if isinstance(input, (dict, list)):
                input_str = json.dumps(input, ensure_ascii=False, default=str)
            else:
                input_str = str(input)

            # Convert output to string if it's a dictionary
            if isinstance(output, dict):
                output_str = json.dumps(output, ensure_ascii=False, default=str)
            else:
                output_str = str(output)

            # Prepare generation data
            generation_data = {
                'name': name,
                'model': model,
                'input': input_str,
                'output': output_str,
                'metadata': metadata or {}
            }

            # Add usage data if provided
            if usage:
                generation_data['usage'] = usage

            # Create the generation
            generation = self.trace.generation(**generation_data)

            # Return the generation ID if available
            if hasattr(generation, 'id'):
                return str(generation.id)
            return None
        except Exception as e:
            print(f"Warning: Failed to log generation: {e}")
            return None

    def log_event(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Log an event.

        Args:
            name: Name of the event
            metadata: Additional metadata for the event

        Returns:
            True if successful, False otherwise
        """
        if not self.langfuse or not self.trace:
            return False

        try:
            event = self.trace.event(
                name=name,
                metadata=metadata or {}
            )
            return True if event else False
        except Exception as e:
            print(f"Warning: Failed to log event: {e}")
            return False

    def log_score(
        self,
        name: str,
        value: float,
        comment: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log a score.

        Args:
            name: Name of the score
            value: Numeric value of the score (0-1)
            comment: Optional comment about the score
            metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        if not self.langfuse or not self.trace:
            return False

        try:
            # Ensure score is between 0 and 1
            score_value = max(0.0, min(1.0, float(value)))

            # Prepare score data
            score_data = {
                'name': name,
                'value': score_value,
                'metadata': metadata or {}
            }

            # Add comment if provided
            if comment is not None:
                score_data['comment'] = comment

            # Log the score
            score = self.trace.score(**score_data)
            return True if score else False

        except (ValueError, TypeError) as e:
            print(f"Warning: Invalid score value: {value}. Must be a number between 0 and 1")
            return False
        except Exception as e:
            print(f"Warning: Failed to log score: {e}")
            return False

    def flush(self):
        """Flush any pending events to Langfuse."""
        if not self.langfuse:
            return

        try:
            self.langfuse.flush()
        except Exception as e:
            print(f"Warning: Failed to flush Langfuse events: {e}")
            return False
        return True

# Global instance of the Langfuse tracer
langfuse_tracer = LangfuseTracer()

def get_langfuse_tracer() -> LangfuseTracer:
    """Get the global Langfuse tracer instance."""
    return langfuse_tracer

def init_langfuse(public_key: Optional[str] = None, secret_key: Optional[str] = None, host: str = "https://cloud.langfuse.com"):
    """Initialize the global Langfuse tracer.

    Args:
        public_key: Langfuse public key
        secret_key: Langfuse secret key
        host: Langfuse host URL
    """
    global langfuse_tracer
    langfuse_tracer = LangfuseTracer(public_key, secret_key, host)
    return langfuse_tracer

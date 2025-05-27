"""Decorators for Langfuse integration."""

import functools
import inspect
import time
import json
import traceback
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from langfuse_integration import get_langfuse_tracer

F = TypeVar('F', bound=Callable[..., Any])

def track_tool(name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Callable[[F], F]:
    """Decorator to track tool usage with Langfuse.

    This decorator will automatically track:
    - Tool execution time
    - Input parameters
    - Output results
    - Any exceptions that occur

    Args:
        name: Custom name for the tool. If not provided, the function name will be used.
        metadata: Additional metadata to include with the tool call.

    Returns:
        The decorated function.
    """
    def decorator(func: F) -> F:
        nonlocal name
        name = name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_langfuse_tracer()
            start_time = time.time()

            # Get the context parameter if it exists
            context = None
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            if 'context' in bound_args.arguments:
                context = bound_args.arguments['context']

            # Get parameter names and values
            params = {}
            for param_name, param_value in bound_args.arguments.items():
                # Skip context parameter as it contains sensitive info
                if param_name == 'context':
                    continue
                # Convert values to string representation, handling large objects
                try:
                    if param_value is None:
                        param_str = "null"
                    elif isinstance(param_value, (str, int, float, bool)):
                        param_str = str(param_value)
                    else:
                        param_str = json.dumps(param_value, default=str, ensure_ascii=False)

                    # Truncate very long strings
                    if len(param_str) > 1000:
                        param_str = param_str[:500] + f"... [truncated {len(param_str) - 500} more characters]"
                    params[param_name] = param_str
                except Exception as e:
                    params[param_name] = f"<unserializable: {str(e)}>"

            # Start a span for this tool call
            span_id = None
            if tracer and hasattr(tracer, 'trace') and tracer.trace:
                try:
                    span_metadata = {
                        "function": func.__name__,
                        "module": func.__module__,
                        **(metadata or {})
                    }

                    # Add params to metadata if not too large
                    try:
                        params_str = json.dumps(params, ensure_ascii=False)
                        if len(params_str) <= 1000:  # Keep params in metadata if not too large
                            span_metadata["params"] = params
                    except Exception:
                        pass

                    span_id = tracer.start_span(
                        name=name,
                        metadata=span_metadata
                    )
                except Exception as e:
                    print(f"Warning: Failed to start Langfuse span: {e}")

            result = None
            error = None
            error_type = None
            stack_trace = None

            try:
                # Call the original function
                if inspect.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = str(e)
                error_type = type(e).__name__
                stack_trace = traceback.format_exc()
                raise
            finally:
                # End the span and log the result or error
                if tracer and hasattr(tracer, 'trace') and tracer.trace and span_id:
                    try:
                        end_time = time.time()
                        duration = end_time - start_time

                        if error is not None:
                            tracer.end_span(
                                span_id=span_id,
                                status="ERROR",
                                metadata={
                                    "error": error,
                                    "error_type": error_type,
                                    "stack_trace": stack_trace,
                                    "duration": duration
                                }
                            )
                        else:
                            # Truncate large results
                            result_str = str(result)
                            if len(result_str) > 1000:
                                result_str = result_str[:500] + f"... [truncated {len(result_str) - 500} more characters]"

                            tracer.end_span(
                                span_id=span_id,
                                status="SUCCESS",
                                metadata={
                                    "result": result_str,
                                    "duration": duration
                                }
                            )
                    except Exception as e:
                        print(f"Warning: Failed to end Langfuse span: {e}")

        # Return the appropriate wrapper based on whether the function is async or not
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            # For sync functions, we need to run them directly
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                # In this case, we're already in an async context, so we can't use asyncio.run()
                # Instead, we'll run the function synchronously
                tracer = get_langfuse_tracer()
                start_time = time.time()

                # Get the context parameter if it exists
                context = None
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                if 'context' in bound_args.arguments:
                    context = bound_args.arguments['context']

                # Get parameter names and values
                params = {}
                for param_name, param_value in bound_args.arguments.items():
                    # Skip context parameter as it contains sensitive info
                    if param_name == 'context':
                        continue
                    # Convert values to string representation, handling large objects
                    try:
                        if param_value is None:
                            param_str = "null"
                        elif isinstance(param_value, (str, int, float, bool)):
                            param_str = str(param_value)
                        else:
                            param_str = json.dumps(param_value, default=str, ensure_ascii=False)

                        # Truncate very long strings
                        if len(param_str) > 1000:
                            param_str = param_str[:500] + f"... [truncated {len(param_str) - 500} more characters]"
                        params[param_name] = param_str
                    except Exception as e:
                        params[param_name] = f"<unserializable: {str(e)}>"

                # Start a span for this tool call if tracer is available
                span_id = None
                if tracer and hasattr(tracer, 'trace') and tracer.trace:
                    try:
                        span_metadata = {
                            "function": func.__name__,
                            "module": func.__module__,
                            **(metadata or {})
                        }

                        # Add params to metadata if not too large
                        try:
                            params_str = json.dumps(params, ensure_ascii=False)
                            if len(params_str) <= 1000:  # Keep params in metadata if not too large
                                span_metadata["params"] = params
                        except Exception:
                            pass

                        span_id = tracer.start_span(
                            name=name,
                            metadata=span_metadata
                        )
                    except Exception as e:
                        print(f"Warning: Failed to start Langfuse span: {e}")

                result = None
                error = None
                error_type = None
                stack_trace = None

                try:
                    # Call the original function synchronously
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    error = str(e)
                    error_type = type(e).__name__
                    stack_trace = traceback.format_exc()
                    raise
                finally:
                    # End the span and log the result or error
                    if tracer and hasattr(tracer, 'trace') and tracer.trace and span_id:
                        try:
                            end_time = time.time()
                            duration = end_time - start_time

                            if error is not None:
                                tracer.end_span(
                                    span_id=span_id,
                                    status="ERROR",
                                    metadata={
                                        "error": error,
                                        "error_type": error_type,
                                        "stack_trace": stack_trace,
                                        "duration": duration
                                    }
                                )
                            else:
                                # Truncate large results
                                result_str = str(result)
                                if len(result_str) > 1000:
                                    result_str = result_str[:500] + f"... [truncated {len(result_str) - 500} more characters]"

                                tracer.end_span(
                                    span_id=span_id,
                                    status="SUCCESS",
                                    metadata={
                                        "result": result_str,
                                        "duration": duration
                                    }
                                )
                        except Exception as e:
                            print(f"Warning: Failed to end Langfuse span: {e}")
            
            return sync_wrapper

    return decorator

def track_llm(
    name: str,
    model: str,
    input_mapping: Optional[Callable[..., Dict[str, Any]]] = None,
    output_mapping: Optional[Callable[..., Dict[str, Any]]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Callable[[F], F]:
    """Decorator to track LLM calls with Langfuse.

    This decorator is specifically designed for LLM calls and provides
    more detailed tracking than the general-purpose tool decorator.

    Args:
        name: Name of the LLM call (e.g., 'generate_code_review')
        model: Name of the model being used (e.g., 'gpt-4')
        input_mapping: Optional function to transform input parameters
        output_mapping: Optional function to transform output
        metadata: Additional metadata to include with the LLM call

    Returns:
        The decorated function.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_langfuse_tracer()
            start_time = time.time()
            trace_id = None
            generation_id = None

            # Prepare input data
            input_data = {}
            if input_mapping:
                try:
                    input_data = input_mapping(*args, **kwargs)
                except Exception as e:
                    print(f"Warning: Failed to map LLM input: {e}")

            # Start a trace for this LLM call if not already in one
            if tracer and tracer.trace:
                try:
                    # Create a trace if one doesn't exist
                    if not tracer.trace:
                        trace_id = f"llm_trace_{int(time.time())}"
                        tracer.start_trace(
                            trace_id=trace_id,
                            name=f"LLM: {name}",
                            metadata={
                                "type": "llm_call",
                                "model": model,
                                **(metadata or {})
                            }
                        )

                    # Create a generation span
                    generation_metadata = {
                        "model": model,
                        "start_time": time.time(),
                        **(metadata or {})
                    }

                    # Add input data to metadata if it's not too large
                    try:
                        input_str = json.dumps(input_data, ensure_ascii=False, default=str)
                        if len(input_str) <= 2000:  # Keep input in metadata if not too large
                            generation_metadata["input"] = input_data
                    except Exception as e:
                        generation_metadata["input_error"] = f"Failed to serialize input: {str(e)}"

                    # Start a span for the generation
                    generation_id = tracer.start_span(
                        name=f"llm:{name}",
                        metadata=generation_metadata
                    )
                except Exception as e:
                    print(f"Warning: Failed to start LLM trace/span: {e}")

            result = None
            error = None
            error_type = None
            stack_trace = None
            usage_data = {}

            try:
                # Call the original function
                result = await func(*args, **kwargs)

                # Extract usage data if available (common pattern with LLM responses)
                if hasattr(result, 'usage') and isinstance(result.usage, dict):
                    usage_data = {
                        'input_tokens': result.usage.get('prompt_tokens', 0),
                        'output_tokens': result.usage.get('completion_tokens', 0),
                        'total_tokens': result.usage.get('total_tokens', 0)
                    }
                elif hasattr(result, 'usage') and hasattr(result.usage, 'model_dump'):
                    # Handle Pydantic models
                    usage_dict = result.usage.model_dump()
                    usage_data = {
                        'input_tokens': usage_dict.get('prompt_tokens', 0),
                        'output_tokens': usage_dict.get('completion_tokens', 0),
                        'total_tokens': usage_dict.get('total_tokens', 0)
                    }

                return result

            except Exception as e:
                error = str(e)
                error_type = type(e).__name__
                stack_trace = traceback.format_exc()
                raise

            finally:
                # Log the completion
                if tracer and tracer.trace and generation_id:
                    try:
                        end_time = time.time()
                        duration = end_time - start_time

                        # Prepare output data
                        output_data = {
                            "duration_seconds": duration,
                            "success": error is None
                        }

                        # Add result or error to output
                        if error:
                            output_data["error"] = error
                            if error_type:
                                output_data["error_type"] = error_type
                            if stack_trace:
                                output_data["stack_trace"] = stack_trace
                        elif result is not None:
                            try:
                                # Apply output mapping if provided
                                if output_mapping:
                                    try:
                                        mapped_output = output_mapping(result, *args, **kwargs)
                                        output_data["result"] = mapped_output
                                    except Exception as e:
                                        output_data["result"] = f"<output_mapping_error: {str(e)}>"
                                else:
                                    # Try to extract a reasonable string representation
                                    if hasattr(result, 'model_dump_json'):
                                        output_data["result"] = result.model_dump_json()
                                    elif hasattr(result, 'model_dump'):
                                        output_data["result"] = json.dumps(result.model_dump(), default=str)
                                    elif isinstance(result, (str, int, float, bool)) or result is None:
                                        output_data["result"] = str(result)
                                    else:
                                        output_data["result"] = json.dumps(result, default=str, ensure_ascii=False)

                                    # Truncate if too large
                                    if len(output_data["result"]) > 4000:
                                        output_data["result"] = output_data["result"][:2000] + f"... [truncated {len(output_data['result']) - 2000} more characters]"

                            except Exception as e:
                                output_data["result"] = f"<unserializable: {str(e)}>"

                        # Include usage data if available
                        if usage_data:
                            output_data["usage"] = usage_data

                        # End the generation span
                        tracer.end_span(
                            output=output_data,
                            metadata={
                                "duration_seconds": duration,
                                "usage": usage_data or None,
                                **(metadata or {})
                            }
                        )

                        # If we created a trace, end it
                        if trace_id:
                            tracer.trace = None

                    except Exception as e:
                        print(f"Warning: Failed to log LLM generation end: {e}")
                        if trace_id:
                            tracer.trace = None  # Clean up trace if it exists

        # Return the appropriate wrapper based on whether the function is async
        if inspect.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        return cast(F, async_wrapper)

    return decorator

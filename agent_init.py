"""Agent initialization and tool registration."""

import os
from typing import Any, Dict, List, Optional

from pydantic_ai import Agent, RunContext

from agent_tools import (
    get_pr_diff,
    post_review_comment,
    get_review_instructions,
    search_best_practices,
    detect_languages,
    aggregate_review_comments,
    PRDiffResponse,
    FileDiff,
    ReviewComment,
)
from agent_prompts import SYSTEM_PROMPT
from langfuse_integration import init_langfuse, get_langfuse_tracer
from models.deps import ReviewDeps

# Initialize Langfuse tracer
langfuse_tracer = init_langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)

def create_agent(llm_model: str = "openai:gpt-4.1", deps: Any = None) -> Agent:
    """Create and configure the agent with all tools.

    Args:
        llm_model: The LLM model to use
        deps: Dependencies to pass to the tools

    Returns:
        Configured Agent instance with all tools registered
    """

    # Define tool wrapper functions first
    async def get_pr_diff_wrapper(
        context: RunContext,
        repository: str,
        pr_id: int,
        max_files: int = 100,
        max_chunk_size: int = 10000,
        **kwargs: Any
    ) -> PRDiffResponse:
        return await get_pr_diff(
            context=context,
            repository=repository,
            pr_id=pr_id,
            max_files=max_files,
            max_chunk_size=max_chunk_size,
            deps=deps,
            **kwargs
        )

    async def post_review_comment_wrapper(
        context: RunContext,
        repository: str,
        pr_id: int,
        comments: List[ReviewComment],
        **kwargs: Any
    ) -> Dict[str, Any]:
        return await post_review_comment(
            context=context,
            repository=repository,
            pr_id=pr_id,
            comments=comments,
            deps=deps,
            **kwargs
        )

    async def get_review_instructions_wrapper(
        context: RunContext,
        instructions_path: str,
        **kwargs: Any
    ) -> str:
        return await get_review_instructions(
            context=context,
            instructions_path=instructions_path,
            deps=deps,
            **kwargs
        )

    async def search_best_practices_wrapper(
        context: RunContext,
        language: str,
        framework: Optional[str] = None,
        **kwargs: Any
    ) -> Dict[str, str]:
        return await search_best_practices(
            context=context,
            language=language,
            framework=framework,
            deps=deps,
            **kwargs
        )

    async def detect_languages_wrapper(
        context: RunContext,
        files: List[FileDiff],
        **kwargs: Any
    ) -> List[str]:
        return await detect_languages(
            context=context,
            files=files,
            deps=deps,
            **kwargs
        )

    async def aggregate_review_comments_wrapper(
        context: RunContext,
        diff: PRDiffResponse,
        custom_instructions: str,
        best_practices: Dict[str, str],
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        return await aggregate_review_comments(
            context=context,
            diff=diff,
            custom_instructions=custom_instructions,
            best_practices=best_practices,
            deps=deps,
            **kwargs
        )

    # Create the agent with the system prompt and dependencies
    agent = Agent(
        model=llm_model,
        system_prompt=SYSTEM_PROMPT,
        deps=deps,
        deps_type=ReviewDeps,  # Use the actual ReviewDeps type
        tools=[
            get_pr_diff_wrapper,
            post_review_comment_wrapper,
            get_review_instructions_wrapper,
            search_best_practices_wrapper,
            detect_languages_wrapper,
            aggregate_review_comments_wrapper,
        ],
        tracer=langfuse_tracer,
    )

    # Start a new trace for this agent run
    if langfuse_tracer and langfuse_tracer.langfuse:
        langfuse_tracer.start_trace(
            trace_id=f"agent_run_{os.urandom(4).hex()}",
            name="code_review_agent_run",
            metadata={
                "llm_model": llm_model,
                "system_prompt": SYSTEM_PROMPT[:100] + "..." if len(SYSTEM_PROMPT) > 100 else SYSTEM_PROMPT,
            }
        )

    return agent

def flush_langfuse():
    """Flush any pending Langfuse events."""
    tracer = get_langfuse_tracer()
    if tracer:
        tracer.flush()

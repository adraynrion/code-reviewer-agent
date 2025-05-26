"""Agent initialization and tool registration."""

from pydantic_ai import Agent
from agent_tools import (
    get_pr_diff,
    post_review_comment,
    get_review_instructions,
    search_best_practices,
    detect_languages,
    aggregate_review_comments,
)
from agent_prompts import SYSTEM_PROMPT
from typing import Any

def create_agent(llm_model: str = "openai:gpt-4.1-mini") -> Agent:
    """Create and configure the agent with all tools.

    Args:
        llm_model: The LLM model to use

    Returns:
        Configured Agent instance with all tools registered
    """
    # Create the agent
    agent = Agent(
        llm_model,
        system_prompt=SYSTEM_PROMPT,
        deps_type=Any,  # We'll handle deps manually
        retries=2,
    )

    # Register all tools
    agent.tool()(get_pr_diff)
    agent.tool()(post_review_comment)
    agent.tool()(get_review_instructions)
    agent.tool()(search_best_practices)
    agent.tool()(detect_languages)
    agent.tool()(aggregate_review_comments)

    return agent

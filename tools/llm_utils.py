"""LLM-related utilities for the code review agent."""

import asyncio
import json
import logging
from typing import Dict, List, Any
from pydantic_ai import RunContext
from langfuse_decorators import track_llm, track_tool
from models import ReviewComment, PRDiffResponse
from models.deps import ReviewDeps
from .utils import (
    log_error,
)

# Configure logger
logger = logging.getLogger(__name__)

@track_llm(
    name="analyze_with_llm",
    model=lambda context: getattr(getattr(context, 'deps', None), 'llm_model', 'unknown'),
    metadata={"component": "llm_analysis"}
)
async def analyze_with_llm(
    context: RunContext[ReviewDeps],
    diff_content: str,
    custom_instructions: str,
    best_practices: str
) -> List[Dict[str, Any]]:
    """
    Analyze code diff with LLM to generate review comments.

    Args:
        context: The dependency injection container
        diff_content: The diff content to analyze
        custom_instructions: Custom instructions for the code review
        best_practices: Best practices to consider during review

    Returns:
        List of review comments
    """
    try:
        # Get dependencies from context
        deps = context.deps

        # Prepare the prompt for the LLM
        prompt = f"""Please review the following code changes and provide feedback.

        Custom Instructions:
        {custom_instructions}

        Best Practices:
        {best_practices}

        Code Diff:
        {diff_content}

        Please provide your review comments in the following JSON format:
        [
            {{
                "file_path": "path/to/file",
                "line_number": 123,
                "comment": "Your comment here",
                "comment_type": "suggestion|question|concern",
                "suggestion": "Optional suggested code"
            }}
        ]
        """

        # Call the LLM
        response = await deps.llm_client.generate(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.3,
        )

        # Parse the response
        try:
            comments = json.loads(response.choices[0].message.content)
            return comments
        except json.JSONDecodeError as e:
            log_error(f"Failed to parse LLM response: {response.choices[0].message.content}", exc_info=e)
            return []

    except Exception as e:
        log_error(f"Error analyzing with LLM: {str(e)}", exc_info=e)
        return []

@track_tool(name="aggregate_review_comments", metadata={"component": "review_aggregation"})
async def aggregate_review_comments(
    context: RunContext[ReviewDeps],
    diff: PRDiffResponse,
    custom_instructions: str,
    best_practices: Dict[str, str],
    deps: ReviewDeps = None,
    batch_size: int = 1,
    max_tokens_per_minute: int = 150000,
) -> List[ReviewComment]:
    """
    Aggregate review comments by processing files in batches.

    Args:
        context: The dependency injection container
        diff: The PR diff response
        custom_instructions: Custom instructions for the code review
        best_practices: Dictionary of best practices by language/framework
        deps: Optional dependencies (will be extracted from context if not provided)
        batch_size: Number of files to process in parallel
        max_tokens_per_minute: Maximum tokens per minute to respect rate limits

    Returns:
        List of review comments
    """
    try:
        # Use deps from context if not provided directly
        if deps is None and hasattr(context, 'deps'):
            deps = context.deps

        if deps is None:
            raise ValueError("No dependencies provided. Please ensure the agent is initialized with the correct dependencies.")

        all_comments = []

        # Process files in batches
        for i in range(0, len(diff.files), batch_size):
            batch = diff.files[i:i + batch_size]

            # Process each file in the batch
            tasks = []
            for file in batch:
                if not file.get('patch'):
                    continue

                # Get best practices for this file's language
                file_best_practices = best_practices.get('general', '')
                if hasattr(file, 'language') and file.language in best_practices:
                    file_best_practices += "\n\n" + best_practices[file.language]

                # Create task for this file
                task = analyze_with_llm(
                    context,
                    file['patch'],
                    custom_instructions,
                    file_best_practices
                )
                tasks.append(task)

                # Respect rate limits
                await asyncio.sleep(0.5)

            # Wait for all tasks in the batch to complete
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for file, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    log_error(f"Error processing file {file.get('filename', 'unknown')}: {str(result)}")
                    continue

                for comment_data in result:
                    try:
                        comment = ReviewComment(
                            file_path=comment_data['file_path'],
                            line_number=comment_data['line_number'],
                            comment=comment_data['comment'],
                            comment_type=comment_data.get('comment_type', 'suggestion'),
                            suggestion=comment_data.get('suggestion')
                        )
                        all_comments.append(comment)
                    except (KeyError, TypeError) as e:
                        log_error(f"Invalid comment format: {comment_data}", exc_info=e)

        return all_comments

    except Exception as e:
        log_error(f"Error aggregating review comments: {str(e)}", exc_info=e)
        raise

"""Code review service for the code review agent."""

import argparse
import asyncio
import sys
import time
from typing import Any, Dict, List, Optional

from code_reviewer_agent.config.config import config
from code_reviewer_agent.models.agent import CodeReviewResponse, get_code_review_agent
from code_reviewer_agent.prompts.cr_agent import USER_PROMPT
from code_reviewer_agent.services.github import (
    get_request_files as get_github_request_files,
)
from code_reviewer_agent.services.github import post_github_review, update_github_pr
from code_reviewer_agent.services.gitlab import (
    get_request_files as get_gitlab_request_files,
)
from code_reviewer_agent.services.gitlab import post_gitlab_review, update_gitlab_mr
from code_reviewer_agent.utils.langfuse import configure_langfuse
from code_reviewer_agent.utils.rich_utils import (
    console,
    print_debug,
    print_diff,
    print_error,
    print_exception,
    print_header,
    print_info,
    print_section,
    print_success,
    print_warning,
)

# Configure Langfuse for agent observability
tracer = configure_langfuse()


def parse_arguments() -> argparse.Namespace:
    """Parse and validate command line arguments.

    Returns:
        Parsed command line arguments

    """
    print_section("Parsing Command Line Arguments", "🔧")

    # Create the argument parser with rich help formatting
    parser = argparse.ArgumentParser(
        description="[bold]Code Review Agent[/bold] - Automated code review tool for GitHub and GitLab",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "[bold]Examples:[/bold]\n"
            "  python -m code_reviewer_agent --platform github --repository owner/repo --pr-id 123\n"
            "  python -m code_reviewer_agent --platform gitlab --repository 12345 --pr-id 42 --instructions-path ./docs"
        ),
    )

    # Platform argument
    parser.add_argument(
        "--platform",
        type=str,
        choices=["github", "gitlab"],
        help="Version control platform (overrides PLATFORM env var)",
        metavar="PLATFORM",
    )

    # Repository argument
    parser.add_argument(
        "--repository",
        type=str,
        help=(
            "Repository identifier. For GitHub: 'owner/repo' format. "
            "For GitLab: project ID (overrides REPOSITORY env var)"
        ),
        metavar="REPO",
    )

    # PR/MR ID argument
    parser.add_argument(
        "--id",
        "--pr-id",
        "--mr-id",
        type=int,
        help="Pull request or merge request ID (overrides PR_ID env var)",
        metavar="ID",
    )

    # Instructions path argument
    parser.add_argument(
        "--instructions-path",
        type=str,
        help=(
            "Path to the local directory containing your custom instructions "
            "for the code review (overrides LOCAL_FILE_DIR env var)"
        ),
        metavar="PATH",
    )

    # Parse arguments
    try:
        args = parser.parse_args()
        print_success("Command line arguments parsed successfully")
        return args

    except Exception as e:
        print_error(f"Error parsing command line arguments: {str(e)}")
        parser.print_help()
        print_exception()
        sys.exit(1)


async def main() -> None:
    """Main entry point for the code review agent."""
    console.clear()
    print_header("Starting Code Reviewer Agent process")

    if config.logging.debug:
        config.print_config()

    args = parse_arguments()
    platform: str = args.platform or config.reviewer.platform
    repository: str = args.repository or config.reviewer.repository
    instructions_path: str = (
        args.instructions_path or config.reviewer.instruction_dir_path
    )
    request_id: int = args.id
    reviewed_label: str = "ReviewedByAI"

    if config.logging.debug:
        print_section("Final Configuration retrieved:", "⚙️")
        print_info(f"Platform: {platform.upper()}")
        print_info(f"Repository: {repository}")
        print_info(f"Instructions path: {instructions_path}")
        print_info(f"Request ID: {request_id}")

    try:
        # Validate inputs
        if platform not in ("github", "gitlab"):
            raise ValueError("Invalid platform. Must be either 'github' or 'gitlab'.")

        if platform == "github" and not config.reviewer.github_token:
            raise ValueError(
                "github_token config variable is required when platform is 'github'."
            )

        if platform == "gitlab" and not config.reviewer.gitlab_token:
            raise ValueError(
                "gitlab_token config variable is required when platform is 'gitlab'."
            )

        if not repository:
            raise ValueError(
                "Repository not specified. Use --repository argument or set repository config variable."
            )

        if not request_id:
            raise ValueError(
                "Request ID not specified. Use --id, --pr-id or --mr-id argument."
            )
    except ValueError as e:
        print_error(f"Error validating inputs: {str(e)}")
        print_exception()
        sys.exit(1)

    # Fetch request files
    print_section("Fetching PR/MR Information", "🌐")
    files_diff: List[Dict[str, Any]] = []
    try:
        if platform == "github":
            files_diff = get_github_request_files(repository, request_id)
        else:
            files_diff = get_gitlab_request_files(repository, request_id)
    except Exception as e:
        print_error(f"Error fetching PR/MR information: {str(e)}")
        print_exception()
        sys.exit(1)

    # ========== Reviewer Agent: loop on each file diff ==========
    print_section("Starting Code Review process", "🤖")
    print_debug(f"Reviewing {len(files_diff)} file(s) with changes")

    reviewer_agent = get_code_review_agent()
    try:
        with tracer.start_as_current_span("CR-Agent-Main-Trace") as main_span:
            main_span.set_attribute("langfuse.user.id", f"cr-request-{request_id}")
            main_span.set_attribute(
                "langfuse.session.id", f"cr-{platform}-{repository}"
            )

            files_reviewed = 0
            for diff in files_diff:
                try:
                    filename = diff.get("filename", "unknown")
                    languages = ", ".join(diff.get("languages", ["unknown"]))
                    patch = diff.get("patch", "")

                    if not patch:
                        print_warning(f"No changes found for file: {filename}")
                        continue

                    if config.logging.debug:
                        print_info(f"Reviewing file: {filename}")
                        print_info(f"  - Languages: {languages}")
                        print_diff(patch)

                    # Prepare the User input for the code review
                    user_input = USER_PROMPT.format(
                        diff=patch,
                    )
                    print_debug(f"User input length: {len(user_input)}")

                    # Start a new tracing for this file review
                    print_info(f"Starting code review for file: {filename}")
                    with tracer.start_as_current_span(
                        "CR-Agent-Review"
                    ) as file_review_span:
                        file_review_span.set_attribute(
                            "langfuse.user.id", f"cr-request-{request_id}"
                        )
                        file_review_span.set_attribute(
                            "langfuse.session.id", f"cr-{platform}-{repository}"
                        )
                        file_review_span.set_attribute("filename", filename)
                        file_review_span.set_attribute("languages", languages)

                        # Run the code review AI Agent
                        start_time = time.perf_counter()
                        reviewer_output: Optional[CodeReviewResponse] = None

                        try:
                            reviewer_response = await reviewer_agent.run(
                                user_input,
                                output_type=CodeReviewResponse,
                            )
                            reviewer_output = reviewer_response.output

                            if not reviewer_output or not hasattr(
                                reviewer_output, "comment"
                            ):
                                raise ValueError(
                                    "The AI did not return a valid code review response!"
                                )

                        except ValueError as e:
                            # Re-raise validation errors as-is
                            raise
                        except Exception as agent_error:
                            print_error(f"Agent run failed: {str(agent_error)}")
                            raise

                        duration = time.perf_counter() - start_time
                        print_debug(f"Code review completed in {duration:.2f} seconds")
                        print_success(
                            f"Code review response successfully retrieved from Agent"
                        )

                        if config.logging.debug:
                            reviewer_output.print_info()

                        # Set langfuse span attributes
                        file_review_span.set_attribute("input.value", user_input)
                        file_review_span.set_attribute("output.value", reviewer_output)

                        # Post review comments to the PR/MR
                        try:
                            if platform == "github":
                                await post_github_review(
                                    repository,
                                    request_id,
                                    diff,
                                    reviewer_output,
                                )
                            else:
                                await post_gitlab_review(
                                    repository,
                                    request_id,
                                    diff,
                                    reviewer_output,
                                )
                            print_success("Review posted successfully")

                        except Exception as post_error:
                            print_error(f"Failed to post review: {str(post_error)}")
                            print_exception()
                            raise

                        files_reviewed += 1

                except Exception as file_error:
                    print_warning(
                        f"Skipping review of file {filename} due to error: {str(file_error)}"
                    )
                    print_exception()
                    continue  # Continue with the next file even if one fails

            print_success(
                f"{files_reviewed}/{len(files_diff)} reviews done and posted successfully!"
            )

            # Add label and assign reviewer after processing all files
            print_section("Finalizing Review by updating PR/MR", "🔄")
            if platform == "github":
                await update_github_pr(repository, request_id, reviewed_label)
            else:
                await update_gitlab_mr(repository, request_id, reviewed_label)
            print_success("Reviewer and label updated successfully")

    except Exception as e:
        print_error(f"An unexpected error occurred: {str(e)}")
        print_exception()
        sys.exit(1)

    print_section("Review Complete", "✅")
    print_success("Code review process finished successfully")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())

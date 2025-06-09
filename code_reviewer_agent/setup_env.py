#!/usr/bin/env python3
"""Interactive setup script for the code review agent.

This script helps users set up their environment by creating a .env file with the
required configuration.

"""

import os
import sys
from pathlib import Path

# Import rich utilities
from .utils import (
    confirm,
    console,
    print_error,
    print_exception,
    print_header,
    print_info,
    print_panel,
    print_section,
    print_success,
)


def get_input(
    prompt: str, default: str = "", is_required: bool = True, is_password: bool = False
) -> str:
    """Helper function to get user input with a default value and optional password
    masking.

    Args:
        prompt: The prompt to display to the user
        default: Default value if user enters nothing
        is_required: Whether the field is required
        is_password: Whether to mask input (for passwords)

    Returns:
        The user's input or default value

    """
    while True:
        # Format the prompt with default value if provided
        if default:
            prompt_text = f"[bold]{prompt}[/bold] [[dim]{default}[/]]: "
        else:
            prompt_text = f"[bold]{prompt}:[/] "

        try:
            if is_password:
                import getpass

                # For password fields, we need to use getpass which doesn't support rich
                console.print(prompt_text, end="(hidden entry)", style="bold")
                value = getpass.getpass("")
            else:
                value = console.input(prompt_text)

            value = value.strip()

            # Return default if no input provided and default exists
            if not value and default:
                return default

            # Validate required fields
            if not value and is_required:
                print_error("This field is required. Please enter a value.")
                continue

            return value

        except (KeyboardInterrupt, EOFError):
            console.print("\nOperation cancelled by user.")
            sys.exit(1)
        except Exception as e:
            print_error(f"An error occurred: {str(e)}")
            if not confirm("Continue?"):
                sys.exit(1)


def setup_environment() -> None:
    """Set up the environment by creating a .env file with user input."""
    env_file = Path(".env")

    if env_file.exists():
        if not confirm("A .env file already exists. Do you want to overwrite it?"):
            print_info("Setup cancelled.")
            return

    console.clear()
    print_header("Code Reviewer Agent - Environment Setup")
    print_info("Setting up your environment...\n")

    # Required Configuration Section
    print_section("Required Configuration")
    print_info("Configure the essential settings for the code reviewer agent.")

    # LLM Provider Configuration
    print_section("LLM Provider Configuration", "🤖")
    print_info("Configure your preferred LLM provider and model.")

    provider = get_input(
        "LLM Provider (OpenAI/TogetherAI/OpenRouter/Google/Ollama)", default="OpenAI"
    )

    model_choice = get_input(
        "Model choice (e.g., gpt-4.1-mini, anthropic/claude-3.7-sonnet, gemini-2.0-flash, mistrall-small3.1)",
        default="gpt-4.1-mini",
    )

    base_url = get_input(
        "Base URL for the API (leave empty for default)",
        default={
            "OpenAI": "https://api.openai.com/v1",
            "TogetherAI": "https://api.together.xyz/v1",
            "OpenRouter": "https://openrouter.ai/api/v1",
            "Ollama": "http://localhost:11434/v1",
        }.get(provider, ""),
        is_required=False,
    )

    llm_api_key = get_input(f"API Key for {provider}", is_password=True)
    openai_api_key = get_input(
        "OpenAI API Key (required for some features)", is_password=True
    )

    # Supabase Configuration
    print_section("Supabase Configuration", "📊")
    print_info("Configure your Supabase backend for document storage.")

    supabase_url = get_input("Supabase project URL", is_required=True)
    supabase_service_key = get_input(
        "Supabase Service Key (for admin operations)",
        is_required=True,
        is_password=True,
    )

    # Optional Configuration Section
    print_section("Optional Configuration", "⚙️")
    print_info("Customize additional settings (press Enter to use defaults).")

    # Embedding Model
    embedding_model = get_input(
        "Embedding Model", default="text-embedding-3-small", is_required=False
    )

    # Local File Storage
    local_file_dir = get_input(
        "Local instructions storage directory",
        default=os.path.join(os.path.dirname(__file__), "instructions"),
        is_required=False,
    )

    # Logging
    log_level = get_input(
        "Log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)",
        default="INFO",
        is_required=False,
    )

    debug = get_input(
        "Enable debug mode (true/false)", default="false", is_required=False
    )

    # Git Provider Configuration
    print_section("Git Provider Configuration", "🔌")
    print_info("Configure your Git provider for code reviews.")

    platform = get_input("Platform (github/gitlab)", default="github")

    repository = get_input(
        "Repository (format: 'owner/repo' for GitHub or 'project_id' for GitLab)",
        is_required=True,
    )

    github_token = (
        get_input(
            "GitHub Personal Access Token (with 'repo' scope)",
            is_required=True if platform == "github" else False,
            is_password=True,
        )
        if platform == "github"
        else ""
    )

    gitlab_token = (
        get_input(
            "GitLab Personal Access Token (with 'api' scope)",
            is_required=True if platform == "gitlab" else False,
            is_password=True,
        )
        if platform == "gitlab"
        else ""
    )

    gitlab_api_url = (
        get_input(
            "GitLab API URL (optional, for self-hosted instances)",
            default="https://gitlab.com/api/v4",
            is_required=False,
        )
        if platform == "gitlab"
        else ""
    )

    # Langfuse Configuration
    print_section("Langfuse Configuration (Optional)", "📈")
    print_info("Configure Langfuse for analytics (press Enter to skip).")

    langfuse_public_key = get_input(
        "Langfuse Public Key (optional)", default="", is_required=False
    )

    langfuse_secret_key = ""
    if langfuse_public_key:
        langfuse_secret_key = get_input(
            "Langfuse Secret Key", default="", is_required=False, is_password=True
        )

    langfuse_host = ""
    if langfuse_public_key and langfuse_secret_key:
        langfuse_host = get_input(
            "Langfuse Host", default="https://cloud.langfuse.com", is_required=False
        )

    # Create the .env content with proper formatting
    env_content = """# ===================================
# Required Configuration
# ===================================

# LLM Provider Configuration
PROVIDER={provider}
MODEL_CHOICE={model_choice}
BASE_URL={base_url}
LLM_API_KEY={llm_api_key}
OPENAI_API_KEY={openai_api_key}

# Supabase Configuration
SUPABASE_URL={supabase_url}
SUPABASE_SERVICE_KEY={supabase_service_key}

# Embedding Model
EMBEDDING_MODEL={embedding_model}

# Local File Storage
LOCAL_FILE_DIR={local_file_dir}

# Logging
LOG_LEVEL={log_level}
DEBUG={debug}

# Git Provider Configuration
PLATFORM={platform}
REPOSITORY={repository}
GITHUB_TOKEN={github_token}
GITLAB_TOKEN={gitlab_token}
GITLAB_API_URL={gitlab_api_url}

# Langfuse Configuration (Optional)
LANGFUSE_PUBLIC_KEY={langfuse_public_key}
LANGFUSE_SECRET_KEY={langfuse_secret_key}
LANGFUSE_HOST={langfuse_host}
"""

    # Write the .env file
    try:
        with open(env_file, "w") as f:
            env_content = env_content.format(
                provider=provider,
                model_choice=model_choice,
                base_url=base_url,
                llm_api_key=llm_api_key,
                openai_api_key=openai_api_key,
                supabase_url=supabase_url,
                supabase_service_key=supabase_service_key,
                embedding_model=embedding_model,
                local_file_dir=local_file_dir,
                log_level=log_level,
                debug=debug,
                platform=platform,
                repository=repository,
                github_token=github_token,
                gitlab_token=gitlab_token,
                gitlab_api_url=gitlab_api_url,
                langfuse_public_key=langfuse_public_key,
                langfuse_secret_key=langfuse_secret_key,
                langfuse_host=langfuse_host,
            )
            f.write(env_content)

        # Display success message with file path and next steps
        print_success(f"Successfully created configuration file: {env_file.absolute()}")

        # Create a panel with next steps
        next_steps = """[bold]Next steps:[/bold]
1. Review the generated .env file
2. Run the code review agent with: [code]code-reviewer-agent[/]
3. For help, run: [code]code-reviewer-agent --help[/]"""

        print_panel(next_steps, title="✅ Setup Complete", border_style="green")

    except Exception as e:
        print_error(f"Failed to create {env_file}: {str(e)}")
        print_exception()
        sys.exit(1)


if __name__ == "__main__":
    setup_environment()

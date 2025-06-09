#!/usr/bin/env python3
"""Interactive setup script for the code review agent.

This script helps users set up their environment by creating a .env file with the
required configuration.

"""

import os
from pathlib import Path


def get_input(
    prompt: str, default: str = "", is_required: bool = True, is_password: bool = False
) -> str:
    """Helper function to get user input with a default value and optional password
    masking."""
    while True:
        if default:
            prompt_text = f"{prompt} [{default}]: "
        else:
            prompt_text = f"{prompt}: "

        if is_password:
            import getpass

            value = getpass.getpass(prompt_text)
        else:
            value = input(prompt_text).strip()

        if not value and default:
            return default
        elif not value and is_required:
            print("This field is required. Please enter a value.")
        else:
            return value


def setup_environment() -> None:
    """Set up the environment by creating a .env file with user input."""
    env_file = Path(".env")

    if env_file.exists():
        print(
            "A .env file already exists. Do you want to overwrite it? (y/N): ", end=""
        )
        if input().strip().lower() != "y":
            print("Setup cancelled.")
            return

    print("\n🛠️  Setting up your environment...\n")
    print("=== Required Configuration ===\n")

    # LLM Provider Configuration
    print("LLM Provider Configuration")
    print("-------------------------")
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
    print("\nSupabase Configuration")
    print("---------------------")
    supabase_url = get_input("Supabase project URL", is_required=True)

    supabase_service_key = get_input(
        "Supabase Service Key (for admin operations)",
        is_required=True,
        is_password=True,
    )

    # Optional Configuration
    print("\n=== Optional Configuration ===\n")

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
    print("\nGit Provider Configuration")
    print("------------------------")
    platform = get_input("Platform (github/gitlab)", default="github")

    repository = get_input(
        "Repository (format: 'owner/repo' for GitHub or 'project_id' for GitLab)",
        is_required=True,
    )

    github_token = get_input(
        "GitHub Personal Access Token (with 'repo' scope)",
        is_required=True if platform == "github" else False,
        is_password=True,
    )

    gitlab_token = get_input(
        "GitLab Personal Access Token (with 'api' scope)",
        is_required=True if platform == "gitlab" else False,
        is_password=True,
    )

    gitlab_api_url = get_input(
        "GitLab API URL (optional, for self-hosted instances)",
        default="https://gitlab.com/api/v4",
        is_required=False,
    )

    # Langfuse Configuration
    print("\nLangfuse Configuration (Optional)")
    print("------------------------------")
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

    # Create the .env content
    env_content = f"""# ===================================
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
SUPABASE_SERVICE_KEY={supabase_service_key if supabase_service_key else ''}

# ===================================
# Optional Configuration
# ===================================

# Embedding Model
EMBEDDING_MODEL_CHOICE={embedding_model}

# Local File Storage
LOCAL_FILE_DIR={local_file_dir}

# Logging
LOG_LEVEL={log_level}
DEBUG={debug}

# ===================================
# Git Provider Configuration
# ===================================
# GitHub Personal Access Token (with 'repo' scope)
GITHUB_TOKEN={github_token if github_token else ''}

# GitLab Configuration
GITLAB_TOKEN={gitlab_token if gitlab_token else ''}
GITLAB_API_URL={gitlab_api_url}

# ===================================
# Repository Configuration
# ===================================
PLATFORM={platform}
REPOSITORY={repository}

# ===================================
# Langfuse Configuration (Optional)
# ===================================
"""

    # Add Langfuse config only if keys are provided
    if langfuse_public_key and langfuse_secret_key:
        env_content += f"""LANGFUSE_PUBLIC_KEY={langfuse_public_key}
LANGFUSE_SECRET_KEY={langfuse_secret_key}
LANGFUSE_HOST={langfuse_host}
"""

    # Write the .env file
    with open(env_file, "w") as f:
        f.write(env_content)

    print(f"\n✅ Successfully created {env_file} with your configuration.")
    print("You can now run the code review agent with: code-reviewer-agent")


if __name__ == "__main__":
    setup_environment()

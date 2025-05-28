# AI Code Review Agent

An intelligent code review agent that analyzes pull requests on GitHub and GitLab, providing detailed feedback based on custom review instructions and language-specific best practices.

## Features

- **Multi-Platform Support**: Works with both GitHub and GitLab
- **Modular Architecture**: Built using Model Context Protocol (MCP) for extensibility
- **Specialized Agents**: Dedicated agents for different tasks (search, filesystem, Git, web crawling, code review)
- **Observability**: Built-in Langfuse integration for monitoring and analytics
- **Environment-based Configuration**: Simple setup with environment variables

## Prerequisites

- Python 3.8+
- Node.js 16+ and npm (for MCP servers)
- Git
- GitHub/GitLab account with appropriate permissions
- API keys for required services (see Configuration)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/adraynrion/code-reviewer-agent.git
   cd code-reviewer-agent
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. (Optional) Install MCP servers globally:
   ```bash
   npm install -g @modelcontextprotocol/server-brave-search \
                 @modelcontextprotocol/server-filesystem \
                 @modelcontextprotocol/server-github \
                 @modelcontextprotocol/server-gitlab
   ```

5. Copy the example environment file and update with your details:
   ```bash
   cp .env.example .env
   # Edit .env with your tokens and configuration
   ```

## Architecture

The agent is built with a modular architecture using the Model Context Protocol (MCP) with the following components:

- **Primary Agent**: Coordinates the review process and delegates to specialized agents
- **Brave Search Agent**: Performs web searches using Brave Search API
- **Filesystem Agent**: Interacts with the local filesystem
- **Repository Agent**: Handles Git repository operations (GitHub/GitLab)
- **Firecrawl Agent**: Web crawling and content extraction
- **Reviewer Agent**: Specialized in code review and analysis

## Configuration

Update the `.env` file with your configuration:

```
# Required: Platform (github or gitlab)
PLATFORM=github

# Required: Repository in format 'owner/repo' for GitHub or 'group/project' for GitLab
REPOSITORY=owner/repo

# GitHub Configuration
GITHUB_TOKEN=your_github_token_here

# GitLab Configuration (if using GitLab)
# GITLAB_TOKEN=your_gitlab_token_here
# GITLAB_API_URL=https://gitlab.com/api/v4  # For self-hosted GitLab

# LLM Configuration
LLM_API_KEY=your_openai_api_key_here
MODEL_CHOICE=gpt-4.1-mini  # or your preferred model
BASE_URL=https://api.openai.com/v1  # For OpenAI-compatible APIs

# Brave Search API Key (required for web search)
BRAVE_API_KEY=your_brave_api_key_here

# Firecrawl API Key (required for web crawling)
FIRECRAWL_API_KEY=your_firecrawl_api_key_here

# Langfuse Configuration (optional)
# LANGFUSE_PUBLIC_KEY=your_public_key_here
# LANGFUSE_SECRET_KEY=your_secret_key_here
# LANGFUSE_HOST=https://cloud.langfuse.com  # For self-hosted instances
```

## Usage

Run the agent with the required PR ID:

```bash
python agent.py --pr-id 123
```

### Command Line Arguments

| Argument | Description | Required | Default |
|----------|-------------|:--------:|:-------:|
| `--pr-id` | Pull/Merge Request ID | ✅ | - |
| `--repository` | Repository in format `owner/repo` | ❌ | Uses `REPOSITORY` env var |
| `--platform` | Version control platform: `github` or `gitlab` | ❌ | Uses `PLATFORM` env var or `github` |
| `--instructions-path` | Path to custom instructions folder | ❌ | `instructions` |

## Monitoring and Observability

The agent includes built-in integration with [Langfuse](https://langfuse.com) for comprehensive monitoring and observability. This integration provides:

- **End-to-End Tracing**: Full trace of each code review request
- **LLM Monitoring**: Detailed tracking of all LLM interactions
- **Tool Usage**: Performance metrics for all tool calls
- **Error Tracking**: Centralized error tracking with context

## License

MIT

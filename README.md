# AI Code Review Agent

An intelligent code review agent that analyzes pull requests on GitHub and GitLab, providing detailed feedback based on custom review instructions and language-specific best practices. Also includes a web crawler agent for documentation processing.

## Features

- **Multi-Platform Support**: Works with both GitHub and GitLab
- **Modular Architecture**: Built using Model Context Protocol (MCP) for extensibility
- **Specialized Agents**: Dedicated agents for different tasks (repository operations, filesystem, code review, documentation processing)
- **Vector Database Integration**: Stores and retrieves documentation using Supabase
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
- **Repository Agent**: Handles Git repository operations (GitHub/GitLab)
- **Filesystem Agent**: Interacts with the local filesystem
- **Reviewer Agent**: Specialized in code review and analysis
- **Crawler Agent**: Web crawler for processing documentation websites and storing in vector database

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
OPENAI_API_KEY=your_openai_api_key_here
MODEL_CHOICE=gpt-4.1-mini  # or your preferred model
BASE_URL=https://api.openai.com/v1  # For OpenAI-compatible APIs

# Crawler Configuration (for documentation processing)
SUPABASE_URL=your_supabase_url_here
SUPABASE_SERVICE_KEY=your_supabase_service_key_here

# Langfuse Configuration (optional)
# LANGFUSE_PUBLIC_KEY=your_public_key_here
# LANGFUSE_SECRET_KEY=your_secret_key_here
# LANGFUSE_HOST=https://cloud.langfuse.com  # For self-hosted instances
```

## Usage

### Code Review Agent

Run the code review agent with the required PR ID:

```bash
python code_review_agent.py --pr-id 123
```

#### Code Review Agent Command Line Arguments

| Argument | Description | Required | Default |
|----------|-------------|:--------:|:-------:|
| `--pr-id` | Pull/Merge Request ID | ✅ | - |
| `--repository` | Repository in format `owner/repo` | ❌ | Uses `REPOSITORY` env var |
| `--platform` | Version control platform: `github` or `gitlab` | ❌ | Uses `PLATFORM` env var or `github` |
| `--instructions-path` | Path to custom instructions folder | ❌ | `instructions` |

### Crawler Agent

The crawler agent processes documentation websites and stores the content in a vector database for later retrieval.

```bash
python crawler_agent.py --doc-url https://example.com/docs
```

#### Crawler Agent Command Line Arguments

| Argument | Description | Required | Default |
|----------|-------------|:--------:|:-------:|
| `--doc-url` | URL of the documentation to crawl | ✅ | - |
| `--mode` | Crawling mode: `single-page` or `full` | ❌ | `single-page` |

In `single-page` mode, only the specified URL will be crawled. In `full` mode, the crawler will follow all links from the starting page.

## Monitoring and Observability

The agent includes built-in integration with [Langfuse](https://langfuse.com) for comprehensive monitoring and observability. This integration provides:

- **End-to-End Tracing**: Full trace of each code review request
- **LLM Monitoring**: Detailed tracking of all LLM interactions
- **Tool Usage**: Performance metrics for all tool calls
- **Error Tracking**: Centralized error tracking with context

## License

MIT

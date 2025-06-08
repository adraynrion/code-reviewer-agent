# AI Code Review Agent

[![Python Version](https://img.shields.io/badge/python-3.11.9-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type Checker: mypy](https://img.shields.io/badge/type%20checker-mypy-blueviolet)](http://mypy-lang.org/)
[![Code style: flake8](https://img.shields.io/badge/code%20style-flake8-ff69b4)](https://flake8.pycqa.org/)
[![Testing: pytest](https://img.shields.io/badge/testing-pytest-0d8fcc)](https://docs.pytest.org/)
[![Coverage](https://github.com/adraynrion/code-reviewer-agent/actions/workflows/test.yml/badge.svg?branch=main&event=push)](https://github.com/adraynrion/code-reviewer-agent/actions/workflows/test.yml)

An intelligent code review agent that analyzes pull requests on GitHub and GitLab, providing detailed feedback based on custom review instructions and language-specific best practices. Also includes a web crawler agent for documentation processing.

## ✨ Features

- 🤖 **AI-Powered** - Uses advanced language models to understand code changes
- 🔍 **Smart Analysis** - Analyzes git diffs to understand changes in context
- 🎨 **Beautiful Output** - Rich terminal formatting with syntax highlighting
- 🧪 **Type Hints** - Full type annotations for better development experience
- 📊 **Observability** - Built-in Langfuse integration for monitoring and analytics
- 🔹 **Multi-Platform Support** - Works with both GitHub and GitLab
- 📦 **Modular Architecture** - Built using Model Context Protocol (MCP) for extensibility
- 🗂️ **Vector Database Integration** - Stores and retrieves documentation using Supabase
- 🌲 **Environment-based Configuration** - Simple setup with environment variables

## 📦 Prerequisites

- Python 3.11.9
- Node.js 22+ and npm (for MCP servers)
- Git
- GitHub/GitLab account with appropriate permissions
- API keys for required services (see Configuration)

## 📦 Installation

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

3. Install in development mode with all dependencies:
```bash
# Install the dev requirements
pip install -e '.[dev]'
# Install the crawl4ai dependencies
crawl4ai-setup
```

4. Copy the example environment file and update with your details:
```bash
cp .env.example .env
# Edit .env with your tokens and configuration
```

## 🛠️ Configuration

Update the `.env` file with your configuration:

```sh
# Required: Platform (github or gitlab)
PLATFORM=github

# Required: Repository in format 'owner/repo' for GitHub or '<project_id>' for GitLab
REPOSITORY=owner/repo

# GitHub Configuration
# Note: Must be a personal access token, not a developer token
# The token will be used to assign the PR author as a reviewer
GITHUB_TOKEN=your_github_token_here

# GitLab Configuration (if using GitLab)
# GITLAB_TOKEN=your_gitlab_token_here
# GITLAB_API_URL=https://gitlab.com/api/v4  # For self-hosted GitLab

# LLM Configuration
LLM_API_KEY=your_llm_api_key_here
MODEL_CHOICE=gpt-4.1-mini  # or your preferred model
EMBEDDING_MODEL_CHOICE=text-embedding-ada-002  # or your preferred embedding model
BASE_URL=https://api.openai.com/v1  # API URL of the LLM provider

# Crawler Configuration (for documentation processing)
OPENAI_API_KEY=your_openai_api_key_here # For Crawler AI Agent only
SUPABASE_URL=your_supabase_url_here
SUPABASE_SERVICE_KEY=your_supabase_service_key_here

# Langfuse Configuration (optional)
# LANGFUSE_PUBLIC_KEY=your_public_key_here
# LANGFUSE_SECRET_KEY=your_secret_key_here
# LANGFUSE_HOST=https://cloud.langfuse.com
```

## 📝 Usage

### 🤖 Code Review Agent

Run the code review agent with the required PR/MR ID:

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

### 📚 Crawler Agent

The crawler agent processes documentation websites and stores the content in a vector database for later retrieval.

```bash
python crawler_agent.py --doc-url https://example.com/docs
```

#### Crawler Agent Command Line Arguments

| Argument | Description | Required | Default |
|----------|-------------|:--------:|:-------:|
| `--doc-url` | URL of the documentation to crawl | ✅ | - |
| `--max-depth` | Maximum depth of the crawl | ❌ | `3` |
| `--max-pages` | Maximum number of pages to crawl | ❌ | `None` |

## 🧪 Testing

Run the test suite:

```bash
make test
```

Run with coverage:

```bash
make test-cov
```

## 🛠️ Code Quality

We use several tools to maintain code quality. All commands can be run via the Makefile:

1. **Remove unused imports**:
```bash
make clean-imports
```

2. **Sort imports**:
```bash
make sort-imports
```

3. **Format code with Black**:
```bash
make format
```

4. **Format docstrings**:
```bash
make format-docs
```

5. **Add type annotations** (review changes carefully):
```bash
make add-type-annotations
```

6. **Run all code quality checks and formatting**:
```bash
make all
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📊 Monitoring and Observability

The agent includes built-in integration with [Langfuse](https://langfuse.com) for comprehensive monitoring and observability. This integration provides:

- **End-to-End Tracing**: Full trace of each code review request
- **LLM Monitoring**: Detailed tracking of all LLM interactions
- **Tool Usage**: Performance metrics for all tool calls
- **Error Tracking**: Centralized error tracking with context

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenAI](https://openai.com/)
- [Pydantic](https://pydantic-docs.helpmanual.io/)
- [Rich](https://github.com/Textualize/rich)
- [Supabase](https://supabase.com/)
- [Langfuse](https://langfuse.com/)
- [Crawl4AI](https://github.com/unclecode/crawl4ai)

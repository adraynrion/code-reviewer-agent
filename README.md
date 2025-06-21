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
- ⚙️ **Flexible Configuration** - Supports environment variables, config files, and CLI
- 📦 **Modular Architecture** - Built using Model Context Protocol (MCP) for extensibility
- 🗂️ **Vector Database Integration** - Stores and retrieves documentation using Supabase
- 🌲 **Environment-based Configuration** - Simple setup with environment variables

## 📦 Prerequisites

- Python 3.11.9
- Node.js 22+ and npm (for MCP servers)
- Git
- GitHub/GitLab account with appropriate permissions
- API keys for required services (see Configuration)
- Supabase account with appropriate permissions

## 🏗️ Supabase "documents" table

To work with the crawler agent, you need to create a "documents" table and a "match_documents" function in your Supabase database.
**All the necessary queries are stored under supabase/ folder.**

## 🚀 Installation

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

3. Install the package in development mode with all extras:
```bash
pip install -e '.[dev,crawler,langfuse]'

# Or for minimal installation
pip install -e .

# Install additional dependencies as needed
pip install -e '.[dev]'  # For development
pip install -e '.[crawler]'  # For web crawling functionality
pip install -e '.[langfuse]'  # For Langfuse observability
```

4. Init playwright:
```bash
# If missing any dependencies
npx playwright install-deps
# Init playwright
playwright install
```

5. Configure the application:
Copy the default_config.yaml file to ~/.config/code-reviewer/config.yaml and modify it as needed.

## 🚀 Usage

### Code Review Agent

```bash
# Run the code review agent
code-reviewer --help

# Example: Review a pull request
code-reviewer --repo-url https://github.com/owner/repo --pr 123
```

### Crawler Agent

```bash
# Run the crawler agent
crawler-agent --help

# Example: Crawl documentation
crawler-agent --url https://docs.example.com --max-pages 10
```

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

## 📊 Monitoring and Observability

The agent includes built-in integration with [Langfuse](https://langfuse.com) for comprehensive monitoring and observability. This integration provides:

- **End-to-End Tracing**: Full trace of each code review request
- **LLM Monitoring**: Detailed tracking of all LLM interactions
- **Tool Usage**: Performance metrics for all tool calls
- **Error Tracking**: Centralized error tracking with context

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenAI](https://openai.com/)
- [Pydantic](https://pydantic-docs.helpmanual.io/)
- [Rich](https://github.com/Textualize/rich)
- [Supabase](https://supabase.com/)
- [Langfuse](https://langfuse.com/)
- [Crawl4AI](https://github.com/unclecode/crawl4ai)

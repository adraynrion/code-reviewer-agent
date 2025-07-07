# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered code review agent that analyzes pull requests on GitHub and GitLab, providing detailed feedback based on custom review instructions and language-specific best practices. It also includes a web crawler agent for documentation processing and vector database integration.

## Architecture

### Core Components
- **Dual-purpose AI agent**: Code review + web crawling capabilities
- **Multi-platform support**: GitHub and GitLab integration
- **Vector knowledge base**: Supabase with pgvector for contextual retrieval
- **Configuration-driven**: YAML-based config with environment overrides
- **MCP-compatible**: Model Context Protocol integration for extensibility

### Key Directories
- `code_reviewer_agent/models/` - Pydantic models, AI agents, and data structures
- `code_reviewer_agent/services/` - Core business logic (GitHub/GitLab, crawling, code review)
- `code_reviewer_agent/config/` - Configuration management
- `code_reviewer_agent/prompts/` - AI prompt templates
- `code_reviewer_agent/utils/` - Shared utilities (Rich console, Langfuse, language detection)
- `supabase/` - Database schema and queries for vector storage

## Development Commands

### Setup
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with all dependencies
pip install -e '.[dev,crawler,langfuse]'

# Initialize playwright (for web crawling)
playwright install
```

### Code Quality
```bash
# Run all quality checks and formatting
make all

# Individual operations
make clean-imports      # Remove unused imports with pycln
make sort-imports       # Sort imports with isort
make format            # Format code with black
make format-docs       # Format docstrings with docformatter
make add-type-annotations  # Add type hints with autotyping
make type-check        # Run mypy static type checking
```

### Testing
```bash
make test              # Run pytest test suite
make test-cov          # Run tests with coverage reporting
```

### Build
```bash
make build             # Build PyInstaller executable
make clean             # Clean all build artifacts
```

## Configuration

### Config File Locations (in order of precedence):
1. `./config.yaml` (project root)
2. `~/.config/code-reviewer/config.yaml` (user config)
3. `/etc/code-reviewer/config.yaml` (system config)
4. `code_reviewer_agent/default_config.yaml` (fallback)

### Environment Variables
All config options can be overridden with environment variables using uppercase and underscore format (e.g., `OPENAI_API_KEY`, `SUPABASE_URL`).

## AI Integration

### Supported LLM Providers
- OpenAI (GPT-4, GPT-3.5-turbo)
- Google (Gemini)
- TogetherAI
- OpenRouter

### Agent Types
- **ReviewerAgent**: Code analysis and structured feedback generation
- **CrawlerAgents**: Web content extraction and processing
- **Base Agent**: Common AI model abstraction

## Database Integration

### Supabase Setup
The crawler agent requires a Supabase database with:
- `documents` table for storing crawled content
- `match_documents` function for similarity search
- pgvector extension for embeddings

SQL files are located in `supabase/` directory.

## CLI Usage

### Code Review
```bash
# Review a pull request
code-reviewer review --repo-url https://github.com/owner/repo --pr 123

# Review with custom config
code-reviewer review --config ./custom-config.yaml --repo-url https://github.com/owner/repo --pr 123
```

### Web Crawling
```bash
# Crawl documentation
code-reviewer crawl --url https://docs.example.com --max-pages 10

# Crawl with custom depth
code-reviewer crawl --url https://docs.example.com --max-depth 3
```

## Type Safety

This codebase uses strict type checking with:
- **mypy**: Static type analysis (configured in `mypy.ini`)
- **Pydantic**: Runtime type validation for all data models
- **Custom validators**: Extended built-in types in `base_types.py`

When adding new code, ensure all functions have proper type annotations and follow the existing patterns in the models/ directory.

## Error Handling

The codebase uses structured error handling with:
- **Rich console output**: Formatted error messages with syntax highlighting
- **Langfuse integration**: Optional observability and error tracking
- **Graceful degradation**: Fallback mechanisms for API failures

## Testing Strategy

- **pytest**: Main testing framework
- **pytest-asyncio**: For async test support
- **pytest-cov**: Coverage reporting
- **Mock external APIs**: Use fixtures for GitHub/GitLab API calls

Tests are located in `tests/` directory and follow the same structure as the main package.

## Contributing Guidelines

1. All new features must include type annotations
2. Follow the existing code style (enforced by black, isort, flake8)
3. Add tests for new functionality
4. Update configuration models in `pydantic_config_models.py` for new config options
5. Document new CLI options in the appropriate service classes
6. For AI prompt changes, update templates in `prompts/` directory

## Version Management

```bash
# Bump version and create git tag
make bump-version VERSION=1.2.3
```

This will update `code_reviewer_agent/__init__.py`, create a commit, and tag the release.
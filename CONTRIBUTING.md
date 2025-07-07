# Contributing to AI Code Review Agent

Thank you for your interest in contributing to the AI Code Review Agent! This document provides guidelines and instructions for contributors.

## Development Setup

### Prerequisites
- Python 3.11.9
- Node.js 22+ and npm (for MCP servers)
- Git
- GitHub/GitLab account with appropriate permissions

### Environment Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/adraynrion/code-reviewer-agent.git
   cd code-reviewer-agent
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -e '.[dev,crawler,langfuse]'
   ```

4. **Initialize Playwright** (for web crawling):
   ```bash
   playwright install
   ```

5. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

## Development Workflow

### Code Quality Standards

This project maintains high code quality standards using automated tools:

- **Black**: Code formatting (88 character line length)
- **isort**: Import sorting
- **mypy**: Static type checking
- **flake8**: Linting with multiple plugins
- **pytest**: Testing framework
- **pycln**: Remove unused imports
- **docformatter**: Docstring formatting

### Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the coding standards

3. **Run quality checks**:
   ```bash
   make all  # Runs all quality checks and formatting
   ```

4. **Run tests**:
   ```bash
   make test      # Run test suite
   make test-cov  # Run with coverage
   ```

5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "FEATURE/MEDIUM: AB-1234 - your descriptive commit message"
   ```
   
   Pre-commit hooks will automatically run and may modify your files. If files are modified, you'll need to add and commit again.

### Commit Message Convention

Follow this strict format:
```
<commit_type>/<severity>: <ticket> - <short_summary>

<detailed_description>
```

#### Allowed Commit Types:
| Type    | Severity Required | Purpose                             |
| ------- | ----------------- | ----------------------------------- |
| FEATURE | ✅ Yes             | New features                        |
| IMPROVE | ✅ Yes             | Enhancements or UX/UI improvements  |
| BUGFIX  | ✅ Yes             | Bug fixes or error handling         |
| REFACTO | ✅ Yes             | Refactoring with no behavior change |
| CORE    | ❌ Optional        | Build system, tools, dependencies   |
| TEST    | ❌ Optional        | Tests                               |
| DOC     | ❌ Not Required    | Documentation                       |

#### Severity Levels:
| Level  | When to Use                               |
| ------ | ----------------------------------------- |
| MAJOR  | Breaking or high-impact change            |
| MEDIUM | Mid-sized features or contained bug fixes |
| MINOR  | Cosmetic or non-critical changes          |

#### Examples:
```
FEATURE/MEDIUM: AB-1234 - add OAuth2 authentication support

Implement OAuth2 flow with Google and GitHub providers including
user session management and redirect handling for authentication
callbacks.
```

```
BUGFIX/MAJOR: CD-5678 - resolve null pointer exception in user validation

The validation middleware was not properly checking for null user
objects before accessing properties, causing crashes on invalid
requests that affected production stability.
```

## Code Standards

### Type Annotations
- All functions must have complete type annotations
- Use Pydantic models for data validation
- Follow the patterns in `models/base_types.py` for custom types

### Documentation
- Document all public functions and classes
- Use docstrings following Google format
- Update README.md for user-facing changes
- Update CLAUDE.md for development-related changes

### Testing
- Write tests for all new functionality
- Maintain test coverage above 80%
- Use pytest fixtures for common test data
- Mock external API calls

### Configuration
- Add new configuration options to `pydantic_config_models.py`
- Update `default_config.yaml` with sensible defaults
- Document configuration options in docstrings

## Pull Request Process

1. **Ensure all checks pass**:
   - All tests pass
   - Code quality checks pass
   - No security vulnerabilities
   - Documentation is updated

2. **Create pull request**:
   - Use descriptive title and description
   - Reference related issues
   - Include screenshots for UI changes
   - Add reviewer if known

3. **Review process**:
   - Address feedback promptly
   - Keep commits focused and atomic
   - Squash commits if requested

## CI/CD Pipeline

The project uses GitHub Actions for automated testing and deployment:

- **CI Pipeline**: Runs on every push and PR
  - Code quality checks
  - Test suite execution
  - Security scanning
  - Build verification

- **Release Pipeline**: Runs on version tags
  - Creates GitHub releases
  - Builds distribution packages
  - Generates release notes

## Architecture Guidelines

### AI Integration
- Use PydanticAI for structured AI interactions
- Implement proper error handling for AI failures
- Follow patterns in `models/base_agent.py`

### Service Layer
- Extend `BaseService` for new service implementations
- Use dependency injection for external dependencies
- Implement proper logging and observability

### Configuration Management
- Use layered configuration (file → environment → CLI)
- Validate all configuration with Pydantic
- Support both development and production scenarios

## Security Considerations

- Never commit API keys or sensitive data
- Use environment variables for secrets
- Follow OWASP guidelines for web security
- Implement proper input validation
- Use secure defaults in configuration

## Getting Help

- Check existing issues and discussions
- Create detailed bug reports with reproduction steps
- Join discussions for feature requests
- Ask questions in GitHub Discussions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
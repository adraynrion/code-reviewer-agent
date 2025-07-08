name: "Implement Comprehensive Test Coverage"
description: |
  Complete test suite implementation with 80% minimum coverage for the code reviewer agent application.

---

## Goal
Implement a comprehensive test suite with 80% minimum code coverage for the entire code reviewer agent application, following pytest best practices and establishing robust testing patterns for AI agents, API integrations, and configuration management.

## Why
- **Quality Assurance**: Prevent regressions and ensure code reliability in production
- **Development Velocity**: Enable confident refactoring and feature development
- **CI/CD Integration**: Automated testing gates prevent broken code from reaching production
- **Maintainability**: Well-tested code is easier to understand, modify, and extend
- **Cost Reduction**: Catch bugs early in development cycle, reducing debugging time

## What
Create a complete test suite covering all major components of the code reviewer agent:
- AI agent testing with proper LLM mocking
- GitHub/GitLab API integration testing
- Configuration management testing
- Pydantic model validation testing
- Async service testing
- Utility function testing

### Success Criteria
- [ ] 80% minimum code coverage achieved
- [ ] All tests pass consistently
- [ ] CI/CD integration with coverage enforcement
- [ ] Comprehensive test documentation
- [ ] Zero test-related technical debt

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://ai.pydantic.dev/testing/
  why: PydanticAI testing patterns with TestModel and FunctionModel
  critical: Avoid actual LLM API calls and costs in tests

- url: https://colin-b.github.io/pytest_httpx/
  why: HTTP mocking for GitHub/GitLab API calls
  critical: pytest-httpx provides fixture for HTTPX request mocking

- url: https://docs.pytest.org/en/stable/how-to/fixtures.html
  why: Fixture patterns for test organization and reusability
  critical: Modular fixtures for configuration and service mocking

- url: https://tonybaloney.github.io/posts/async-test-patterns-for-pytest-and-unittest.html
  why: Async testing patterns for service layer
  critical: Proper async/await testing with pytest-asyncio

- url: https://medium.com/@keployio/mastering-python-test-coverage-tools-tips-and-best-practices-11daf699d79b
  why: Coverage configuration and 80% minimum enforcement
  critical: Quality over quantity in coverage metrics

- file: code_reviewer_agent/models/base_agent.py
  why: AI agent architecture patterns to follow
  critical: PydanticAI agent structure and dependency injection

- file: code_reviewer_agent/services/github.py
  why: API service patterns for mocking
  critical: Async HTTP client patterns and error handling

- file: code_reviewer_agent/config/config.py
  why: Configuration loading precedence logic
  critical: File/environment variable precedence testing

- file: pyproject.toml
  why: Existing coverage configuration and dev dependencies
  critical: Coverage settings already configured, just need tests
```

### Current Codebase Structure
```
code_reviewer_agent/
├── models/
│   ├── base_agent.py          # AI agent base class
│   ├── base_types.py          # Custom validators
│   ├── crawler_agents.py      # Web crawler agents
│   ├── pydantic_config_models.py  # Config models
│   ├── pydantic_reviewer_models.py  # Review models
│   └── reviewer_agent.py      # Main reviewer agent
├── services/
│   ├── code_reviewer.py       # Main orchestration
│   ├── contextual_retrieval.py # Vector DB operations
│   ├── crawler.py             # Web crawling
│   ├── github.py              # GitHub API integration
│   ├── gitlab.py              # GitLab API integration
│   └── repository.py          # Repository abstraction
├── config/
│   └── config.py              # Configuration management
├── utils/
│   ├── language_utils.py      # Language detection
│   ├── rich_utils.py          # Console output
│   └── langfuse.py            # Observability
└── prompts/
    └── cr_agent.py            # Prompt templates
```

### Desired Test Structure
```
tests/
├── __init__.py                # (exists)
├── conftest.py                # Shared fixtures
├── test_models/
│   ├── test_base_types.py     # Custom validator testing
│   ├── test_config_models.py  # Config model validation
│   ├── test_reviewer_agent.py # AI agent testing
│   └── test_crawler_agents.py # Crawler agent testing
├── test_services/
│   ├── test_code_reviewer.py  # Main orchestration
│   ├── test_github.py         # GitHub API mocking
│   ├── test_gitlab.py         # GitLab API mocking
│   └── test_contextual_retrieval.py # Vector DB testing
├── test_config/
│   └── test_config.py         # Configuration precedence
├── test_utils/
│   ├── test_language_utils.py # Language detection
│   └── test_rich_utils.py     # Console utilities
└── integration/
    └── test_end_to_end.py     # Full workflow testing
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: PydanticAI requires TestModel for testing
# Use TestModel to avoid actual LLM API calls and costs
# Example: agent.override(model=TestModel())

# CRITICAL: Async testing requires pytest-asyncio
# Use @pytest.mark.asyncio for async test functions
# Example: async def test_async_service()

# CRITICAL: GitHub/GitLab APIs have rate limits
# Use pytest-httpx to mock all HTTP requests
# Example: httpx_mock.add_response(json={"key": "value"})

# CRITICAL: Configuration has file precedence rules
# Test config loading from: ./config.yaml -> ~/.config/code-reviewer/config.yaml -> /etc/code-reviewer/config.yaml -> default_config.yaml
# Use tmp_path fixture for temporary config files

# CRITICAL: Coverage excludes CLI entry points
# pyproject.toml already excludes __main__.py and __init__.py
# Focus on business logic for 80% coverage target

# CRITICAL: Rich console output needs special testing
# Use StringIO or capsys fixtures for console output testing
# Rich formatting may interfere with standard output capture
```

## Implementation Blueprint

### Core Dependencies to Add
```python
# Additional testing dependencies needed:
# pytest-httpx==0.30.0  # HTTP mocking for API calls
# pytest-xdist==3.5.0   # Parallel test execution
# pytest-mock==3.12.0   # Enhanced mocking capabilities
```

### List of Tasks in Implementation Order

```yaml
Task 1: Setup Test Infrastructure
CREATE tests/conftest.py:
  - IMPLEMENT shared fixtures for configuration
  - IMPLEMENT AI agent fixtures with TestModel
  - IMPLEMENT HTTP mocking fixtures
  - IMPLEMENT async test utilities

Task 2: Foundation Testing - Base Types
CREATE tests/test_models/test_base_types.py:
  - MIRROR validation patterns from base_types.py
  - TEST custom validators with edge cases
  - TEST type coercion and validation errors
  - ACHIEVE 90%+ coverage for type safety

Task 3: Foundation Testing - Configuration
CREATE tests/test_config/test_config.py:
  - TEST configuration file precedence logic
  - TEST environment variable overrides
  - TEST default configuration loading
  - TEST invalid configuration handling

Task 4: Model Testing - Pydantic Models
CREATE tests/test_models/test_config_models.py:
  - TEST all configuration model validations
  - TEST field validators and constraints
  - TEST model serialization/deserialization
  - USE parametrize for multiple validation scenarios

Task 5: Utility Testing
CREATE tests/test_utils/test_language_utils.py:
  - TEST language detection for various file types
  - TEST edge cases (empty files, binary files)
  - TEST language mapping accuracy
  - ACHIEVE 85%+ coverage for utility functions

Task 6: API Service Testing - GitHub
CREATE tests/test_services/test_github.py:
  - MOCK GitHub API responses with pytest-httpx
  - TEST pull request fetching logic
  - TEST error handling (404, 403, rate limits)
  - TEST async request patterns
  - PATTERN: Use httpx_mock.add_response for API mocking

Task 7: API Service Testing - GitLab  
CREATE tests/test_services/test_gitlab.py:
  - MIRROR GitHub testing patterns
  - MOCK GitLab API responses
  - TEST merge request operations
  - TEST authentication handling
  - PRESERVE identical error handling patterns

Task 8: Service Testing - Code Reviewer
CREATE tests/test_services/test_code_reviewer.py:
  - MOCK file system operations
  - TEST async orchestration logic
  - TEST error aggregation and reporting
  - PATTERN: Use AsyncMock for async dependencies

Task 9: Service Testing - Contextual Retrieval
CREATE tests/test_services/test_contextual_retrieval.py:
  - MOCK Supabase database operations
  - TEST vector similarity search
  - TEST document embedding workflows
  - PATTERN: Mock vecs client operations

Task 10: AI Agent Testing - Reviewer Agent
CREATE tests/test_models/test_reviewer_agent.py:
  - USE TestModel to avoid LLM API calls
  - TEST prompt template rendering
  - TEST structured response parsing
  - TEST tool integration with crawler
  - PATTERN: agent.override(model=TestModel())

Task 11: AI Agent Testing - Crawler Agents
CREATE tests/test_models/test_crawler_agents.py:
  - MOCK web crawling with pytest-httpx
  - TEST async crawling workflows
  - TEST content extraction logic
  - TEST error handling for failed crawls

Task 12: Integration Testing
CREATE tests/integration/test_end_to_end.py:
  - TEST complete PR review workflow
  - MOCK all external dependencies
  - TEST CLI command execution
  - VERIFY end-to-end functionality

Task 13: Coverage Enforcement
MODIFY pyproject.toml:
  - VERIFY coverage configuration
  - ENSURE 80% minimum threshold
  - CONFIGURE coverage reporting

UPDATE .github/workflows/ci.yml:
  - ADD coverage enforcement step
  - ADD complexity analysis with radon
  - ENSURE CI fails on insufficient coverage
```

### Critical Testing Patterns

```python
# AI Agent Testing with TestModel
@pytest.fixture
def mock_reviewer_agent():
    """Fixture for testing AI agent without LLM calls"""
    with reviewer_agent.override(model=TestModel()):
        yield reviewer_agent

# Async Service Testing
@pytest.mark.asyncio
async def test_async_service():
    """Pattern for testing async services"""
    # Use AsyncMock for async dependencies
    with patch('external_service.call', new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {"result": "success"}
        result = await service.process()
        assert result.status == "success"

# HTTP API Mocking
def test_github_api(httpx_mock):
    """Pattern for mocking HTTP APIs"""
    httpx_mock.add_response(
        method="GET",
        url="https://api.github.com/repos/owner/repo/pulls/1",
        json={"number": 1, "title": "Test PR"}
    )
    result = github_service.get_pull_request("owner/repo", 1)
    assert result["number"] == 1

# Configuration Testing
def test_config_precedence(tmp_path):
    """Pattern for testing configuration loading"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("openai_api_key: test_key")
    
    with patch.dict(os.environ, {"OPENAI_API_KEY": "env_key"}):
        config = load_config(str(config_file))
        assert config.openai_api_key == "env_key"  # Env overrides file
```

## Validation Loop

### Level 1: Code Quality & Syntax
```bash
# Run existing quality checks first
make all                    # Format, lint, type check
mypy tests/                 # Type check test files
pytest --collect-only       # Verify test discovery

# Expected: No errors. All existing quality gates pass.
```

### Level 2: Unit Tests Development
```bash
# Run tests incrementally as you build them
pytest tests/test_models/test_base_types.py -v
pytest tests/test_config/test_config.py -v
pytest tests/test_services/test_github.py -v
# Continue for each test module...

# Expected: All tests pass. No skipped tests.
```

### Level 3: Coverage Validation
```bash
# Check coverage incrementally
pytest --cov=code_reviewer_agent --cov-report=term-missing tests/
pytest --cov=code_reviewer_agent --cov-report=html tests/

# Enforce 80% minimum coverage
pytest --cov=code_reviewer_agent --cov-fail-under=80 tests/

# Expected: 80%+ coverage achieved. HTML report shows uncovered lines.
```

### Level 4: Integration Testing
```bash
# Run full test suite
pytest tests/ -v --tb=short

# Run with performance profiling
pytest tests/ --durations=10

# Expected: All tests pass in reasonable time (<2 minutes total)
```

## Final Validation Checklist
- [ ] All tests pass: `pytest tests/ -v`
- [ ] 80% coverage achieved: `pytest --cov=code_reviewer_agent --cov-fail-under=80 tests/`
- [ ] No linting errors: `make all`
- [ ] Type checking passes: `mypy .`
- [ ] CI/CD integration working: Coverage enforcement in GitHub Actions
- [ ] Performance acceptable: Test suite runs in <2 minutes
- [ ] Documentation complete: Test patterns documented for future development

---

## Anti-Patterns to Avoid
- ❌ Don't make actual API calls in tests (use mocking)
- ❌ Don't use actual LLM models in tests (use TestModel)
- ❌ Don't test implementation details (focus on behavior)
- ❌ Don't skip error handling test cases
- ❌ Don't hardcode test data (use fixtures and parametrize)
- ❌ Don't ignore async/await patterns in async tests
- ❌ Don't mock too broadly (be specific about what you mock)

**PRP Confidence Score: 8/10**

This PRP provides comprehensive context, specific implementation patterns, and clear validation loops. The AI agent should be able to implement this successfully with the detailed documentation references, code patterns, and testing strategies provided. The 8/10 confidence reflects the complexity of AI agent testing but acknowledges the thorough preparation and context provided.
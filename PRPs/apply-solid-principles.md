name: "Apply SOLID Principles to Code Reviewer Agent"
description: |
  Comprehensive refactoring to apply SOLID principles to the CodeReviewService class and other violations throughout the codebase.

---

## Goal
Refactor the CodeReviewService class (code_reviewer_agent/services/code_reviewer.py:36-322) to apply SOLID principles, splitting it into focused classes with single responsibilities. Additionally, identify and fix other SOLID principle violations throughout the codebase to improve maintainability, testability, and extensibility.

## Why
- **Maintainability**: Current CodeReviewService has 4+ responsibilities mixed together making it difficult to maintain
- **Testability**: Monolithic class structure makes unit testing nearly impossible
- **Extensibility**: Adding new platforms requires modifying existing code instead of extending
- **Code Quality**: 322 lines of mixed concerns violate fundamental design principles
- **Developer Experience**: Complex interdependencies make the code difficult to understand and debug

## What
Transform the monolithic CodeReviewService into a well-structured, SOLID-compliant architecture with clear separation of concerns.

### Success Criteria
- [ ] CodeReviewService class is split into focused classes with single responsibilities
- [ ] New platforms can be added without modifying existing code (Open/Closed Principle)
- [ ] Each class has a single reason to change (Single Responsibility Principle)
- [ ] Dependencies are properly abstracted (Dependency Inversion Principle)
- [ ] All existing functionality is preserved with identical CLI interface
- [ ] Code passes all linting, type checking, and existing tests
- [ ] Additional SOLID violations in other files are identified and fixed

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://www.geeksforgeeks.org/system-design/solid-principle-in-programming-understand-with-real-life-examples/
  why: Practical examples and before/after code for each SOLID principle
  critical: Shows Factory pattern implementation and dependency injection

- file: code_reviewer_agent/services/code_reviewer.py
  why: Primary file to refactor - contains all the SOLID violations
  critical: Lines 36-322 show the monolithic structure that needs splitting

- file: code_reviewer_agent/services/base_service.py
  why: Inheritance pattern to follow for new classes
  critical: Shows how config and langfuse are properly injected

- file: code_reviewer_agent/services/repository.py
  why: Shows proper ABC usage and platform abstraction patterns
  critical: Lines 24-111 demonstrate good interface design

- file: code_reviewer_agent/models/base_agent.py
  why: Shows configuration patterns and provider setup
  critical: Lines 52-133 also have SOLID violations to fix

- file: code_reviewer_agent/models/reviewer_agent.py
  why: Shows agent management patterns
  critical: Lines 21-61 InstructionPath class needs extraction

- file: code_reviewer_agent/utils/rich_utils.py
  why: Logging patterns that must be preserved
  critical: Consistent console output formatting requirements
```

### Current Codebase Tree
```bash
code_reviewer_agent/
├── models/
│   ├── base_agent.py           # AiModel class - configuration violations
│   ├── reviewer_agent.py       # InstructionPath class - SRP violation
│   ├── base_types.py           # Type definitions
│   └── pydantic_*.py          # Pydantic models
├── services/
│   ├── base_service.py         # Base class pattern
│   ├── code_reviewer.py        # MAIN TARGET - monolithic class
│   ├── repository.py           # ABC pattern (has violations in diffs setter)
│   ├── github.py              # Platform implementation
│   └── gitlab.py              # Platform implementation
├── utils/
│   ├── rich_utils.py           # Console output patterns
│   └── langfuse.py            # Observability integration
└── config/
    └── config.py              # Configuration management
```

### Desired Codebase Tree with New Files
```bash
code_reviewer_agent/
├── models/
│   ├── base_agent.py           # [MODIFIED] Separate provider setup
│   ├── reviewer_agent.py       # [MODIFIED] Extract InstructionPath
│   └── instruction_loader.py   # [NEW] Handle filesystem instructions
├── services/
│   ├── base_service.py         # [UNCHANGED] Base class
│   ├── code_reviewer.py        # [MODIFIED] Slim orchestrator only
│   ├── platform_factory.py     # [NEW] Factory for platform services
│   ├── configuration_manager.py # [NEW] Configuration validation
│   ├── review_orchestrator.py  # [NEW] Main review workflow
│   ├── review_file_processor.py # [NEW] Individual file processing
│   └── repository.py           # [MODIFIED] Fix diffs setter
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: Pydantic v2 is used throughout - ensure compatibility
# CRITICAL: Rich console formatting must be preserved exactly
# CRITICAL: Langfuse integration requires specific span management
# CRITICAL: Platform service initialization order matters for tokens
# CRITICAL: Configuration validation timing is critical - validate before use
# CRITICAL: Error handling patterns must be preserved for CLI stability
# CRITICAL: Type annotations must be maintained for mypy compliance
# CRITICAL: BaseService inheritance provides config and langfuse access
```

## Implementation Blueprint

### Data Models and Structure
```python
# Core classes that need to be created following existing patterns

class PlatformServiceFactory:
    """Factory for creating platform-specific services (solves OCP, DIP)"""
    @staticmethod
    def create_service(platform: Platform, repository: Repository, 
                      request_id: RequestId, config: ReviewerConfig) -> RepositoryService

class ConfigurationManager:
    """Manages configuration validation and platform-specific settings (solves SRP)"""
    def __init__(self, config: Config, platform: Platform, repository: Repository, 
                 request_id: RequestId, instructions_path: InstructionsPath)
    def validate_platform_config(self) -> None
    def get_platform_credentials(self) -> dict[str, Token]

class ReviewOrchestrator(BaseService):
    """Orchestrates the review process (solves SRP)"""
    def __init__(self, config_manager: ConfigurationManager, 
                 platform_factory: PlatformServiceFactory, reviewer_agent: ReviewerAgent)
    async def orchestrate_review(self) -> None

class ReviewFileProcessor:
    """Processes individual files for review (solves SRP)"""
    async def process_file(self, diff: CodeDiff, agent: Agent, 
                          repository_service: RepositoryService) -> CodeReviewResponse
```

### List of Tasks to Complete (in order)

```yaml
Task 1: Create PlatformServiceFactory
CREATE code_reviewer_agent/services/platform_factory.py:
  - IMPLEMENT Factory pattern for platform service creation
  - ABSTRACT GitHub/GitLab service instantiation
  - FOLLOW existing type annotation patterns
  - PRESERVE error handling for invalid platforms

Task 2: Create ConfigurationManager
CREATE code_reviewer_agent/services/configuration_manager.py:
  - EXTRACT configuration validation logic from CodeReviewService
  - IMPLEMENT platform-specific validation (lines 100-114 from original)
  - PRESERVE existing property patterns and type safety
  - MAINTAIN error messages for missing tokens

Task 3: Create ReviewFileProcessor
CREATE code_reviewer_agent/services/review_file_processor.py:
  - EXTRACT file processing logic (lines 157-283 from original)
  - IMPLEMENT single file review workflow
  - PRESERVE langfuse integration patterns
  - MAINTAIN error handling for file failures

Task 4: Create ReviewOrchestrator
CREATE code_reviewer_agent/services/review_orchestrator.py:
  - EXTRACT main review workflow (lines 285-322 from original)
  - IMPLEMENT orchestration using new classes
  - PRESERVE BaseService inheritance for config/langfuse
  - MAINTAIN rich console output patterns

Task 5: Refactor CodeReviewService
MODIFY code_reviewer_agent/services/code_reviewer.py:
  - SIMPLIFY to thin facade/compatibility layer
  - DELEGATE responsibilities to new classes
  - PRESERVE existing public interface for CLI
  - MAINTAIN backward compatibility

Task 6: Extract InstructionPath utility
CREATE code_reviewer_agent/utils/instruction_loader.py:
  - MOVE InstructionPath class from reviewer_agent.py
  - IMPLEMENT as standalone utility
  - PRESERVE filesystem loading logic
  - MAINTAIN console output patterns

Task 7: Refactor RepositoryService diffs setter
MODIFY code_reviewer_agent/services/repository.py:
  - EXTRACT file processing logic to separate method
  - SIMPLIFY diffs setter responsibility
  - PRESERVE existing functionality
  - MAINTAIN type safety

Task 8: Refactor AiModel configuration
MODIFY code_reviewer_agent/models/base_agent.py:
  - SEPARATE provider setup from configuration
  - IMPLEMENT provider factory pattern
  - PRESERVE existing functionality
  - MAINTAIN type annotations

Task 9: Create comprehensive tests
CREATE tests/test_*.py files:
  - UNIT tests for each new class
  - INTEGRATION tests for review workflow
  - MOCK external dependencies appropriately
  - FOLLOW pytest patterns

Task 10: Validation and integration
RUN validation commands:
  - EXECUTE linting and type checking
  - VERIFY all tests pass
  - CONFIRM CLI functionality unchanged
  - VALIDATE error handling preserved
```

### Per Task Pseudocode

```python
# Task 1: PlatformServiceFactory
class PlatformServiceFactory:
    @staticmethod
    def create_service(platform: Platform, repository: Repository, 
                      request_id: RequestId, config: ReviewerConfig) -> RepositoryService:
        # PATTERN: Factory pattern with static method
        if platform == "github":
            return GitHubReviewerService(repository, request_id, config)
        elif platform == "gitlab":
            return GitLabReviewerService(repository, request_id, config)
        else:
            # PRESERVE: Same error message as original
            raise ValueError("Invalid platform. Must be either 'github' or 'gitlab'.")

# Task 2: ConfigurationManager
class ConfigurationManager:
    def __init__(self, config: Config, platform: Platform, repository: Repository, 
                 request_id: RequestId, instructions_path: InstructionsPath):
        # PATTERN: Validate all configuration in constructor
        self._validate_and_set_config(config, platform, repository, request_id, instructions_path)
    
    def _validate_and_set_config(self, ...):
        # EXTRACT: Lines 100-114 from original CodeReviewService
        # PRESERVE: Same validation logic and error messages
        # PATTERN: Use existing property setter patterns

# Task 3: ReviewFileProcessor
class ReviewFileProcessor:
    async def process_file(self, diff: CodeDiff, agent: Agent, 
                          repository_service: RepositoryService) -> CodeReviewResponse:
        # EXTRACT: Lines 157-283 from original
        # PATTERN: Use existing langfuse span management
        # PRESERVE: Same error handling and retry logic
        # MAINTAIN: Rich console output patterns

# Task 4: ReviewOrchestrator
class ReviewOrchestrator(BaseService):
    def __init__(self, config_manager: ConfigurationManager, 
                 platform_factory: PlatformServiceFactory, reviewer_agent: ReviewerAgent):
        # PATTERN: Follow BaseService inheritance
        super().__init__(config_manager.config)
        # INJECT: Dependencies through constructor
        
    async def orchestrate_review(self) -> None:
        # EXTRACT: Lines 285-322 from original main() method
        # DELEGATE: File processing to ReviewFileProcessor
        # PRESERVE: Same workflow and error handling
```

### Integration Points
```yaml
CLI_INTEGRATION:
  - maintain: CodeReviewService as entry point
  - preserve: All existing CLI arguments and behavior
  - ensure: Same error codes and messages

CONFIGURATION:
  - use: Existing Config class and patterns
  - preserve: Environment variable overrides
  - maintain: Configuration validation timing

LOGGING:
  - preserve: All rich console output patterns
  - maintain: Same debug/info/error message formats
  - ensure: Consistent logging across new classes

OBSERVABILITY:
  - preserve: Langfuse integration patterns
  - maintain: Same span names and attributes
  - ensure: Proper span lifecycle management
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
ruff check code_reviewer_agent/ --fix     # Auto-fix formatting issues
mypy code_reviewer_agent/                 # Type checking
black code_reviewer_agent/                # Code formatting

# Expected: No errors. If errors exist, read carefully and fix.
```

### Level 2: Unit Tests
```python
# CREATE comprehensive test suite for new classes
def test_platform_factory_github():
    """Test GitHub service creation"""
    service = PlatformServiceFactory.create_service("github", repo, request_id, config)
    assert isinstance(service, GitHubReviewerService)

def test_platform_factory_invalid():
    """Test invalid platform handling"""
    with pytest.raises(ValueError, match="Invalid platform"):
        PlatformServiceFactory.create_service("invalid", repo, request_id, config)

def test_configuration_manager_validation():
    """Test configuration validation"""
    with pytest.raises(ValueError, match="github_token"):
        ConfigurationManager(config_without_token, "github", repo, request_id, instructions)

def test_review_orchestrator_workflow():
    """Test review orchestration"""
    orchestrator = ReviewOrchestrator(config_manager, factory, agent)
    # Mock dependencies and test workflow
```

```bash
# Run and iterate until passing:
pytest tests/ -v --tb=short
# If failing: Read error messages, understand root cause, fix code, re-run
```

### Level 3: Integration Test
```bash
# Test the complete CLI workflow
python -m code_reviewer_agent review --repo-url https://github.com/test/repo --pr 123

# Expected: Same behavior as before refactoring
# If different: Check logs and compare outputs with original
```

## Final Validation Checklist
- [ ] All tests pass: `pytest tests/ -v`
- [ ] No linting errors: `ruff check code_reviewer_agent/`
- [ ] No type errors: `mypy code_reviewer_agent/`
- [ ] CLI interface unchanged: Test with sample commands
- [ ] Error handling preserved: Test error scenarios
- [ ] Console output maintained: Verify rich formatting
- [ ] Performance unchanged: Compare execution times
- [ ] All SOLID principles applied: Review class responsibilities

---

## Anti-Patterns to Avoid
- ❌ Don't break existing CLI interface or change command arguments
- ❌ Don't modify error messages or console output formats
- ❌ Don't skip type annotations - maintain mypy compliance
- ❌ Don't ignore langfuse integration - preserve observability
- ❌ Don't change configuration loading order - maintain validation timing
- ❌ Don't remove rich console formatting - preserve user experience
- ❌ Don't create new configuration patterns - follow existing Config class
- ❌ Don't break BaseService inheritance - maintain config/langfuse access

## Confidence Score: 9/10
This PRP provides comprehensive context, clear implementation steps, and thorough validation for successfully applying SOLID principles while maintaining all existing functionality. The systematic approach and detailed guidance should enable one-pass implementation success.
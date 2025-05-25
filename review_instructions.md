# Code Review Instructions

## General Guidelines

- Be kind and constructive in all feedback
- Focus on the code, not the person
- Explain the 'why' behind suggestions
- Acknowledge good practices when you see them
- Keep feedback actionable and specific

## Project-Specific Rules

### Python
- Follow PEP 8 style guide
- Use type hints for all function signatures
- Keep functions small and focused (max 30 lines)
- Use list/dict comprehensions when appropriate
- Prefer f-strings over %-formatting or .format()
- Use `pathlib` instead of `os.path` for filesystem operations
- Add docstrings to all public functions/classes/modules
- Use `logging` instead of `print`
- Handle exceptions specifically, don't use bare `except`
- Use virtual environments (venv/poetry/pipenv)

### JavaScript/TypeScript
- Use `const` by default, `let` when needed, avoid `var`
- Use arrow functions for callbacks
- Prefer template literals over string concatenation
- Use `===` instead of `==`
- Use ES6+ features when possible
- Add JSDoc/TypeScript types for all functions
- Handle Promises properly with async/await
- Follow the Airbnb JavaScript Style Guide

### Security
- Never commit secrets or credentials
- Sanitize all user inputs
- Use parameterized queries for database access
- Validate all API responses
- Set secure HTTP headers (CSP, HSTS, etc.)
- Use environment variables for configuration
- Keep dependencies updated

### Testing
- Write tests for new features and bug fixes
- Follow the testing pyramid (more unit tests than integration/e2e)
- Use descriptive test names
- Test edge cases and error conditions
- Keep tests independent and deterministic
- Mock external dependencies
- Aim for at least 80% code coverage

### Documentation
- Update README.md for significant changes
- Document architecture decisions (ADRs)
- Add comments for complex logic
- Keep API documentation up to date
- Document environment variables

### Git
- Write clear, concise commit messages
- Keep commits small and focused
- Use feature branches
- Rebase before merging to main
- Clean up merged branches
- Use meaningful PR titles and descriptions

## Code Review Checklist

Before submitting a review, check for:
- [ ] Code style consistency
- [ ] Proper error handling
- [ ] Test coverage
- [ ] Documentation updates
- [ ] Security considerations
- [ ] Performance implications
- [ ] Backward compatibility
- [ ] Accessibility concerns

## Common Issues to Watch For

- Magic numbers/strings
- Code duplication
- Overly complex conditionals
- Unused imports/variables
- Memory leaks
- Race conditions
- Hardcoded values
- Inconsistent error handling
- Lack of input validation
- Inefficient algorithms/data structures

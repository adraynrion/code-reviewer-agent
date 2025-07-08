## FEATURE:
[Describe what you want to build - be specific about functionality and requirements]
Based on a recent analysis, the following result has been approved for modification:

Location: code_reviewer_agent/services/code_reviewer.py:36-322

- Issue: CodeReviewService handles platform routing, configuration, agent management, and review orchestration (4+ responsibilities)
- Complexity: 322 lines with multiple concerns mixed together
- Impact: Difficult to test, maintain, and extend

The fix to apply is then the following:

Apply SOLID principles:
# Split into focused classes
class PlatformServiceFactory:
    """Factory for creating platform-specific services"""

class ReviewOrchestrator:
    """Orchestrates the review process"""

class ConfigurationManager:
    """Manages configuration validation"""


## EXAMPLES:
Follow examples within documentation website listed below.

## DOCUMENTATION:
- SOLID Principles: Clean Code by Robert Martin
- SOLID Principles with examples: https://www.geeksforgeeks.org/system-design/solid-principle-in-programming-understand-with-real-life-examples/

## OTHER CONSIDERATIONS:
Besides the actual fix to apply, analyze the code for any other files/classes with bad/broken SOLID principles and fix it too.

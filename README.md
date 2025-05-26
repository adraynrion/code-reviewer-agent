# AI Code Review Agent

An intelligent code review agent that analyzes pull requests on GitHub and GitLab, providing detailed feedback based on custom review instructions and language-specific best practices.

## Features

- **Multi-Platform Support**: Works with both GitHub and GitLab
- **Custom Review Instructions**: Follows guidelines defined in `review_instructions.md`
- **Language-Aware**: Provides feedback based on language-specific best practices
- **Comprehensive Feedback**: Covers code quality, security, performance, and more
- **Easy Integration**: Simple setup with environment variables

## Prerequisites

- Python 3.8+
- Git
- Node.js 16+ and npm (for Brave MCP Search submodule)
- GitHub/GitLab account with appropriate permissions
- Brave Search API key (for web search functionality)

## Installation

1. Clone the repository with submodules:
   ```bash
   git clone --recurse-submodules https://github.com/yourusername/code-reviewer-agent.git
   cd code-reviewer-agent
   ```

   If you already cloned without submodules, initialize them with:
   ```bash
   git submodule update --init --recursive
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Python dependencies for the Brave MCP search module using uv:
   ```bash
   cd brave_mcp_search
   uv pip install -r requirements.txt
   cd ..
   ```

   Note: If you don't have `uv` installed, you can install it with:
   ```bash
   curl -sSf https://astral.sh/uv/install.sh | sh
   ```

5. Copy the example environment file and update with your details:
   ```bash
   cp .env.example .env
   # Edit .env with your tokens and repository information
   ```

## Architecture

The agent is built with a modular architecture that includes the following components:

- **Main Agent**: Core functionality for code review and analysis
- **Context7 MCP Integration**: For accessing library documentation and resolving library IDs
- **Brave MCP Search**: Submodule for performing web searches using the Brave Search API

### Submodules

- `brave_mcp_search/`: Contains the Brave Search MCP server implementation
  - Requires Node.js and npm
  - Automatically started by the agent when needed
  - Communicates via JSON-RPC over stdio

## Configuration

1. **GitHub Setup**:
   - Create a Personal Access Token with `repo` scope
   - Set `GITHUB_TOKEN` in `.env`

2. **GitLab Setup**:
   - Create a Personal Access Token with `api` scope
   - Set `GITLAB_TOKEN` in `.env`

3. **Environment Variables** (`.env` file):
   ```
   # Required for GitHub
   GITHUB_TOKEN=your_github_token_here

   # Required for GitLab
   # GITLAB_TOKEN=your_gitlab_token_here

   # Required: Platform (github or gitlab)
   PLATFORM=github

   # Required: Repository in format 'owner/repo' for GitHub or 'group/project' for GitLab
   REPOSITORY=owner/repo

   # OpenAI API Key (required for AI analysis)
   OPENAI_API_KEY=your_openai_api_key_here

   # Brave Search API Key (required for web search functionality)
   BRAVE_API_KEY=your_brave_api_key_here
   ```

## Usage

1. Update `review_instructions.md` with your custom review guidelines
2. Run the agent with the required PR ID:
   ```bash
   # Basic usage
   python agent.py --pr-id 123

   # Full options
   python agent.py \
     --pr-id 123 \
     --repository owner/repo \
     --platform github \
     --instructions review_instructions.md \
     --log-level INFO
   ```

### Command Line Arguments

| Argument | Description | Required | Default |
|----------|-------------|:--------:|:-------:|
| `--pr-id` | Pull/Merge Request ID | ✅ | - |
| `--repository` | Repository in format `owner/repo` (GitHub) or `group/project` (GitLab) | ❌ | Uses `REPOSITORY` env var |
| `--platform` | Version control platform: `github` or `gitlab` | ❌ | Uses `PLATFORM` env var or `github` |
| `--instructions` | Path to custom review instructions file | ❌ | `review_instructions.md` |
| `--log-level` | Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL | ❌ | `INFO` |

### Environment Variables

All command line arguments can be set via environment variables for convenience:

- `REPOSITORY`
- `PLATFORM`
- `GITHUB_TOKEN`
- `GITLAB_TOKEN`
- `OPENAI_API_KEY`

Command line arguments take precedence over environment variables.
   python agent.py
   ```

The agent will:
1. Fetch the PR/MR diff
2. Load custom review instructions
3. Detect languages in the changes
4. Retrieve language-specific best practices
5. Generate and post review comments

## Customization

### Review Instructions
Edit `review_instructions.md` to include your team's specific:
- Coding standards
- Security requirements
- Documentation guidelines
- Testing expectations
- Any other project-specific rules

### Language Support
The agent automatically detects languages from file extensions. To add support for additional languages:
1. Update the `detect_languages` function in `agent_tools.py`
2. Add language-specific best practices in the `search_best_practices` function

## Best Practices

1. **Keep PRs Small**: Smaller PRs are easier to review and get better feedback
2. **Clear Descriptions**: Provide context about the changes in PR descriptions
3. **Update Documentation**: Include necessary updates to READMEs and other docs
4. **Add Tests**: Include tests for new features and bug fixes
5. **Run Linters**: Fix any linting issues before submitting for review

## Troubleshooting

- **Authentication Errors**: Verify your tokens have the correct permissions
- **Rate Limiting**: If you hit API rate limits, wait before retrying
- **File Not Found**: Ensure file paths in your configuration are correct
- **Permission Issues**: Check repository access for the token being used
- **Submodule Issues**: If you encounter issues with submodules:
  ```bash
  # Update all submodules
  git submodule update --init --recursive

  # If you need to force update submodules
  git submodule update --init --recursive --force
  ```
- **Brave MCP Server**: If the Brave MCP server fails to start:
  - Ensure Node.js and npm are installed
  - Check that all dependencies are installed in the `brave_mcp_search` directory
  - Verify the `BRAVE_API_KEY` is set correctly in your environment variables

## Contributing

Contributions are welcome! Please open an issue to discuss your ideas or submit a pull request.

## License

MIT

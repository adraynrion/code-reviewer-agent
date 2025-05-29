# Tech Context

This document outlines the technologies, development setup, and technical constraints relevant to the AI Code Review Agent project.

## Technologies Used
- Python 3.8+ as the primary programming language
- Model Context Protocol (MCP) for modular architecture
- Vector database (Supabase) for documentation storage
- Langfuse for monitoring and analytics
- GitHub and GitLab APIs for repository interactions

## Development Setup
- Python virtual environment (.venv)
- Required Python dependencies listed in requirements.txt
- Node.js 16+ and npm for MCP servers

## Technical Constraints
- Compatibility with both GitHub and GitLab platforms
- Support for multiple MCP servers for different tasks

## Dependencies
- Python packages: listed in requirements.txt
- MCP servers: @modelcontextprotocol/server-brave-search, @modelcontextprotocol/server-filesystem, @modelcontextprotocol/server-github, @modelcontextprotocol/server-gitlab

## Tool Usage Patterns
- Primary Agent coordinates the review process
- Specialized agents handle specific tasks
- Use of environment variables for configuration

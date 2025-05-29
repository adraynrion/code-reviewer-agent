# System Patterns

This document outlines the key technical decisions, design patterns, and component relationships in the AI Code Review Agent project.

## System Architecture
- Modular architecture using Model Context Protocol (MCP)
- Multiple specialized agents for different tasks:
  - Repository Agent for Git operations
  - Filesystem Agent for local file interactions
  - Reviewer Agent for code analysis
  - Crawler Agent for documentation processing

## Key Technical Decisions
- Use of MCP for modularity and extensibility
- Integration with vector database for documentation storage
- Langfuse integration for observability and monitoring

## Design Patterns
- Agent-based architecture for task specialization
- Environment-based configuration for flexibility

## Component Relationships
- Primary Agent coordinates the review process
- Specialized agents handle specific tasks
- Vector database stores processed documentation

## Critical Implementation Paths
- Code review process flow
- Documentation crawling and storage mechanism
- Integration with GitHub and GitLab APIs

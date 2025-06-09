#!/usr/bin/env python3
"""Main entry point for the code review agent."""

import asyncio

from code_reviewer_agent.services.code_reviewer import main as code_reviewer_main

if __name__ == "__main__":
    asyncio.run(code_reviewer_main())

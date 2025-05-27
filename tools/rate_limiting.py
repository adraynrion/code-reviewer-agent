"""Rate limiting utilities for the code review agent."""

import asyncio
import time
from typing import Optional, Any, List, Dict

from pydantic_ai import RunContext
from models.deps import ReviewDeps
from .utils import log_error

class TokenBucket:
    """Token bucket implementation for rate limiting."""
    
    def __init__(self, tokens: int, refill_rate: float):
        """
        Initialize the token bucket.
        
        Args:
            tokens: Maximum number of tokens the bucket can hold
            refill_rate: Number of tokens to add per second
        """
        self.tokens = tokens
        self.capacity = tokens
        self.refill_rate = refill_rate  # tokens per second
        self.last_update = time.time()
        self.lock = asyncio.Lock()
    
    async def consume(self, tokens: int) -> float:
        """
        Consume tokens, returns the time to wait if rate limited.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            Time to wait in seconds if rate limited, 0 otherwise
        """
        async with self.lock:
            now = time.time()
            time_passed = now - self.last_update
            
            # Refill tokens based on time passed
            self.tokens = min(
                self.capacity,
                self.tokens + time_passed * self.refill_rate
            )
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return 0.0
            
            # Calculate time to wait for enough tokens
            tokens_needed = tokens - self.tokens
            wait_time = tokens_needed / self.refill_rate
            
            # Update tokens to 0 since we're going to wait
            self.tokens = 0
            
            return wait_time
    
    async def wait_for_tokens(self, tokens: int) -> None:
        """
        Wait until we have enough tokens available.
        
        Args:
            tokens: Number of tokens to wait for
        """
        while True:
            wait_time = await self.consume(tokens)
            if wait_time <= 0:
                break
            await asyncio.sleep(wait_time)

# Global rate limiter for LLM API calls
llm_rate_limiter = TokenBucket(tokens=100, refill_rate=1.0)  # 100 tokens, refills at 1 token/second

async def process_file_with_retry(
    context: RunContext[ReviewDeps],
    file_content: str,
    custom_instructions: str,
    best_practices: str,
    max_retries: int = 3,
    initial_delay: float = 1.0
) -> Optional[List[Dict[str, Any]]]:
    """
    Process a file with retry logic for rate limits.
    
    Args:
        context: The dependency injection container
        file_content: Content of the file to process
        custom_instructions: Custom instructions for the code review
        best_practices: Best practices to consider during review
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        
    Returns:
        List of review comments or None if all retries failed
    """
    delay = initial_delay
    
    for attempt in range(max_retries):
        try:
            # Wait for rate limiter
            await llm_rate_limiter.wait_for_tokens(1)
            
            # Process the file
            comments = await analyze_with_llm(
                context=context,
                diff_content=file_content,
                custom_instructions=custom_instructions,
                best_practices=best_practices
            )
            return comments
            
        except Exception as e:
            if attempt == max_retries - 1:
                log_error(f"Failed to process file after {max_retries} attempts", exc_info=e)
                return None
                
            # Exponential backoff
            await asyncio.sleep(delay)
            delay = min(delay * 2, 60)  # Cap at 60 seconds

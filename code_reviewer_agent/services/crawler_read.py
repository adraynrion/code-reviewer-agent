"""Web crawler service for the code review agent."""

from typing import Any, Dict, List

import nest_asyncio
from openai import OpenAI

from code_reviewer_agent.config.config import config
from code_reviewer_agent.models.base_agent import get_supabase
from code_reviewer_agent.utils.rich_utils import (
    print_error,
    print_info,
    print_section,
    print_success,
    print_warning,
)

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Initialize OpenAI client
openai_client = OpenAI()
# Initialize Supabase client
supabase_client = get_supabase()


async def search_documents(
    query: str, match_threshold: float = 0.8
) -> List[Dict[str, Any]]:
    """Search for documents chunks similar to the query using embeddings.

    Args:
        query: The search query string
        match_threshold: Similarity threshold for document matching (0-1)

    Returns:
        List of matching document chunks with their metadata

    Raises:
        ValueError: If the response from Supabase is not in the expected format

    """
    try:
        print_info(f"Generating embeddings for query: {query}")
        embeddings_response = openai_client.embeddings.create(
            input=query, model=config.crawler.embedding_model
        )
        embedding = embeddings_response.data[0].embedding

        print_info(f"Searching documents with threshold: {match_threshold}")
        response = supabase_client.rpc(
            "match_documents",
            {"query_embedding": embedding, "match_threshold": match_threshold},
        ).execute()

        if not hasattr(response, "data"):
            print_error("Unexpected response format from Supabase")
            raise ValueError("Unexpected response format from Supabase")

        results = [dict(item) for item in response.data]
        print_success(f"Found {len(results)} matching document chunks(s)")

        if results and config.logging.debug:
            print_section("Top match:")
            print_info(f"  Content: {results[0].get('content', '')[:200]}...")
            print_info(f"  Similarity: {results[0].get('similarity', 0):.4f}")

        return results

    except Exception as e:
        print_error(f"Error searching documents: {str(e)}")
        print_warning("Search failed, proceeding with empty results")
        return []

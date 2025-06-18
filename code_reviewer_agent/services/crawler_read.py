from openai import OpenAI

from code_reviewer_agent.models.base_types import (
    ConfigArgs,
    CrawledDocument,
    CrawledDocuments,
)
from code_reviewer_agent.utils.rich_utils import (
    print_error,
    print_info,
    print_section,
    print_success,
    print_warning,
)
from supabase import Client as SupabaseClient


class CrawlerReader:
    def __init__(self, args: ConfigArgs) -> None:
        self._openai_client = OpenAI()
        self.supabase_client = SupabaseClient(
            supabase_url=str(args.get("supabase_url", "")),
            supabase_key=str(args.get("supabase_key", "")),
        )
        self.embedding_model = str(args.get("embedding_model", ""))
        self.debug = bool(args.get("debug", False))

    def search_documents(
        self, query: str, match_threshold: float = 0.8
    ) -> CrawledDocuments:
        """Search for documents similar to the query using vector embeddings.

        Args:
            query: The search query text
            match_threshold: The similarity threshold (0-1) for matching documents

        Returns:
            List of matching document chunks with their content and similarity scores

        """
        try:
            print_info(f"Generating embeddings for query: {query}")
            embeddings_response = self._openai_client.embeddings.create(
                input=query, model=self.embedding_model
            )
            embedding = embeddings_response.data[0].embedding

            print_info(f"Searching documents with threshold: {match_threshold}")
            response = self.supabase_client.rpc(
                "match_documents",
                {
                    "query_embedding": embedding,
                    "match_threshold": match_threshold,
                },
            ).execute()

            if not hasattr(response, "data"):
                raise ValueError("Unexpected response format from Supabase")

            results: list[CrawledDocument] = [
                CrawledDocument(**item) for item in response.data
            ]
            print_success(f"Found {len(results)} matching document chunks(s)")

            if self.debug:
                for i, result in enumerate(results):
                    print_section(f"Match {i + 1}")
                    print_info(f"  Content: {result.get('content', '')}")
                    print_info(f"  Similarity: {result.get('similarity', 0):.4f}")

            return CrawledDocuments(results)

        except Exception as e:
            print_error(f"Error searching documents: {str(e)}")
            print_warning("Search failed, proceeding with empty results")
            return CrawledDocuments()

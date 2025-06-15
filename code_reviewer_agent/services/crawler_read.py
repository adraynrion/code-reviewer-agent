from openai import OpenAI
from supabase._sync.client import SyncClient

from code_reviewer_agent.models.crawler_agents import ConfigArgs, CrawledDocuments
from code_reviewer_agent.utils.rich_utils import (
    print_error,
    print_info,
    print_section,
    print_success,
    print_warning,
)


class CrawlerReader:
    _openai_client: OpenAI
    supabase_client: SyncClient
    embedding_model: str
    debug: bool

    def __init__(self, args: ConfigArgs) -> None:
        self._openai_client = args.get("openai_client")
        self.supabase_client = args.get("supabase_client")
        self.embedding_model = args.get("embedding_model")
        self.debug = args.get("debug")

    def search_documents(
        self, query: str, match_threshold: float = 0.8
    ) -> CrawledDocuments:
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

            results = [dict(item) for item in response.data]
            print_success(f"Found {len(results)} matching document chunks(s)")

            if self.debug:
                for i, result in enumerate(results):
                    print_section(f"Match {i + 1}")
                    print_info(f"  Content: {result.get('content', '')}")
                    print_info(f"  Similarity: {result.get('similarity', 0):.4f}")

            return results

        except Exception as e:
            print_error(f"Error searching documents: {str(e)}")
            print_warning("Search failed, proceeding with empty results")
            return []

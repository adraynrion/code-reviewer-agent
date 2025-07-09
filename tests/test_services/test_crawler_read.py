from unittest.mock import Mock, patch

from code_reviewer_agent.models.base_types import ConfigArgs, CrawledDocuments
from code_reviewer_agent.services.crawler_read import CrawlerReader


class TestCrawlerReader:
    """Tests for CrawlerReader class."""

    def test_initialization(self) -> None:
        """Test CrawlerReader initialization."""
        args = ConfigArgs(
            {
                "supabase_url": "https://project.supabase.co",
                "supabase_key": "key123",
                "embedding_model": "text-embedding-3-small",
                "debug": True,
            }
        )

        with patch("code_reviewer_agent.services.crawler_read.OpenAI") as mock_openai:
            with patch(
                "code_reviewer_agent.services.crawler_read.SupabaseClient"
            ) as mock_supabase:
                reader = CrawlerReader(args)

                assert reader.embedding_model == "text-embedding-3-small"
                assert reader.debug is True
                mock_openai.assert_called_once()
                mock_supabase.assert_called_once_with(
                    supabase_url="https://project.supabase.co", supabase_key="key123"
                )

    def test_initialization_with_defaults(self) -> None:
        """Test CrawlerReader initialization with default values."""
        args = ConfigArgs({})

        with patch("code_reviewer_agent.services.crawler_read.OpenAI"):
            with patch("code_reviewer_agent.services.crawler_read.SupabaseClient"):
                reader = CrawlerReader(args)

                assert reader.embedding_model == ""
                assert reader.debug is False

    @patch("code_reviewer_agent.services.crawler_read.print_info")
    @patch("code_reviewer_agent.services.crawler_read.print_success")
    def test_search_documents_success(
        self, mock_print_success, mock_print_info
    ) -> None:
        """Test successful document search."""
        args = ConfigArgs(
            {
                "supabase_url": "https://project.supabase.co",
                "supabase_key": "key123",
                "embedding_model": "text-embedding-3-small",
                "debug": False,
            }
        )

        # Mock OpenAI client
        mock_embeddings_response = Mock()
        mock_embeddings_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]

        mock_openai_client = Mock()
        mock_openai_client.embeddings.create.return_value = mock_embeddings_response

        # Mock Supabase client
        mock_supabase_response = Mock()
        mock_supabase_response.data = [
            {
                "content": "Test document 1",
                "similarity": 0.9,
                "url": "http://example.com/1",
            },
            {
                "content": "Test document 2",
                "similarity": 0.85,
                "url": "http://example.com/2",
            },
        ]

        mock_rpc = Mock()
        mock_rpc.execute.return_value = mock_supabase_response

        mock_supabase_client = Mock()
        mock_supabase_client.rpc.return_value = mock_rpc

        with patch(
            "code_reviewer_agent.services.crawler_read.OpenAI",
            return_value=mock_openai_client,
        ):
            with patch(
                "code_reviewer_agent.services.crawler_read.SupabaseClient",
                return_value=mock_supabase_client,
            ):
                reader = CrawlerReader(args)
                results = reader.search_documents("test query", 0.8)

                # Verify embeddings call
                mock_openai_client.embeddings.create.assert_called_once_with(
                    input="test query", model="text-embedding-3-small"
                )

                # Verify Supabase call
                mock_supabase_client.rpc.assert_called_once_with(
                    "match_documents",
                    {
                        "query_embedding": [0.1, 0.2, 0.3],
                        "match_threshold": 0.8,
                    },
                )

                # Verify results
                assert isinstance(results, CrawledDocuments)
                assert len(results) == 2

                # Verify print calls
                mock_print_info.assert_any_call(
                    "Generating embeddings for query: test query"
                )
                mock_print_info.assert_any_call(
                    "Searching documents with threshold: 0.8"
                )
                mock_print_success.assert_called_once_with(
                    "Found 2 matching document chunks(s)"
                )

    @patch("code_reviewer_agent.services.crawler_read.print_info")
    @patch("code_reviewer_agent.services.crawler_read.print_success")
    @patch("code_reviewer_agent.services.crawler_read.print_section")
    def test_search_documents_debug_mode(
        self, mock_print_section, mock_print_success, mock_print_info
    ) -> None:
        """Test document search in debug mode."""
        args = ConfigArgs(
            {
                "supabase_url": "https://project.supabase.co",
                "supabase_key": "key123",
                "embedding_model": "text-embedding-3-small",
                "debug": True,
            }
        )

        # Mock OpenAI client
        mock_embeddings_response = Mock()
        mock_embeddings_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]

        mock_openai_client = Mock()
        mock_openai_client.embeddings.create.return_value = mock_embeddings_response

        # Mock Supabase client
        mock_supabase_response = Mock()
        mock_supabase_response.data = [
            {"content": "Test document", "similarity": 0.9, "url": "http://example.com"}
        ]

        mock_rpc = Mock()
        mock_rpc.execute.return_value = mock_supabase_response

        mock_supabase_client = Mock()
        mock_supabase_client.rpc.return_value = mock_rpc

        with patch(
            "code_reviewer_agent.services.crawler_read.OpenAI",
            return_value=mock_openai_client,
        ):
            with patch(
                "code_reviewer_agent.services.crawler_read.SupabaseClient",
                return_value=mock_supabase_client,
            ):
                reader = CrawlerReader(args)
                results = reader.search_documents("test query")

                # Verify debug output
                mock_print_section.assert_called_once_with("Match 1")
                assert mock_print_info.call_count >= 4  # 2 for regular, 2 for debug

    @patch("code_reviewer_agent.services.crawler_read.print_error")
    @patch("code_reviewer_agent.services.crawler_read.print_warning")
    def test_search_documents_invalid_response(
        self, mock_print_warning, mock_print_error
    ) -> None:
        """Test document search with invalid Supabase response."""
        args = ConfigArgs(
            {
                "supabase_url": "https://project.supabase.co",
                "supabase_key": "key123",
                "embedding_model": "text-embedding-3-small",
            }
        )

        # Mock OpenAI client
        mock_embeddings_response = Mock()
        mock_embeddings_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]

        mock_openai_client = Mock()
        mock_openai_client.embeddings.create.return_value = mock_embeddings_response

        # Mock Supabase client with invalid response
        mock_supabase_response = Mock()
        del mock_supabase_response.data  # Remove data attribute

        mock_rpc = Mock()
        mock_rpc.execute.return_value = mock_supabase_response

        mock_supabase_client = Mock()
        mock_supabase_client.rpc.return_value = mock_rpc

        with patch(
            "code_reviewer_agent.services.crawler_read.OpenAI",
            return_value=mock_openai_client,
        ):
            with patch(
                "code_reviewer_agent.services.crawler_read.SupabaseClient",
                return_value=mock_supabase_client,
            ):
                reader = CrawlerReader(args)
                results = reader.search_documents("test query")

                # Should return empty results on error
                assert isinstance(results, CrawledDocuments)
                assert len(results) == 0

                # Verify error handling
                mock_print_error.assert_called_once()
                mock_print_warning.assert_called_once_with(
                    "Search failed, proceeding with empty results"
                )

    @patch("code_reviewer_agent.services.crawler_read.print_error")
    @patch("code_reviewer_agent.services.crawler_read.print_warning")
    def test_search_documents_openai_exception(
        self, mock_print_warning, mock_print_error
    ) -> None:
        """Test document search with OpenAI exception."""
        args = ConfigArgs(
            {
                "supabase_url": "https://project.supabase.co",
                "supabase_key": "key123",
                "embedding_model": "text-embedding-3-small",
            }
        )

        # Mock OpenAI client to raise exception
        mock_openai_client = Mock()
        mock_openai_client.embeddings.create.side_effect = Exception("OpenAI API error")

        with patch(
            "code_reviewer_agent.services.crawler_read.OpenAI",
            return_value=mock_openai_client,
        ):
            with patch("code_reviewer_agent.services.crawler_read.SupabaseClient"):
                reader = CrawlerReader(args)
                results = reader.search_documents("test query")

                # Should return empty results on error
                assert isinstance(results, CrawledDocuments)
                assert len(results) == 0

                # Verify error handling
                mock_print_error.assert_called_once()
                mock_print_warning.assert_called_once_with(
                    "Search failed, proceeding with empty results"
                )

    @patch("code_reviewer_agent.services.crawler_read.print_error")
    @patch("code_reviewer_agent.services.crawler_read.print_warning")
    def test_search_documents_supabase_exception(
        self, mock_print_warning, mock_print_error
    ) -> None:
        """Test document search with Supabase exception."""
        args = ConfigArgs(
            {
                "supabase_url": "https://project.supabase.co",
                "supabase_key": "key123",
                "embedding_model": "text-embedding-3-small",
            }
        )

        # Mock OpenAI client
        mock_embeddings_response = Mock()
        mock_embeddings_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]

        mock_openai_client = Mock()
        mock_openai_client.embeddings.create.return_value = mock_embeddings_response

        # Mock Supabase client to raise exception
        mock_supabase_client = Mock()
        mock_supabase_client.rpc.side_effect = Exception("Supabase connection error")

        with patch(
            "code_reviewer_agent.services.crawler_read.OpenAI",
            return_value=mock_openai_client,
        ):
            with patch(
                "code_reviewer_agent.services.crawler_read.SupabaseClient",
                return_value=mock_supabase_client,
            ):
                reader = CrawlerReader(args)
                results = reader.search_documents("test query")

                # Should return empty results on error
                assert isinstance(results, CrawledDocuments)
                assert len(results) == 0

                # Verify error handling
                mock_print_error.assert_called_once()
                mock_print_warning.assert_called_once_with(
                    "Search failed, proceeding with empty results"
                )

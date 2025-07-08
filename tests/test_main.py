from unittest.mock import AsyncMock, patch

from click.testing import CliRunner

from code_reviewer_agent.__main__ import cli


class TestMainCLI:
    """Tests for the main CLI interface."""

    def test_cli_help(self) -> None:
        """Test CLI help command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Code Reviewer Agent" in result.output
        assert "AI-powered code review assistant" in result.output

    def test_review_command_help(self) -> None:
        """Test review command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["review", "--help"])

        assert result.exit_code == 0
        assert "Run code review" in result.output
        assert "--platform" in result.output
        assert "--repository" in result.output

    def test_crawl_command_help(self) -> None:
        """Test crawl command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["crawl", "--help"])

        assert result.exit_code == 0
        assert "Run the web crawler" in result.output
        assert "--max-pages" in result.output
        assert "--max-depth" in result.output

    @patch("code_reviewer_agent.__main__.asyncio.run")
    @patch("code_reviewer_agent.__main__.CodeReviewService")
    def test_review_command_execution(self, mock_service, mock_asyncio) -> None:
        """Test review command execution."""
        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "review",
                "--platform",
                "github",
                "--repository",
                "owner/repo",
                "--id",
                "123",
            ],
        )

        assert result.exit_code == 0
        mock_service.assert_called_once()
        mock_asyncio.assert_called_once()

    @patch("code_reviewer_agent.__main__.asyncio.run")
    @patch("code_reviewer_agent.services.crawler.CrawlService")
    def test_crawl_command_execution(self, mock_service, mock_asyncio) -> None:
        """Test crawl command execution."""
        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance

        runner = CliRunner()
        result = runner.invoke(cli, ["crawl", "https://example.com"])

        assert result.exit_code == 0
        mock_service.assert_called_once()
        mock_asyncio.assert_called_once()

    @patch("code_reviewer_agent.__main__.asyncio.run")
    @patch("code_reviewer_agent.services.crawler.CrawlService")
    def test_crawl_command_with_options(self, mock_service, mock_asyncio) -> None:
        """Test crawl command with various options."""
        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "crawl",
                "https://example.com",
                "--max-pages",
                "10",
                "--max-depth",
                "5",
                "--concurrent-tasks",
                "2",
                "--extraction-type",
                "block",
                "--chunk-token-threshold",
                "500",
                "--overlap-rate",
                "0.2",
                "--temperature",
                "0.5",
                "--max-tokens",
                "1000",
                "--no-headless",
                "--locale",
                "fr-FR",
                "--timezone",
                "Europe/Paris",
                "--keywords",
                "test",
                "--keywords",
                "example",
                "--keyword-weight",
                "0.8",
            ],
        )

        assert result.exit_code == 0
        mock_service.assert_called_once()

        # Check that keywords were converted to list
        call_args = mock_service.call_args[1]
        assert call_args["keywords"] == ["test", "example"]
        assert call_args["max_pages"] == 10
        assert call_args["headless"] is False

    def test_crawl_multiple_urls(self) -> None:
        """Test crawl command with multiple URLs."""
        with patch("code_reviewer_agent.__main__.asyncio.run") as mock_asyncio:
            with patch(
                "code_reviewer_agent.services.crawler.CrawlService"
            ) as mock_service:
                mock_service_instance = AsyncMock()
                mock_service.return_value = mock_service_instance

                runner = CliRunner()
                result = runner.invoke(
                    cli, ["crawl", "https://example.com", "https://example.org"]
                )

                assert result.exit_code == 0
                call_args = mock_service.call_args[1]
                assert call_args["urls"] == (
                    "https://example.com",
                    "https://example.org",
                )

    def test_review_command_missing_args(self) -> None:
        """Test review command with missing required arguments."""
        runner = CliRunner()
        result = runner.invoke(cli, ["review"])

        # Should still work as arguments are optional with defaults from env/config
        assert result.exit_code == 0

    def test_crawl_command_missing_urls(self) -> None:
        """Test crawl command with missing URLs."""
        runner = CliRunner()
        result = runner.invoke(cli, ["crawl"])

        assert result.exit_code != 0
        assert "Missing argument" in result.output

    def test_invalid_command(self) -> None:
        """Test invalid command."""
        runner = CliRunner()
        result = runner.invoke(cli, ["invalid"])

        assert result.exit_code != 0
        assert "No such command" in result.output

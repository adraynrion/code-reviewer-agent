from pathlib import Path
from unittest.mock import patch

from code_reviewer_agent.config.config import Config
from code_reviewer_agent.models.reviewer_agent import InstructionPath, ReviewerAgent


class TestInstructionPath:
    """Test InstructionPath class for loading instruction files."""

    def test_valid_instruction_directory(self, temp_config_dir: Path) -> None:
        """Test loading from valid instruction directory."""
        # Create instruction directory with files
        instruction_dir = temp_config_dir / "instructions"
        instruction_dir.mkdir()

        # Create test instruction files
        (instruction_dir / "instruction1.txt").write_text("First instruction")
        (instruction_dir / "instruction2.txt").write_text("Second instruction")

        # Test loading
        instruction_path = InstructionPath(str(instruction_dir))
        instructions = list(instruction_path)

        assert len(instructions) == 2
        assert "First instruction" in instructions
        assert "Second instruction" in instructions

    def test_nonexistent_directory(self) -> None:
        """Test behavior with non-existent directory."""
        instruction_path = InstructionPath("/nonexistent/path")
        instructions = list(instruction_path)

        # Should return empty list when directory doesn't exist
        assert len(instructions) == 0

    def test_empty_directory(self, temp_config_dir: Path) -> None:
        """Test behavior with empty directory."""
        empty_dir = temp_config_dir / "empty"
        empty_dir.mkdir()

        instruction_path = InstructionPath(str(empty_dir))
        instructions = list(instruction_path)

        assert len(instructions) == 0


class TestReviewerAgent:
    """Test ReviewerAgent class."""

    def test_init(self, mock_config: Config) -> None:
        """Test ReviewerAgent initialization."""
        with patch(
            "code_reviewer_agent.models.reviewer_agent.InstructionPath"
        ) as mock_instruction_path:
            mock_instruction_path.return_value = ["instruction1", "instruction2"]
            with patch.object(ReviewerAgent, "_setup_agent"):
                with patch("code_reviewer_agent.models.reviewer_agent.CrawlerReader"):
                    with patch(
                        "code_reviewer_agent.models.reviewer_agent.print_header"
                    ):
                        with patch(
                            "code_reviewer_agent.models.reviewer_agent.print_debug"
                        ):
                            with patch(
                                "code_reviewer_agent.models.reviewer_agent.print_success"
                            ):
                                agent = ReviewerAgent(mock_config)

        assert agent._config == mock_config
        assert agent._instruction_path == ["instruction1", "instruction2"]

    def test_embedding_model_property(self, mock_config: Config) -> None:
        """Test embedding_model property."""
        mock_config.schema.crawler.embedding_model = "text-embedding-3-large"

        with patch(
            "code_reviewer_agent.models.reviewer_agent.InstructionPath"
        ) as mock_instruction_path:
            mock_instruction_path.return_value = []
            with patch.object(ReviewerAgent, "_setup_agent"):
                with patch("code_reviewer_agent.models.reviewer_agent.CrawlerReader"):
                    with patch(
                        "code_reviewer_agent.models.reviewer_agent.print_header"
                    ):
                        with patch(
                            "code_reviewer_agent.models.reviewer_agent.print_debug"
                        ):
                            with patch(
                                "code_reviewer_agent.models.reviewer_agent.print_success"
                            ):
                                agent = ReviewerAgent(mock_config)

        assert agent.embedding_model == "text-embedding-3-large"

    def test_instruction_path_integration(self, mock_config: Config) -> None:
        """Test that instruction path is properly integrated."""
        with patch(
            "code_reviewer_agent.models.reviewer_agent.InstructionPath"
        ) as mock_instruction_path:
            mock_instruction_path.return_value = [
                "Instruction 1",
                "Instruction 2",
                "Instruction 3",
            ]

            with patch.object(ReviewerAgent, "_setup_agent"):
                with patch("code_reviewer_agent.models.reviewer_agent.CrawlerReader"):
                    with patch(
                        "code_reviewer_agent.models.reviewer_agent.print_header"
                    ):
                        with patch(
                            "code_reviewer_agent.models.reviewer_agent.print_debug"
                        ):
                            with patch(
                                "code_reviewer_agent.models.reviewer_agent.print_success"
                            ):
                                agent = ReviewerAgent(mock_config)

        # Test that instruction path is properly stored
        assert len(agent._instruction_path) == 3
        assert "Instruction 1" in agent._instruction_path

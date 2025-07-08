import pytest

from code_reviewer_agent.models.base_types import (
    LLM,
    ApiKey,
    BaseUrl,
    CodeDiff,
    CommitSha,
    ConfigArgs,
    CrawledDocument,
    CrawledDocuments,
    EmbeddingModel,
    Filename,
    Files,
    FilesDiff,
    FilesPath,
    FloatValidator,
    GitHubToken,
    GitLabApiUrl,
    GitLabToken,
    InstructionsPath,
    IntegerValidator,
    Label,
    Languages,
    LanguageTuple,
    ModelProvider,
    NbUrlsCrawled,
    Platform,
    PositiveFloatValidator,
    PositiveIntegerValidator,
    Repository,
    RequestId,
    StringValidator,
    SupabaseKey,
    SupabaseUrl,
    Token,
    Url,
    Urls,
)


class TestStringValidator:
    """Test the base StringValidator class."""

    def test_valid_string(self) -> None:
        """Test valid string input."""
        validator = StringValidator("test_string")
        assert validator == "test_string"
        assert isinstance(validator, str)

    def test_non_string_input(self) -> None:
        """Test non-string input raises ValueError."""
        with pytest.raises(ValueError, match="Value must be a string"):
            StringValidator(123)

        with pytest.raises(ValueError, match="Value must be a string"):
            StringValidator(None)

        with pytest.raises(ValueError, match="Value must be a string"):
            StringValidator([])

    def test_empty_string(self) -> None:
        """Test empty string raises ValueError."""
        with pytest.raises(ValueError, match="Value cannot be empty"):
            StringValidator("")

        with pytest.raises(ValueError, match="Value cannot be empty"):
            StringValidator("   ")  # Only whitespace

        with pytest.raises(ValueError, match="Value cannot be empty"):
            StringValidator("\t\n")  # Only whitespace characters

    def test_whitespace_string(self) -> None:
        """Test string with valid content and whitespace."""
        validator = StringValidator("  test  ")
        assert validator == "  test  "  # Preserves original whitespace


class TestIntegerValidator:
    """Test the base IntegerValidator class."""

    def test_valid_integer(self) -> None:
        """Test valid integer input."""
        validator = IntegerValidator(42)
        assert validator == 42
        assert isinstance(validator, int)

    def test_zero(self) -> None:
        """Test zero is valid."""
        validator = IntegerValidator(0)
        assert validator == 0

    def test_negative_integer(self) -> None:
        """Test negative integer is valid."""
        validator = IntegerValidator(-42)
        assert validator == -42

    def test_non_integer_input(self) -> None:
        """Test non-integer input raises ValueError."""
        with pytest.raises(ValueError, match="Value must be an integer"):
            IntegerValidator("123")

        with pytest.raises(ValueError, match="Value must be an integer"):
            IntegerValidator(42.5)

        with pytest.raises(ValueError, match="Value must be an integer"):
            IntegerValidator(None)


class TestPositiveIntegerValidator:
    """Test the PositiveIntegerValidator class."""

    def test_valid_positive_integer(self) -> None:
        """Test valid positive integer input."""
        validator = PositiveIntegerValidator(42)
        assert validator == 42
        assert isinstance(validator, int)

    def test_zero(self) -> None:
        """Test zero is valid (not negative)."""
        validator = PositiveIntegerValidator(0)
        assert validator == 0

    def test_negative_integer(self) -> None:
        """Test negative integer raises ValueError."""
        with pytest.raises(ValueError, match="Value must be positive"):
            PositiveIntegerValidator(-1)

        with pytest.raises(ValueError, match="Value must be positive"):
            PositiveIntegerValidator(-42)

    def test_non_integer_input(self) -> None:
        """Test non-integer input raises ValueError."""
        with pytest.raises(ValueError, match="Value must be an integer"):
            PositiveIntegerValidator("123")

        with pytest.raises(ValueError, match="Value must be an integer"):
            PositiveIntegerValidator(42.5)


class TestFloatValidator:
    """Test the base FloatValidator class."""

    def test_valid_float(self) -> None:
        """Test valid float input."""
        validator = FloatValidator(3.14)
        assert validator == 3.14
        assert isinstance(validator, float)

    def test_zero_float(self) -> None:
        """Test zero float is valid."""
        validator = FloatValidator(0.0)
        assert validator == 0.0

    def test_negative_float(self) -> None:
        """Test negative float is valid."""
        validator = FloatValidator(-3.14)
        assert validator == -3.14

    def test_non_float_input(self) -> None:
        """Test non-float input raises ValueError."""
        with pytest.raises(ValueError, match="Value must be a float"):
            FloatValidator("3.14")

        with pytest.raises(ValueError, match="Value must be a float"):
            FloatValidator(42)  # Integer is not float

        with pytest.raises(ValueError, match="Value must be a float"):
            FloatValidator(None)


class TestPositiveFloatValidator:
    """Test the PositiveFloatValidator class."""

    def test_valid_positive_float(self) -> None:
        """Test valid positive float input."""
        validator = PositiveFloatValidator(3.14)
        assert validator == 3.14
        assert isinstance(validator, float)

    def test_zero_float(self) -> None:
        """Test zero float is valid (not negative)."""
        validator = PositiveFloatValidator(0.0)
        assert validator == 0.0

    def test_negative_float(self) -> None:
        """Test negative float raises ValueError."""
        with pytest.raises(ValueError, match="Value must be positive"):
            PositiveFloatValidator(-3.14)

        with pytest.raises(ValueError, match="Value must be positive"):
            PositiveFloatValidator(-0.01)

    def test_non_float_input(self) -> None:
        """Test non-float input raises ValueError."""
        with pytest.raises(ValueError, match="Value must be a float"):
            PositiveFloatValidator("3.14")

        with pytest.raises(ValueError, match="Value must be a float"):
            PositiveFloatValidator(42)


class TestStringValidatorSubclasses:
    """Test all StringValidator subclasses."""

    @pytest.mark.parametrize(
        "validator_class",
        [
            ApiKey,
            BaseUrl,
            CommitSha,
            EmbeddingModel,
            Filename,
            GitHubToken,
            GitLabApiUrl,
            GitLabToken,
            InstructionsPath,
            Label,
            LLM,
            ModelProvider,
            Platform,
            Repository,
            SupabaseKey,
            SupabaseUrl,
            Token,
            Url,
        ],
    )
    def test_valid_string_subclasses(
        self, validator_class: type[StringValidator]
    ) -> None:
        """Test all StringValidator subclasses with valid input."""
        validator = validator_class("test_value")
        assert validator == "test_value"
        assert isinstance(validator, str)

    @pytest.mark.parametrize(
        "validator_class",
        [
            ApiKey,
            BaseUrl,
            CommitSha,
            EmbeddingModel,
            Filename,
            GitHubToken,
            GitLabApiUrl,
            GitLabToken,
            InstructionsPath,
            Label,
            LLM,
            ModelProvider,
            Platform,
            Repository,
            SupabaseKey,
            SupabaseUrl,
            Token,
            Url,
        ],
    )
    def test_empty_string_subclasses(
        self, validator_class: type[StringValidator]
    ) -> None:
        """Test all StringValidator subclasses reject empty strings."""
        with pytest.raises(ValueError, match="Value cannot be empty"):
            validator_class("")

    @pytest.mark.parametrize(
        "validator_class",
        [
            ApiKey,
            BaseUrl,
            CommitSha,
            EmbeddingModel,
            Filename,
            GitHubToken,
            GitLabApiUrl,
            GitLabToken,
            InstructionsPath,
            Label,
            LLM,
            ModelProvider,
            Platform,
            Repository,
            SupabaseKey,
            SupabaseUrl,
            Token,
            Url,
        ],
    )
    def test_non_string_subclasses(
        self, validator_class: type[StringValidator]
    ) -> None:
        """Test all StringValidator subclasses reject non-strings."""
        with pytest.raises(ValueError, match="Value must be a string"):
            validator_class(123)


class TestPositiveIntegerValidatorSubclasses:
    """Test all PositiveIntegerValidator subclasses."""

    @pytest.mark.parametrize("validator_class", [NbUrlsCrawled, RequestId])
    def test_valid_positive_integer_subclasses(
        self, validator_class: type[PositiveIntegerValidator]
    ) -> None:
        """Test all PositiveIntegerValidator subclasses with valid input."""
        validator = validator_class(42)
        assert validator == 42
        assert isinstance(validator, int)

    @pytest.mark.parametrize("validator_class", [NbUrlsCrawled, RequestId])
    def test_zero_subclasses(
        self, validator_class: type[PositiveIntegerValidator]
    ) -> None:
        """Test all PositiveIntegerValidator subclasses accept zero."""
        validator = validator_class(0)
        assert validator == 0

    @pytest.mark.parametrize("validator_class", [NbUrlsCrawled, RequestId])
    def test_negative_integer_subclasses(
        self, validator_class: type[PositiveIntegerValidator]
    ) -> None:
        """Test all PositiveIntegerValidator subclasses reject negative values."""
        with pytest.raises(ValueError, match="Value must be positive"):
            validator_class(-1)


class TestUrls:
    """Test the custom Urls validator."""

    def test_valid_urls_tuple(self) -> None:
        """Test valid URL tuple."""
        urls_tuple = ("https://example.com", "https://test.com")
        validator = Urls(urls_tuple)
        assert validator == urls_tuple
        assert isinstance(validator, tuple)

    def test_single_url(self) -> None:
        """Test single URL in tuple."""
        urls_tuple = ("https://example.com",)
        validator = Urls(urls_tuple)
        assert validator == urls_tuple

    def test_empty_urls_tuple(self) -> None:
        """Test empty URL tuple raises ValueError."""
        with pytest.raises(ValueError, match="At least one URL is required"):
            Urls(())


class TestTypeAliases:
    """Test the type alias classes."""

    def test_code_diff(self) -> None:
        """Test CodeDiff type alias."""
        test_dict = {"filename": "test.py", "patch": "test patch"}
        code_diff = CodeDiff(test_dict)
        assert code_diff == test_dict
        assert isinstance(code_diff, dict)

    def test_config_args(self) -> None:
        """Test ConfigArgs type alias."""
        test_dict = {"key": "value", "number": 42}
        config_args = ConfigArgs(test_dict)
        assert config_args == test_dict
        assert isinstance(config_args, dict)

    def test_crawled_document(self) -> None:
        """Test CrawledDocument type alias."""
        test_dict = {"url": "https://example.com", "content": "test content"}
        crawled_doc = CrawledDocument(test_dict)
        assert crawled_doc == test_dict
        assert isinstance(crawled_doc, dict)

    def test_crawled_documents(self) -> None:
        """Test CrawledDocuments type alias."""
        test_data = [
            {"url": "https://example.com", "content": "test1"},
            {"url": "https://test.com", "content": "test2"},
        ]
        test_docs = [CrawledDocument(doc) for doc in test_data]
        crawled_docs = CrawledDocuments(test_docs)
        assert crawled_docs == test_docs
        assert isinstance(crawled_docs, list)

    def test_files(self) -> None:
        """Test Files type alias."""
        test_tuple = ({"filename": "test.py"}, {"filename": "test2.py"})
        files = Files(test_tuple)
        assert files == test_tuple
        assert isinstance(files, tuple)

    def test_files_diff(self) -> None:
        """Test FilesDiff type alias."""
        test_tuple = ({"filename": "test.py", "patch": "patch1"},)
        files_diff = FilesDiff(test_tuple)
        assert files_diff == test_tuple
        assert isinstance(files_diff, tuple)

    def test_files_path(self) -> None:
        """Test FilesPath type alias."""
        test_tuple = ("path1", "path2")
        files_path = FilesPath(test_tuple)
        assert files_path == test_tuple
        assert isinstance(files_path, tuple)

    def test_languages(self) -> None:
        """Test Languages type alias."""
        test_dict = {"python": {"py", "pyx"}, "javascript": {"js", "jsx"}}
        languages = Languages(test_dict)
        assert languages == test_dict
        assert isinstance(languages, dict)

    def test_language_tuple(self) -> None:
        """Test LanguageTuple type alias."""
        test_tuple = ("python", "javascript")
        language_tuple = LanguageTuple(test_tuple)
        assert language_tuple == test_tuple
        assert isinstance(language_tuple, tuple)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_string_validator_with_unicode(self) -> None:
        """Test StringValidator with Unicode characters."""
        validator = StringValidator("测试")
        assert validator == "测试"

    def test_string_validator_with_special_chars(self) -> None:
        """Test StringValidator with special characters."""
        validator = StringValidator("test@#$%^&*()")
        assert validator == "test@#$%^&*()"

    def test_positive_integer_validator_with_large_number(self) -> None:
        """Test PositiveIntegerValidator with large numbers."""
        large_number = 999999999999999
        validator = PositiveIntegerValidator(large_number)
        assert validator == large_number

    def test_positive_float_validator_with_small_number(self) -> None:
        """Test PositiveFloatValidator with very small positive numbers."""
        small_number = 0.000001
        validator = PositiveFloatValidator(small_number)
        assert validator == small_number

    def test_urls_with_complex_urls(self) -> None:
        """Test Urls with complex URL patterns."""
        complex_urls = tuple(
            [
                "https://example.com/path?param=value&other=test",
                "ftp://files.example.com/file.txt",
                "http://localhost:8080/api/v1/test",
            ]
        )
        validator = Urls(complex_urls)
        assert validator == complex_urls

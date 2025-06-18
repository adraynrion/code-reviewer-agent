from typing import Any, Dict, List, Set, Tuple, cast


class StringValidator(str):
    def __new__(cls, value: str) -> "StringValidator":
        if not isinstance(value, str):
            raise ValueError("Value must be a string")
        if not value.strip():
            raise ValueError("Value cannot be empty")
        return super().__new__(cls, value)


class IntegerValidator(int):
    def __new__(cls, value: int) -> "IntegerValidator":
        if not isinstance(value, int):
            raise ValueError("Value must be an integer")
        return super().__new__(cls, value)


class PositiveIntegerValidator(IntegerValidator):
    def __new__(cls, value: int) -> "PositiveIntegerValidator":
        if not isinstance(value, int):
            raise ValueError("Value must be an integer")
        if value < 0:
            raise ValueError("Value must be positive")
        return cast(PositiveIntegerValidator, super().__new__(cls, value))


class FloatValidator(float):
    def __new__(cls, value: float) -> "FloatValidator":
        if not isinstance(value, float):
            raise ValueError("Value must be a float")
        return super().__new__(cls, value)


class PositiveFloatValidator(FloatValidator):
    def __new__(cls, value: float) -> "PositiveFloatValidator":
        if not isinstance(value, float):
            raise ValueError("Value must be a float")
        if value < 0:
            raise ValueError("Value must be positive")
        return cast(PositiveFloatValidator, super().__new__(cls, value))


########## StringValidator ##########


class ApiKey(StringValidator):
    pass


class BaseUrl(StringValidator):
    pass


class CommitSha(StringValidator):
    pass


class EmbeddingModel(StringValidator):
    pass


class ExtractionType(StringValidator):
    pass


class Filename(StringValidator):
    pass


class GitHubToken(StringValidator):
    pass


class GitLabApiUrl(StringValidator):
    pass


class GitLabToken(StringValidator):
    pass


class InstructionsPath(StringValidator):
    pass


class Label(StringValidator):
    pass


class LLM(StringValidator):
    pass


class Locale(StringValidator):
    def __new__(cls, value: str) -> "Locale":
        formated_value = value.lower().strip()

        from babel import Locale as BabelLocale

        try:
            BabelLocale.parse(formated_value, sep="-")
        except ValueError:
            raise ValueError(
                f"Invalid locale. Must be a valid BCP 47 language tag. Got {formated_value}"
            )

        return str.__new__(cls, value)


class ModelProvider(StringValidator):
    pass


class Platform(StringValidator):
    pass


class Repository(StringValidator):
    pass


class SupabaseKey(StringValidator):
    pass


class SupabaseUrl(StringValidator):
    pass


class Timezone(StringValidator):
    def __new__(cls, value: str) -> "Timezone":
        formated_value = value.lower().strip()

        from dateutil.tz import gettz

        if gettz(formated_value) is None:
            raise ValueError(
                f"Invalid timezone. Must be a valid timezone string. Got {formated_value}"
            )

        return str.__new__(cls, value)


class Token(StringValidator):
    pass


class Url(StringValidator):
    pass


########## PositiveIntegerValidator ##########


class ChunkTokenThreshold(PositiveIntegerValidator):
    pass


class ConcurrentTasks(PositiveIntegerValidator):
    pass


class KeywordWeight(PositiveFloatValidator):
    pass


class MaxDepth(PositiveIntegerValidator):
    pass


class MaxPages(PositiveIntegerValidator):
    pass


class MaxTokens(PositiveIntegerValidator):
    pass


class NbUrlsCrawled(PositiveIntegerValidator):
    pass


class OverlapRate(PositiveFloatValidator):
    pass


class RequestId(PositiveIntegerValidator):
    pass


class Temperature(PositiveFloatValidator):
    pass


########## Others ##########


class CodeDiff(Dict[str, Any]):
    pass


class ConfigArgs(Dict[str, Any]):
    pass


class CrawledDocument(Dict[str, Any]):
    pass


class CrawledDocuments(List[CrawledDocument]):
    pass


class Files(Tuple[Dict[str, Any]]):
    pass


class FilesDiff(Tuple[Dict[str, Any]]):
    pass


class FilesPath(Tuple[str]):
    pass


class Keywords(List[str]):
    pass


class Languages(Dict[str, Set[str]]):
    pass


class LanguageTuple(Tuple[str]):
    pass


class Urls(List[str]):
    def __new__(cls, value: List[str]) -> "Urls":
        if not value or len(value) == 0:
            raise ValueError("At least one URL is required")
        return super().__new__(cls)

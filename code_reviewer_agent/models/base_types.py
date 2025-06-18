from typing import Any, Dict, List, Set, Tuple


class StringValidator(str):
    def __new__(cls, value: str) -> "StringValidator":
        if not isinstance(value, str):
            raise ValueError("Value must be a string")
        if not value.strip():
            raise ValueError("Value cannot be empty")
        return super().__new__(cls)


class IntegerValidator(int):
    def __new__(cls, value: int) -> "IntegerValidator":
        if not isinstance(value, int):
            raise ValueError("Value must be an integer")
        return super().__new__(cls)


class PositiveIntegerValidator(IntegerValidator):
    def __new__(cls, value: int) -> "PositiveIntegerValidator":
        if not isinstance(value, int):
            raise ValueError("Value must be an integer")
        if value < 0:
            raise ValueError("Value must be positive")
        return super().__new__(cls)


class FloatValidator(float):
    def __new__(cls, value: float) -> "FloatValidator":
        if not isinstance(value, float):
            raise ValueError("Value must be a float")
        return super().__new__(cls)


class PositiveFloatValidator(FloatValidator):
    def __new__(cls, value: float) -> "PositiveFloatValidator":
        if not isinstance(value, float):
            raise ValueError("Value must be a float")
        if value < 0:
            raise ValueError("Value must be positive")
        return super().__new__(cls)


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


class Token(StringValidator):
    pass


class Url(StringValidator):
    pass


########## PositiveIntegerValidator ##########


class ChunkTokenThreshold(PositiveIntegerValidator):
    pass


class ConcurrentTasks(PositiveIntegerValidator):
    pass


class MaxDepth(PositiveIntegerValidator):
    pass


class MaxPages(PositiveIntegerValidator):
    pass


class MaxTokens(PositiveIntegerValidator):
    pass


class OverlapRate(PositiveFloatValidator):
    pass


class RequestId(PositiveIntegerValidator):
    pass


class Temperature(PositiveFloatValidator):
    pass


########## Others ##########


class Urls(List[str]):
    def __set__(self, instance, value: List[str]) -> None:
        if not value or len(value) == 0:
            raise ValueError("At least one URL is required")
        super().__set__(instance, value)


class Headless(bool):
    pass


class Files(Tuple[Dict[str, Any]]):
    pass


class FilesDiff(List[Dict[str, Any]]):
    pass


class CodeDiff(Dict[str, Any]):
    pass


class Languages(Dict[str, Set[str]]):
    pass


class ConfigArgs(Dict[str, Any]):
    pass


class CrawledDocument(Dict[str, Any]):
    pass


class CrawledDocuments(List[CrawledDocument]):
    pass

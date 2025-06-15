from code_reviewer_agent.config.config import Config
from code_reviewer_agent.models.base_agent import AiModel, AiModelType
from code_reviewer_agent.models.base_types import StringValidator


# Chunk Type validator
class Chunk(StringValidator):
    pass


# Document Type validator
class Document(StringValidator):
    pass


class ContextualRetrieval(AiModel, metaclass=AiModelType):
    def __init__(
        self, config: Config, document: Document, chunks: tuple[Chunk]
    ) -> None:
        AiModel.__init__(self, config)

        for chunk in chunks:
            if len(chunk) > len(document):
                raise ValueError("Chunk cannot be longer than document")

        self._document = document
        self._chunks = chunks

    @property
    def document(self) -> Document:
        return self._document

    @property
    def chunks(self) -> tuple[Chunk]:
        return self._chunks

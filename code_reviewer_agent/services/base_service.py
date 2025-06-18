from code_reviewer_agent.config.config import Config
from code_reviewer_agent.utils.langfuse import LangfuseModel


class BaseService:
    _config: Config
    _langfuse: LangfuseModel

    def __init__(self, config: Config) -> None:
        self._config = config
        self._langfuse = LangfuseModel(config.schema.langfuse)

    @property
    def config(self) -> Config:
        return self._config

    @property
    def langfuse(self) -> LangfuseModel:
        return self._langfuse

from code_reviewer_agent.config.config import Config
from code_reviewer_agent.models.base_types import StringValidator
from supabase import Client, create_client


# Url Type validator
class SupabaseUrl(StringValidator):
    pass


# Key Type validator
class SupabaseKey(StringValidator):
    pass


class SupabaseModel:
    """SupabaseModel singleton."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SupabaseModel, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, config: Config) -> None:
        self._url = SupabaseUrl(config.schema.supabase.url)
        self._key = SupabaseKey(config.schema.supabase.key)
        try:
            self._client = create_client(self.url, self.key)
        except Exception as e:
            raise ValueError(f"Failed to create Supabase client: {e}")

    @property
    def url(self) -> SupabaseUrl:
        return self._url

    @url.setter
    def url(self, value: SupabaseUrl) -> None:
        self._url = value

    @property
    def key(self) -> SupabaseKey:
        return self._key

    @key.setter
    def key(self, value: SupabaseKey) -> None:
        self._key = value

    @property
    def client(self) -> Client:
        return self._client

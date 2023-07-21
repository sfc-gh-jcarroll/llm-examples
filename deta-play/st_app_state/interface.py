from abc import ABC, abstractmethod
from typing import Union


class StateBackend(ABC):
    @abstractmethod
    def get(self, key: str, default=None) -> Union[dict, None]:
        "Get the dict at key, or return a default value"
        raise NotImplemented

    @abstractmethod
    def put(self, key: str, data: dict) -> None:
        "Put data at key, fully replacing any existing contents"
        raise NotImplemented

    @abstractmethod
    def update(self, key: str, data: dict) -> None:
        "Given a key to an existing dict, update (merge) the dict at key with the k:v pairs in data"
        raise NotImplemented

from abc import ABC, abstractmethod


class Provider(ABC):

    name = "provider"

    @abstractmethod
    def generate(self, prompt: str):
        pass

    @abstractmethod
    def health(self):
        pass

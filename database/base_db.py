from abc import ABC, abstractmethod


class BaseDatabase(ABC):

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def execute(self, query, params=()):
        pass

    @abstractmethod
    def fetchall(self, query, params=()):
        pass

    @abstractmethod
    def fetchone(self, query, params=()):
        pass

    @abstractmethod
    def close(self):
        pass
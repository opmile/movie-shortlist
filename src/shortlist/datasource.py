"""Repository pattern — fonte de dados plugável.

carregar() devolve list[dict] (NÃO list[Filme]): a fonte não conhece subclasses;
quem decide é o FilmeFactory. Desacopla formato/origem, não distribuição.
"""
import csv
import json
from abc import ABC, abstractmethod


class DataSource(ABC):
    @abstractmethod
    def carregar(self) -> list[dict]:
        ...


class CSVDataSource(DataSource):
    def __init__(self, path: str):
        self.path = path

    def carregar(self) -> list[dict]:
        with open(self.path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))


class JSONDataSource(DataSource):
    def __init__(self, path: str):
        self.path = path

    def carregar(self) -> list[dict]:
        with open(self.path, encoding="utf-8") as f:
            return json.load(f)

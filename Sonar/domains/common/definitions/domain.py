from abc import ABC, abstractmethod
from typing import Set
from dataclasses import dataclass


@dataclass(frozen=True)
class TrxParty:

    name: str
    id_column_name: str


class DomainDefinition(ABC):

    @property
    @abstractmethod
    def etl_entities(self) -> Set[str]:
        pass

    @property
    @abstractmethod
    def investigated_entities(self) -> Set[str]:
        pass

    @property
    @abstractmethod
    def cadences(self) -> Set[str]:
        pass

    @property
    @abstractmethod
    def trx_date_column_name(self) -> str:
        pass

    @property
    @abstractmethod
    def initiating_party(self) -> TrxParty:
        pass

    @property
    @abstractmethod
    def counterparty(self) -> TrxParty:
        pass


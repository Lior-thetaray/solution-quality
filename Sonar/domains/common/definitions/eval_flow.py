from common.definitions.domain import DomainDefinition
from abc import ABC, abstractmethod


class EvaluationFlowDefinition(ABC):

    @abstractmethod
    def __init__(self, domain_definition: DomainDefinition):
        self.domain_definition = domain_definition

    @property
    @abstractmethod
    def entity(self) -> str:
        pass

    @property
    @abstractmethod
    def cadence(self) -> str:
        pass

    @property
    @abstractmethod
    def eval_flow_id(self) -> str:
        pass

    @property
    @abstractmethod
    def date_column_name(self) -> str:
        pass

    @property
    @abstractmethod
    def investigated_entity_id_column_name(self) -> str:
        pass

    @property
    def train_dataset_identifier(self) -> str:
        return f'{self.entity}_{self.cadence}_train'

    @property
    def analysis_dataset_identifier(self) -> str:
        return f'{self.entity}_{self.cadence}'

    @property
    def feature_extraction_model_name(self) -> str:
        return f'{self.entity}_{self.cadence}_fe'

    @property
    def detection_model_name(self) -> str:
        return f'{self.entity}_{self.cadence}_ad'

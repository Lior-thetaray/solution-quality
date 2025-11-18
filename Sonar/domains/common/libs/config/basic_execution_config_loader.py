import os
import json

from common.definitions.domain import DomainDefinition
from common.libs.config.loader import load_yaml
from common.libs.context_utils import is_run_triggered_from_airflow
from common.factory.domain_definition import get_domain_definition

from thetaray.common.settings import Settings

from typing import Dict

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BasicExecutionConfig:

    domain: str
    entity: str
    stage: str
    cadence: str = None
    spark_conf: Dict[str, str] = field(default_factory=dict)

    supported_stages = ['etl', 'data_analysis', 'data_exploration']

    def __post_init__(self):
        self._validate_domain()
        self._validate_entity()
        self._validate_cadence()

    def _validate_domain(self):
        self._validate_missing_param('domain', self.domain)
        available_domains = os.listdir(Settings.DOMAINS_PATH)
        if self.domain not in available_domains:
            raise ValueError(f'domain is invalid. A directory under ../domains is expected with domain {self.domain}. \nCurrent defined domains are {available_domains}')

    def _validate_stage(self):
        self._validate_missing_param('stage', self.stage)
        if self.stage.lower() not in self.supported_stages:
            raise ValueError(f'Unsupported stage {self.stage}. Supported stages are {self.supported_stages}')

    def _validate_entity(self):
        if self.stage.lower() == 'data_exploration':
            self._validate_missing_param('entity', self.entity)
        domain_definition: DomainDefinition = get_domain_definition(self.domain)
        if self.entity:
            if self.stage.lower() == 'etl' and self.entity not in domain_definition.etl_entities:
                raise ValueError(f'entity {self.entity} is not supported in domain {self.domain} in {self.stage} stage. \nSupported entities are {domain_definition.etl_entities}')
            elif self.stage.lower() == 'data_analysis' and self.entity not in domain_definition.investigated_entities:
                raise ValueError(f'entity {self.entity} is not supported in domain {self.domain} in {self.stage} stage. \nSupported entities are {domain_definition.investigated_entities}')

    def _validate_cadence(self):
        if self.stage.lower() == 'data_analysis':
            self._validate_missing_param('cadence', self.cadence)
        if self.cadence:
            domain_definition: DomainDefinition = get_domain_definition(self.domain)
            if self.cadence not in domain_definition.cadences:
                raise ValueError(f'cadence {self.cadence} is not supported in domain {self.domain}. \nSupported cadences are {domain_definition.cadences}')

    def _validate_missing_param(self, param_name: str, param_value: str) -> None:
        if param_value is None:
            err_msg = f'{param_name} is missing'
            if is_run_triggered_from_airflow():
                raise ValueError(f'{err_msg}. Please configure it in the dag file params')
            else:
                raise ValueError(f'{err_msg}. Please configure it in ../common/config/ext/dev_execution_config.yaml')


class DevBasicExecutionConfig(BasicExecutionConfig):

    def __init__(self):
        config = load_yaml(f'{Settings.DOMAINS_PATH}/common/config/ext/dev_execution_config.yaml')
        super().__init__(**config)



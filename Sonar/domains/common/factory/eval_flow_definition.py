import importlib

from common.definitions.eval_flow import EvaluationFlowDefinition
from common.libs.config.basic_execution_config_loader import BasicExecutionConfig
from common.libs.class_instance_loader import load_class_from_file


def get_evaluation_flow_definition(basic_execution_config: BasicExecutionConfig) -> EvaluationFlowDefinition:
    domain = basic_execution_config.domain
    entity = basic_execution_config.entity
    cadence = basic_execution_config.cadence
    module = importlib.import_module(f'{domain}.definitions.{entity}_{cadence}')
    return load_class_from_file(module.__name__, module.__file__)()

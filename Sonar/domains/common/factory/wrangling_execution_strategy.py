import importlib
from common.libs.class_instance_loader import load_class_from_file

from common.libs.config.basic_execution_config_loader import BasicExecutionConfig
from common.notebook_utils.wrangling.wrangling_execution_strategy import WranglingExecutionStrategy
from common.factory.domain_definition import get_domain_definition


def get_wrangling_execution_strategy(basic_execution_config: BasicExecutionConfig, config: dict, features: list,) -> WranglingExecutionStrategy:
    domain = basic_execution_config.domain
    cadence = basic_execution_config.cadence

    domain_definition = get_domain_definition(domain)
    trx_date_column_name = domain_definition.trx_date_column_name

    mode = 'analysis' if config['bau'] else 'train'
    module = importlib.import_module(f'common.notebook_utils.wrangling.{cadence}_{mode}')
    return load_class_from_file(module.__name__, module.__file__)(config, trx_date_column_name, features)

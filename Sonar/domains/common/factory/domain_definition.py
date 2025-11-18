import importlib

from common.definitions.domain import DomainDefinition
from common.libs.class_instance_loader import load_class_from_file


def get_domain_definition(domain: str) -> DomainDefinition:
    module = importlib.import_module(f'{domain}.definitions.domain')
    return load_class_from_file(module.__name__, module.__file__)()

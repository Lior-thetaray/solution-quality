import inspect
import importlib


def load_class_from_file(module_name: str, filepath: str):
    # imports the module from the given path
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    mdl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mdl)
    classes = inspect.getmembers(mdl, inspect.isclass)
    for _, cls in classes:
        if cls.__module__ == module_name:
            return cls

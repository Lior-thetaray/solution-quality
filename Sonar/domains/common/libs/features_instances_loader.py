import glob
from pathlib import Path

from common.libs.class_instance_loader import load_class_from_file


def load_features_from_disk(path: str):
    """
    Get a list of feature classes in the given path
    """

    feature_class_instances = {}
    for filepath in glob.glob(f'{path}/*.py'):
        filename = Path(filepath).stem
        feature_class_instance = load_class_from_file(filename, filepath)()
        feature_class_instance.filepath = filepath
        if feature_class_instance.fqfn not in feature_class_instances:
            feature_class_instances[feature_class_instance.fqfn] = feature_class_instance
        else:
            existing_filepath = feature_class_instances[feature_class_instance.fqfn].filepath
            raise RuntimeError(f"2 feature files {filepath, existing_filepath} have the same identifier and version {feature_class_instance.fqfn}")
    return [feature_class_instance for feature_class_instance in feature_class_instances.values()]



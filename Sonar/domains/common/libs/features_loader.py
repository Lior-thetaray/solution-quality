from typing import Tuple

from common.libs.features_instances_loader import load_features_from_disk
import json
import re
from tabulate import tabulate

from thetaray.common.logging import logger


MANDATORY_FIELDS: Tuple[str] = ('active',)
FEATURE_VERSION_PATTERN = r'^v\d+$'


def get_features(features_loading_config, core_features_path, ext_features_path, active_only=True, effective_only=True):
    """
    Get a list of feature classes using a config object

    Parameters
    ----------
    features_loading_config: dict
        a features configuration object
    core_features_path: str
        path to the core features files
    ext_features_path: str
        path to the ext features files
    active_only: bool
        load only active features or all of them?
    effective_only: bool
        if True, core features that are being overriden by ext features will not be returned
    """

    _validate_config(features_loading_config)
    if active_only:
        features_loading_config = filter_features(features_loading_config, field='active')

    features_to_load = [(feature_identifier, _parse_feature_version(feature_version)) for feature_identifier, feature_configs in features_loading_config.items()
                        for feature_version in feature_configs.keys()]

    core_features = [feature for feature in load_features_from_disk(core_features_path)]
    for feature in core_features:
        feature.source_layer = 'core'
    ext_features = [feature for feature in load_features_from_disk(ext_features_path)]
    for feature in ext_features:
        feature.source_layer = 'ext'

    features = []
    for feature_identifier, feature_version in features_to_load:
        core_feature = next((feature for feature in core_features
                             if feature.identifier == feature_identifier and feature.version == feature_version), None)
        ext_feature = next((feature for feature in ext_features
                            if feature.identifier == feature_identifier and feature.version == feature_version), None)

        if not (core_feature or ext_feature):
            raise RuntimeError(f'No implementation found for feature with identifier {feature_identifier} and version {feature_version}'
                               f' in the following paths: {core_features_path, ext_features_path}')

        if not ext_feature:
            features.append(core_feature)
        else:
            features.append(ext_feature)
            if core_feature and not effective_only:
                features.append(core_feature)

    if effective_only:
        _validate_features_clash(features)

    logger.debug('\n ---- L O A D E D    F E A T U R E S: ---- \n')
    logger.debug(tabulate([[feature.identifier, feature.version, feature.source_layer] for feature in features],
                   headers=['identifier', 'version', 'layer']))

    return features


def _validate_config(features_loading_config):
    validate_mandatory_fields(features_loading_config)
    _validate_only_one_active_feature_version(features_loading_config)


def _validate_structure(features_loading_config):
    features_with_unexpected_structure = {}
    for feature_identifier, feature_configs in features_loading_config.items():
        if feature_configs is None:
            features_with_unexpected_structure[feature_identifier] = 'missing feature version, feature version must be in the following format: v<number>, e.g. v1, v2, v3.'
        else:
            for feature_version, feature_config in feature_configs.items():
                if not re.match(FEATURE_VERSION_PATTERN, feature_version):
                    features_with_unexpected_structure[feature_identifier] = f'feature version must be in the following format: v<number>, e.g. v1, v2, v3. given version is {feature_version}'
    if features_with_unexpected_structure:
        raise ValueError(f"Configuration of the following features is broken: \n {json.dumps(features_with_unexpected_structure, indent=4)}")


def validate_mandatory_fields(features_loading_config, mandatory_fields=()):
    mandatory_fields = MANDATORY_FIELDS + mandatory_fields
    _validate_structure(features_loading_config)
    features_with_missing_config = {}
    for feature_identifier, feature_configs in features_loading_config.items():
        for feature_version, feature_config in feature_configs.items():
            for mandatory_field in mandatory_fields:
                if mandatory_field not in feature_config:
                    features_with_missing_config.setdefault(feature_identifier, {})
                    features_with_missing_config[feature_identifier].setdefault(feature_version, {})
                    features_with_missing_config[feature_identifier][feature_version].setdefault('missing_fields', [])
                    features_with_missing_config[feature_identifier][feature_version]['missing_fields'].append(mandatory_field)

    if features_with_missing_config:
        raise ValueError(f"Configuration of mandatory fields is missing for the following features: \n {json.dumps(features_with_missing_config, indent=4)}")


def _validate_only_one_active_feature_version(features_loading_config):
    features_with_multiple_active_versions = {}
    for feature_identifier, feature_configs in features_loading_config.items():
        feature_active_versions = [feature_version for feature_version, feature_config in feature_configs.items()
                                   if feature_config['active']]
        if len(feature_active_versions) > 1:
            features_with_multiple_active_versions[feature_identifier] = feature_active_versions

    if features_with_multiple_active_versions:
        raise RuntimeError(f"Following features have more than 1 version marked as active: \n {json.dumps(features_with_multiple_active_versions, indent=4)}")


def filter_features(features_loading_config, field):
    filtered_features_loading_config = {}
    for feature_identifier, feature_configs in features_loading_config.items():
        for feature_version, feature_config in feature_configs.items():
            if feature_config[field]:
                filtered_features_loading_config.setdefault(feature_identifier, {})
                filtered_features_loading_config[feature_identifier][feature_version] = feature_config
    return filtered_features_loading_config


def _validate_features_clash(features):
    _validate_features_output_fields_clash(features)


def _validate_features_output_fields_clash(features):
    output_fields_features_mapping = {}
    for feature in features:
        for field in feature.output_fields:
            output_fields_features_mapping.setdefault(field.identifier, {'features': []})
            output_fields_features_mapping[field.identifier]['features'].append(feature.fqfn)
    output_fields_in_multiple_features = {field_identifier: field for field_identifier, field in output_fields_features_mapping.items()
                                          if len(field['features']) > 1}
    if output_fields_in_multiple_features:
        raise RuntimeError(f"Following output fields appear in more than 1 feature which is disallowed : \n "
                           f"{json.dumps(output_fields_in_multiple_features, indent=4)}")


def _parse_feature_version(feature_version: str):
    return int(feature_version.replace('v', ''))


def format_feature_version(feature_version: int):
    return f'v{feature_version}'

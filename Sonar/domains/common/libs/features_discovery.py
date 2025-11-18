from thetaray.common import Settings
from common.libs.config.loader import load_config, TR_CFG_METADATA
from common.libs import features_loader
from common.libs.features_loader import validate_mandatory_fields, filter_features


def get_features(cfg, active_only=True, train_only=False, effective_only=True):
    """
    Get a list of feature classes using a config object

    Parameters
    ----------
    cfg: dict
        a configuration object retrieved by using load_config method on a wrangling.yaml file
    active_only: bool
        load only active features or all of them?
    train_only: bool
        load only features that are used in train
    effective_only: bool
        if True, core features that are being overriden by ext features will not be returned
    """
    domain = cfg.get(TR_CFG_METADATA).get('domain')
    cfg_path = cfg.get(TR_CFG_METADATA).get('path')  # <entity>/<cadence>/wrangling.yaml
    entity, cadence, _ = cfg_path.split('/')
    features_loading_config: dict = cfg.get('requested_features')

    validate_mandatory_fields(features_loading_config, ('train',))
    if train_only:
        features_loading_config = filter_features(features_loading_config, field='train')

    features_base_path = f'{Settings.DOMAINS_PATH}/{domain}/features'
    core_features_path = f'{features_base_path}/core/{entity}'
    ext_features_path = f'{features_base_path}/ext/{entity}'
    return features_loader.get_features(features_loading_config, core_features_path, ext_features_path, active_only, effective_only)


def get_features_output_fields(domain, entity, cadence, active_only=True, train_only=False) -> list:
    """
    Get a list of active fields in requested features by config

    Parameters
    ----------
    domain: str
        The domain
    entity: str
        The investigated entity
    cadence: str
        The cadence
    active_only: bool
        Filter inactive features.
    train_only: bool
        Filter features that are used for rules and should be excluded in the train.
    Returns
    -------
    list
        The Fields class instances corresponding to the active fields
    """
    path = f'{entity}/{cadence}/wrangling.yaml'
    config = load_config(path, domain=domain)
    requested_fields = []
    for feature in get_features(config, active_only=active_only, train_only=train_only):
        requested_fields.extend(list(feature.output_fields))
    requested_fields = sorted(requested_fields, key=lambda f: f.identifier)
    return requested_fields


def feature_ids_to_params(cfg, features):
    features_loading_config = cfg.get('requested_features')
    result = {}
    for feature in features:
        feature_config = features_loading_config[feature.identifier][f'v{feature.version}']
        result[feature.identifier] = feature_config.get('params', {})
    return result

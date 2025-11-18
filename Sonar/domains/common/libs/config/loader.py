TR_CFG_METADATA = 'tr_cfg_metadata'

from thetaray.common import Settings
from .. import consts
from thetaray.common.logging import logger

import yaml
import flatdict
import os.path


def load_config(path, context=None, domain=None) -> dict:
    """Load the effective config where the precedence is as follows:
    1. context
    2. ext
    3. core
    It means that a param that is defined in the context (in Airflow / Notebook) takes precedence over the value of the param in the ext/core

    Parameters
    ----------
    path: str
        Relative path to the config file, e.g. libs/zscore.yaml, debtor/daily/wrangling.yaml
    context: JobExecutionContext
        Execution context details, should be provided when function is called from a notebook
    domain: str
        The working domain, it's unnecessary in case context is provided since the context contains the working domain

    Returns
    -------
    dict
        The effective configuration
    """
    if context is None and domain is None:
        raise ValueError("You must provide either the context or the domain you are working on")
    domain = domain or context.domain
    effective_config = flatdict.FlatDict()

    core_config_file_exist = _update_effective_config(effective_config, layer='core', domain=domain, path=path)
    snap_config_file_exist = _update_effective_config(effective_config, layer='snap', domain=domain, path=path)
    ext_config_file_exist = _update_effective_config(effective_config, layer='ext', domain=domain, path=path)

    if not core_config_file_exist and not snap_config_file_exist and not ext_config_file_exist:
        raise FileNotFoundError(f"No config file was found for {path} under any layer (core/snap/ext)")

    logger.debug(f"Configuration for {path} was loaded from core:{core_config_file_exist}, "
          f"snap:{snap_config_file_exist}, "
          f"ext:{ext_config_file_exist}")

    if context:
        context_params = flatdict.FlatDict(context.parameters)
        effective_config.update(context_params)
    missing_keys = {k: v for k, v in effective_config.items() if str(v).upper() == consts.TBD}
    if missing_keys:
        raise ValueError(f"You must configure the following in the '{path}' config file:\n{missing_keys}")
    config = effective_config.as_dict()
    if TR_CFG_METADATA in config.keys():
        raise KeyError('config file cannot contain tr_metadata key')
    config.update({TR_CFG_METADATA: {'path': path,
                                     'domain': domain}})
    return config


def _update_effective_config(effective_config, layer, domain, path):
    filepath = f'{Settings.DOMAINS_PATH}/{domain}/config/{layer}/{path}'
    config_file_exist = os.path.isfile(filepath)
    if config_file_exist:
        config = flatdict.FlatDict(load_yaml(filepath))
        effective_config.update(config)
    return config_file_exist


def load_yaml(filepath):
    with open(filepath, 'r') as stream:
        try:
            parsed_yaml = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid yaml file, reason: {exc}")
        if type(parsed_yaml) != dict:
            raise TypeError(f"Invalid yaml file, parsed yaml should be a dict, got {type(parsed_yaml)}")
    return parsed_yaml


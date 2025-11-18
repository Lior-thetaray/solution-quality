from thetaray.api.solution import IngestionMode
from common.libs.config.loader import load_config


def load_dataset_config(ds_filename, domain) -> dict:
    config = load_config(f'datasets/{ds_filename}', domain=domain)
    config = _load_ingestion_mode(config)
    return config


def _load_ingestion_mode(config):
    if 'ingestion_mode' in config:
        if config['ingestion_mode'].lower() == 'update':
            config['ingestion_mode'] = IngestionMode.UPDATE
        elif config['ingestion_mode'].lower() == 'overwrite':
            config['ingestion_mode'] = IngestionMode.OVERWRITE
        else:
            raise ValueError("Allowed ingestion modes are: [update, overwrite]")
    return config
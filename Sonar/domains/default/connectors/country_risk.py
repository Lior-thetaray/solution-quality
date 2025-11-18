from typing import List

from thetaray.api.connector import FlatFileConnector
from thetaray.api.connector.flat_file_connector.flat_file_connector import (
    Source,
    Target,
    TimestampConf,
    TimestampConfType,
)


def country_risk_connector() -> FlatFileConnector:
    return FlatFileConnector(
        identifier='country_risk',
        display_name='country_risk',
        source=Source(
            folder='country_risk',
            has_header=True,
            delimiter=',',
            timestamp_conf=TimestampConf(type=TimestampConfType.EXECUTION_DATE, filename_pattern='%Y%m%d %H:%M:%S'),
            dataset_schema_ref='country_risk'
        ),
        targets=[Target(dataset_name='country_risk')],
        default_target_dataset_name='country_risk',
    )


def entities() -> List[FlatFileConnector]:
    return [country_risk_connector()]

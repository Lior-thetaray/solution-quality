from thetaray.api.connector import FlatFileConnector

# TODO: Why not import from module, we're mixing between module / file level imports
from thetaray.api.connector.flat_file_connector.flat_file_connector import Source, Target, TimestampConf, TimestampConfType


def card_connector():
    return FlatFileConnector(
        identifier="card",
        display_name="card",
        source=Source(
            folder="card",
            has_header=True,
            delimiter=",",
            timestamp_conf=TimestampConf(type=TimestampConfType.EXECUTION_DATE, filename_pattern="%Y%m%d %H:%M:%S"),
            dataset_schema_ref="card"
        ),
        targets=
        [
            Target(
            dataset_name="card")
        ],
        default_target_dataset_name="card"
    )

def entities():
    return [card_connector()]

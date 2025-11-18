from thetaray.api.connector import FlatFileConnector

# TODO: Why not import from module, we're mixing between module / file level imports
from thetaray.api.connector.flat_file_connector.flat_file_connector import Source, Target, TimestampConfType, TimestampConf


def account_connector():
    return FlatFileConnector(
        identifier="account",
        display_name="account",
        source=Source(
            folder="account",
            has_header=True,
            delimiter=",",
            timestamp_conf=TimestampConf(type=TimestampConfType.COLUMN, column_name='date', filename_pattern="%Y%m%d"),
            dataset_schema_ref="account"
        ),
        targets=[Target(
            dataset_name="account"
        )],
        default_target_dataset_name="account"
    )

def entities():
    return [account_connector()]

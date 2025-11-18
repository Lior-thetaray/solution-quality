from thetaray.api.connector import FlatFileConnector

# TODO: Why not import from module, we're mixing between module / file level imports
from thetaray.api.connector.flat_file_connector.flat_file_connector import Source, Target, TimestampConf, TimestampConfType


def transaction_connector():
    """Build transaction FFC"""
    return FlatFileConnector(
        identifier="transaction",
        display_name="transaction",
        source=Source(
            folder="transaction",
            has_header=True,
            delimiter=",",
            timestamp_conf=TimestampConf(type=TimestampConfType.EXECUTION_DATE, filename_pattern="%Y%m%d %H:%M:%S"),
            dataset_schema_ref="transaction"
        ),
        targets=[Target(
            dataset_name="transaction"
        )],
        default_target_dataset_name="transaction"
    )

def entities():
    return [transaction_connector()]

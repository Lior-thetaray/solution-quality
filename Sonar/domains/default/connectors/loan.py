from thetaray.api.connector import FlatFileConnector

# TODO: Why not import from module, we're mixing between module / file level imports
from thetaray.api.connector.flat_file_connector.flat_file_connector import Source, Target, TimestampConfType, TimestampConf


def loan_connector():
    return FlatFileConnector(
        identifier="loan",
        display_name="loan",
        source=Source(
            folder="loan",
            has_header=True,
            delimiter=",",
            timestamp_conf=TimestampConf(type=TimestampConfType.COLUMN, column_name='date', filename_pattern="%Y%m%d %H:%M:%S"),
            dataset_schema_ref="loan"
        ),
        targets=[Target(
            dataset_name="loan"
        )],
        default_target_dataset_name="loan"
    )

def entities():
    return [loan_connector()]

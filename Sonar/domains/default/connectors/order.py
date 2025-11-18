from thetaray.api.connector import FlatFileConnector

# TODO: Why not import from module, we're mixing between module / file level imports
from thetaray.api.connector.flat_file_connector.flat_file_connector import Source, Target, TimestampConf, TimestampConfType


def order_connector():
    return FlatFileConnector(
        identifier="order",
        display_name="order",
        source=Source(
            folder="order",
            has_header=True,
            delimiter=",",
            timestamp_conf=TimestampConf(type=TimestampConfType.EXECUTION_DATE, filename_pattern="%Y%m%d %H:%M:%S"),
            dataset_schema_ref="order"
        ),
        targets=[Target(
            dataset_name="order"
        )],
        default_target_dataset_name="order"
    )

def entities():
    return [order_connector()]

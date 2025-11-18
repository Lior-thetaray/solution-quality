from thetaray.api.connector import FlatFileConnector

# TODO: Why not import from module, we're mixing between module / file level imports
from thetaray.api.connector.flat_file_connector.flat_file_connector import Source, Target, TimestampConfType, TimestampConf


def client_connector():
    return FlatFileConnector(
        identifier="client",
        display_name="client",
        source=Source(
            folder="client",
            has_header=True,
            delimiter=",",
            timestamp_conf=TimestampConf(type=TimestampConfType.EXECUTION_DATE, filename_pattern="%Y%m%d %H:%M:%S"),
            dataset_schema_ref="client"
        ),
        targets=[Target(
            dataset_name="client"
        )],
        default_target_dataset_name="client"
    )

def entities():
    return [client_connector()]

from thetaray.api.connector import FlatFileConnector

# TODO: Why not import from module, we're mixing between module / file level imports
from thetaray.api.connector.flat_file_connector.flat_file_connector import Source, Target, TimestampConfType, TimestampConf


def district_connector():
    return FlatFileConnector(
        identifier="district",
        display_name="district",
        source=Source(
            folder="district",
            has_header=True,
            delimiter=",",
            timestamp_conf=TimestampConf(type=TimestampConfType.EXECUTION_DATE, filename_pattern="%Y%m%d %H:%M:%S"),
            dataset_schema_ref="district"
        ),
        targets=[Target(
            dataset_name="district"
        )],
        default_target_dataset_name="district"
    )

def entities():
    return [district_connector()]

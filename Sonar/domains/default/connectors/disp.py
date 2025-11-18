from pyspark.sql import DataFrame, Column

from thetaray.api.connector import FlatFileConnector

# TODO: Why not import from module, we're mixing between module / file level imports
from thetaray.api.connector.flat_file_connector.flat_file_connector import Source, Target, TimestampConfType, TimestampConf


def disp_connector():
    def disp_owner_condition(df: DataFrame) -> Column:
        return df.type == "OWNER"

    return FlatFileConnector(
    	identifier="disp",
        display_name="disp",
        source=Source(
            folder="disp",
            has_header=True,
            delimiter=",",
            timestamp_conf=TimestampConf(type=TimestampConfType.EXECUTION_DATE, filename_pattern="%Y%m%d %H:%M:%S"),
            dataset_schema_ref="disp"
        ),
        targets=[
            Target(
                dataset_name="disp_owner",
                condition=disp_owner_condition
            ),
            Target(
                dataset_name="disp_disponent",
                condition='type = "DISPONENT"'
            )
        ],
        default_target_dataset_name="disp_owner"
    )




def entities():
    return [disp_connector()]

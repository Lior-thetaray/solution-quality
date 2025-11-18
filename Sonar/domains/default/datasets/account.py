from typing import List

from pyspark.sql import Column

from thetaray.api.solution import DataSet, DataType, Field, IngestionMode, ParquetIndex
from thetaray.api.solution.dataset import Validator


def account_dataset() -> DataSet:
    def account_id_validation(c: Column) -> Column:
        return c.isNotNull()

    return DataSet(
        identifier="account",
        display_name="account",
        field_list=[
            Field(
                identifier="account_id",
                display_name="account_id",
                data_type=DataType.STRING,
                array_indicator=False,
                encrypted=True,
                audited=True,
                validators=[
                    Validator(
                        name="account_id_validator",
                        action=Validator.Action.REJECT,
                        validate_logic=account_id_validation,
                        enable=True,
                    ),
                ],
            ),
            Field(identifier="district_id", display_name="district_id", data_type=DataType.LONG, array_indicator=False),
            Field(identifier="frequency", display_name="frequency", data_type=DataType.STRING, array_indicator=False),
            Field(
                identifier="date",
                display_name="date",
                data_type=DataType.TIMESTAMP,
                date_format="%Y%m%d",
                array_indicator=False,
            ),
            Field(
                identifier="name",
                display_name="name",
                data_type=DataType.STRING,
                array_indicator=False,
                encrypted=True,
                audited=True,
            ),
            Field(
                identifier="country",
                display_name="country",
                data_type=DataType.STRING,
                array_indicator=False,
                encrypted=True,
            ),
            Field(
                identifier="address",
                display_name="address",
                data_type=DataType.STRING,
                array_indicator=False,
                encrypted=True,
            ),
        ],
        ingestion_mode=IngestionMode.UPDATE,
        publish=True,
        primary_key=["account_id"],
        num_of_partitions=4,
        num_of_buckets=7,
        data_permission="dpv:public",
        parquet_indexes=[
            ParquetIndex(
                identifier="pi_account_id",
                identifier_field="account_id",
                block_size=2 * 1024 * 1024,
                num_identifier_bins=10,
                identifiers_sample_size=1000,
            ),
        ],
    )


def entities() -> List[DataSet]:
    return [account_dataset()]

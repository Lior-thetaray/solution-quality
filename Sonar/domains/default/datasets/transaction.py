from typing import List

from thetaray.api.solution import DataSet, DataType, Field, IngestionMode, RetentionPolicy
from thetaray.api.solution.dataset import DataSetRuleBuilderConfig, FieldRuleBuilderConfig


def transaction_dataset() -> DataSet:
    return DataSet(
        identifier="transaction",
        display_name="transaction",
        field_list=[
            Field(identifier="trans_id", display_name="trans_id", data_type=DataType.LONG, array_indicator=False),
            Field(
                identifier="account_id",
                display_name="account_id",
                data_type=DataType.STRING,
                array_indicator=False,
                encrypted=True,
                audited=True,
            ),
            Field(
                identifier="receiver_id",
                display_name="receiver_id",
                data_type=DataType.STRING,
                array_indicator=False,
                encrypted=True,
                audited=True,
            ),
            Field(
                identifier="date",
                display_name="date",
                data_type=DataType.TIMESTAMP,
                date_format="%Y%m%d",
                array_indicator=False,
            ),
            Field(identifier="type", display_name="type", data_type=DataType.STRING, array_indicator=False),
            Field(identifier="operation", display_name="operation", data_type=DataType.STRING, array_indicator=False),
            Field(identifier="amount", display_name="amount", data_type=DataType.DOUBLE, array_indicator=False),
            Field(identifier="balance", display_name="balance", data_type=DataType.DOUBLE, array_indicator=False),
            Field(identifier="k_symbol", display_name="k_symbol", data_type=DataType.STRING, array_indicator=False),
            Field(identifier="bank", display_name="bank", data_type=DataType.STRING, array_indicator=False),
            Field(identifier="account", display_name="account", data_type=DataType.DOUBLE, array_indicator=False),
            Field(identifier="original_currency", display_name="original_currency", data_type=DataType.STRING, array_indicator=False),
            Field(
                identifier="keyword_group",
                display_name="keyword_group",
                data_type=DataType.STRING,
                array_indicator=False,
                rule_builder_config=FieldRuleBuilderConfig(expose_for_user_enrichments=False),
            ),
        ],
        ingestion_mode=IngestionMode.APPEND,
        publish=True,
        primary_key=["account_id"],
        num_of_partitions=4,
        num_of_buckets=7,
        occurred_on_field="date",
        data_permission="dpv:public",
        retention_policy=RetentionPolicy(months_to_keep=24, months_to_keep_published=12),
        rule_builder_config=DataSetRuleBuilderConfig(expose_for_user_enrichments=True),
    )


def entities() -> List[DataSet]:
    return [transaction_dataset()]

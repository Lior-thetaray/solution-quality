from typing import List

from thetaray.api.solution import DataSet, DataType, Field, IngestionMode


def party_wrangling_dataset() -> DataSet:
    return DataSet(
        identifier="party_wrangling",
        display_name="party_wrangling",
        field_list=[
            Field(
                display_name="party_id",
                data_type=DataType.STRING,
                identifier="party_id",
                encrypted=True,
                audited=True,
            ),
            Field(
                identifier="party_accounts",
                display_name="party_accounts",
                data_type=DataType.STRING,
                encrypted=True,
                audited=True,
            ),
            Field(display_name="district_id_bank", data_type=DataType.LONG, identifier="district_id_bank"),
            Field(display_name="frequency", data_type=DataType.STRING, identifier="frequency"),
            Field(display_name="date_acct", data_type=DataType.TIMESTAMP, identifier="date_acct"),
            Field(display_name="disp_id", data_type=DataType.LONG, identifier="disp_id"),
            Field(display_name="client_id", data_type=DataType.LONG, identifier="client_id"),
            Field(display_name="type_disp", data_type=DataType.STRING, identifier="type_disp"),
            Field(display_name="loan_id", data_type=DataType.LONG, identifier="loan_id"),
            Field(display_name="date_loan", data_type=DataType.TIMESTAMP, identifier="date_loan"),
            Field(display_name="amount", data_type=DataType.LONG, identifier="amount", indexed=True),
            Field(display_name="duration", data_type=DataType.LONG, identifier="duration"),
            Field(display_name="payments", data_type=DataType.LONG, identifier="payments", indexed=True),
            Field(display_name="response", data_type=DataType.LONG, identifier="response"),
            Field(display_name="birth_number", data_type=DataType.LONG, identifier="birth_number"),
            Field(display_name="district_id_client", data_type=DataType.LONG, identifier="district_id_client"),
            Field(display_name="card_id", data_type=DataType.LONG, identifier="card_id"),
            Field(display_name="type_card", data_type=DataType.STRING, identifier="type_card"),
            Field(display_name="min1", data_type=DataType.DOUBLE, identifier="min1"),
            Field(display_name="max1", data_type=DataType.DOUBLE, identifier="max1"),
            Field(display_name="mean1", data_type=DataType.DOUBLE, identifier="mean1"),
            Field(display_name="min2", data_type=DataType.DOUBLE, identifier="min2"),
            Field(display_name="max2", data_type=DataType.DOUBLE, identifier="max2"),
            Field(display_name="mean2", data_type=DataType.DOUBLE, identifier="mean2"),
            Field(display_name="min3", data_type=DataType.DOUBLE, identifier="min3"),
            Field(display_name="max3", data_type=DataType.DOUBLE, identifier="max3"),
            Field(display_name="mean3", data_type=DataType.DOUBLE, identifier="mean3"),
            Field(display_name="min4", data_type=DataType.DOUBLE, identifier="min4"),
            Field(display_name="max4", data_type=DataType.DOUBLE, identifier="max4"),
            Field(display_name="mean4", data_type=DataType.DOUBLE, identifier="mean4"),
            Field(display_name="min5", data_type=DataType.DOUBLE, identifier="min5"),
            Field(display_name="max5", data_type=DataType.DOUBLE, identifier="max5"),
            Field(display_name="mean5", data_type=DataType.DOUBLE, identifier="mean5"),
            Field(display_name="min6", data_type=DataType.DOUBLE, identifier="min6"),
            Field(display_name="max6", data_type=DataType.DOUBLE, identifier="max6"),
            Field(display_name="mean6", data_type=DataType.DOUBLE, identifier="mean6"),
            Field(display_name="has_card", data_type=DataType.LONG, identifier="has_card"),
        ],
        ingestion_mode=IngestionMode.APPEND,
        publish=True,
        primary_key=["party_id"],
        num_of_partitions=4,
        num_of_buckets=7,
        occurred_on_field="date_loan",
        data_permission="dpv:public",
    )


def entities() -> List[DataSet]:
    return [party_wrangling_dataset()]

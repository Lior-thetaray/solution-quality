from thetaray.api.solution import DataSet, Field, DataType, IngestionMode


def order_dataset():
    return DataSet(
        identifier="order",
        display_name="order",
        field_list=[
            Field(identifier="order_id", display_name="order_id", data_type=DataType.LONG, array_indicator=False),
            Field(identifier="account_id", display_name="account_id", data_type=DataType.STRING, array_indicator=False),
            Field(identifier="bank_to", display_name="bank_to", data_type=DataType.STRING, array_indicator=False),
            Field(identifier="account_to", display_name="account_to", data_type=DataType.STRING, array_indicator=False),
            Field(identifier="amount", display_name="amount", data_type=DataType.DOUBLE, array_indicator=False),
            Field(identifier="k_symbol", display_name="k_symbol", data_type=DataType.STRING, array_indicator=False),
        ],
        ingestion_mode=IngestionMode.OVERWRITE,
        publish=True,
        primary_key=["order_id"],
        num_of_partitions=4,
        num_of_buckets=7,
        data_permission="dpv:public"
    )

def entities():
    return [order_dataset()]
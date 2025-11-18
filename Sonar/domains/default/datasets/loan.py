from thetaray.api.solution import DataSet, Field, DataType, IngestionMode


def loan_dataset():
    return DataSet(
        identifier="loan",
        display_name="loan",
        field_list=[
            Field(identifier="loan_id", display_name="loan_id", data_type=DataType.LONG, array_indicator=False),
            Field(identifier="account_id", display_name="account_id", data_type=DataType.STRING, array_indicator=False),
            Field(identifier="date", display_name="date", data_type=DataType.TIMESTAMP, date_format='%Y%m%d', array_indicator=False),
            Field(identifier="amount", display_name="amount", data_type=DataType.LONG, array_indicator=False),
            Field(identifier="duration", display_name="duration", data_type=DataType.LONG, array_indicator=False),
            Field(identifier="payments", display_name="payments", data_type=DataType.LONG, array_indicator=False),
            Field(identifier="status", display_name="status", data_type=DataType.STRING, array_indicator=False)
        ],  
        ingestion_mode=IngestionMode.UPDATE,
        publish=True,
        primary_key=["account_id"],
        num_of_partitions=4,
        num_of_buckets=7,
        data_permission="dpv:public"
    )

def entities():
    return [loan_dataset()]
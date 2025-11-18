from thetaray.api.solution import DataSet, Field, DataType, IngestionMode


def client_dataset():
    return DataSet(
        identifier="client",
        display_name="client",
        field_list=[
            Field(identifier="client_id", display_name="client_id", data_type=DataType.LONG, array_indicator=False),
            Field(identifier="birth_number", display_name="birth_number", data_type=DataType.LONG, array_indicator=False),
            Field(identifier="district_id", display_name="district_id", data_type=DataType.LONG, array_indicator=False)
        ],
        ingestion_mode=IngestionMode.OVERWRITE,
        publish=True,
        primary_key=["client_id"],
        num_of_partitions=4,
        num_of_buckets=7,
        data_permission="dpv:public"
    )

def entities():
    return [client_dataset()]


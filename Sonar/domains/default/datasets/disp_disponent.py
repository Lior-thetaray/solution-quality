from thetaray.api.solution import DataSet, Field, DataType, IngestionMode


def disp_disponent_dataset():
    return DataSet(
        identifier="disp_disponent",
        display_name="disp_disponent",
        field_list=[
            Field(identifier="disp_id", display_name="disp_id", data_type=DataType.LONG, array_indicator=False),
            Field(identifier="client_id", display_name="client_id", data_type=DataType.LONG, array_indicator=False),
            Field(identifier="account_id", display_name="account_id", data_type=DataType.STRING, array_indicator=False),
            Field(identifier="type", display_name="type", data_type=DataType.STRING, array_indicator=False)
        ],
        ingestion_mode=IngestionMode.OVERWRITE,
        publish=True,
        primary_key=["disp_id"],
        num_of_partitions=4,
        num_of_buckets=7,
        data_permission="dpv:public"
    )

def entities():
    return [disp_disponent_dataset()]
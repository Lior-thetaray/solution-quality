from thetaray.api.solution import DataSet, Field, DataType, IngestionMode, TableIndex


def card_dataset():
    return DataSet(
        identifier="card",
        display_name="card",
        field_list=[
            Field(identifier="card_id", display_name="card_id", data_type=DataType.LONG, array_indicator=False),
            Field(identifier="disp_id", display_name="disp_id", data_type=DataType.LONG, array_indicator=False),
            Field(identifier="type", display_name="type", data_type=DataType.STRING, array_indicator=False),
            Field(identifier="issued", display_name="issued", data_type=DataType.STRING, array_indicator=False),
            Field(identifier="codes", display_name="codes", data_type=DataType.STRING, array_indicator=False)
        ],
        ingestion_mode=IngestionMode.OVERWRITE,
        publish=True,
        primary_key=["card_id"],
        num_of_partitions=4,
        num_of_buckets=7,
        data_permission="dpv:public",
        table_indexes=[TableIndex(identifier="reference_index", columns=["type", "issued"], include=["codes"])],
        primary_key_index=False
    )

def entities():
    return [card_dataset()]
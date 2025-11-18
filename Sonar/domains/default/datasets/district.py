from thetaray.api.solution import DataSet, Field, DataType, IngestionMode


def district_dataset():
    return DataSet(
        identifier="district",
        display_name="district",
        field_list=[
            Field(identifier="a1", display_name="A1", data_type=DataType.LONG, array_indicator=False),
            Field(identifier="a2", display_name="A2", data_type=DataType.STRING, array_indicator=False),
            Field(identifier="a3", display_name="A3", data_type=DataType.STRING, array_indicator=False),
            Field(identifier="a4", display_name="A4", data_type=DataType.LONG, array_indicator=False),
            Field(identifier="a5", display_name="A5", data_type=DataType.LONG, array_indicator=False),
            Field(identifier="a6", display_name="A6", data_type=DataType.LONG, array_indicator=False),
            Field(identifier="a7", display_name="A7", data_type=DataType.LONG, array_indicator=False),
            Field(identifier="a8", display_name="A8", data_type=DataType.LONG, array_indicator=False),
            Field(identifier="a9", display_name="A9", data_type=DataType.LONG, array_indicator=False),
            Field(identifier="a10", display_name="A10", data_type=DataType.DOUBLE, array_indicator=False),
            Field(identifier="a11", display_name="A11", data_type=DataType.DOUBLE, array_indicator=False),
            Field(identifier="a12", display_name="A12", data_type=DataType.DOUBLE, array_indicator=False),
            Field(identifier="a13", display_name="A13", data_type=DataType.DOUBLE, array_indicator=False),
            Field(identifier="a14", display_name="A14", data_type=DataType.LONG, array_indicator=False),
            Field(identifier="a15", display_name="A15", data_type=DataType.LONG, array_indicator=False),
            Field(identifier="a16", display_name="A16", data_type=DataType.LONG, array_indicator=False)
        ],
        ingestion_mode=IngestionMode.OVERWRITE,
        publish=True,
        primary_key=["a1"],
        num_of_partitions=4,
        num_of_buckets=7,
        data_permission="dpv:public"
    )

def entities():
    return [district_dataset()]
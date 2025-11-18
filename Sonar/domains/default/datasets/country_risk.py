from typing import List

from thetaray.api.solution import DataSet, DataType, Field, IngestionMode


def country_risk_dataset() -> DataSet:
    return DataSet(
        identifier='country_risk',
        display_name='country_risk',
        field_list=[
            Field(identifier='country_code', display_name='country_code', data_type=DataType.STRING),
            Field(identifier='risk', display_name='risk', data_type=DataType.STRING),
        ],
        ingestion_mode=IngestionMode.OVERWRITE,
        publish=True,
        primary_key=['country_code'],
        num_of_partitions=1,
        num_of_buckets=1,
        data_permission='dpv:public',
    )


def entities() -> List[DataSet]:
    return [country_risk_dataset()]

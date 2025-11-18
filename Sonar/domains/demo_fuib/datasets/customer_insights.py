from thetaray.api.solution import DataSet, Field, DataType, IngestionMode


def entities():
    return [customer_insights_dataset()]

def customer_insights_dataset():
    return DataSet(
        identifier='customer_insights_fuib',
        display_name='customer_insights',
        ingestion_mode=IngestionMode.UPDATE,
        data_permission='dpv:demo_fuib',
        publish=True,
        primary_key=['customer_id'],
        num_of_partitions=4,
        num_of_buckets=7,
                field_list=[
			Field(identifier='customer_id', display_name='customer_id', data_type=DataType.STRING, array_indicator=False),
			Field(identifier='trx_to_date', display_name='trx_to_date', data_type=DataType.TIMESTAMP, array_indicator=False),
			Field(identifier='month_offset', display_name='month_offset', data_type=DataType.LONG, array_indicator=False),
			Field(identifier='tr_in_count', display_name='tr_in_count', data_type=DataType.LONG, array_indicator=False),
			Field(identifier='tr_in', display_name='tr_in', data_type=DataType.DOUBLE, array_indicator=False),
			Field(identifier='tr_out_count', display_name='tr_out_count', data_type=DataType.LONG, array_indicator=False),
			Field(identifier='tr_out', display_name='tr_out', data_type=DataType.DOUBLE, array_indicator=False),
			Field(identifier='customer_name', display_name='Customer Name', data_type=DataType.STRING, array_indicator=False),
            Field(identifier='customer_country', display_name='Customer Country', data_type=DataType.STRING, array_indicator=False),
			Field(identifier='customer_type', display_name='Customer Type', data_type=DataType.STRING, array_indicator=False),
            Field(identifier='customer_age', display_name='customer Age', data_type=DataType.LONG, array_indicator=False),
			Field(identifier='date_of_birth', display_name='date_of_birth', data_type=DataType.STRING, array_indicator=False),
			Field(identifier='address_full', display_name='address_full', data_type=DataType.STRING, array_indicator=False),
			Field(identifier='occupation', display_name='occupation', data_type=DataType.STRING, array_indicator=False),
            Field(identifier='customer_risk', display_name='customer_risk', data_type=DataType.STRING, array_indicator=False),
			Field(identifier='pep_indicator', display_name='pep_indicator', data_type=DataType.BOOLEAN, array_indicator=False),
			Field(identifier='hr_cc', display_name='hr_cc', data_type=DataType.STRING, array_indicator=True),
			Field(identifier='mr_cc', display_name='mr_cc', data_type=DataType.STRING, array_indicator=True),
			Field(identifier='lr_cc', display_name='lr_cc', data_type=DataType.STRING, array_indicator=True),
            Field(identifier='incorporation_date', display_name='Account Opening Date', data_type=DataType.STRING, array_indicator=False),
			Field(identifier='trx_from_date', display_name='trx_from_date', data_type=DataType.TIMESTAMP, array_indicator=False),
			Field(identifier='tr_timestamp', display_name='tr_timestamp', data_type=DataType.TIMESTAMP, array_indicator=False),
			Field(identifier='effective_date', display_name='effective_date', data_type=DataType.TIMESTAMP, array_indicator=False)
		],
    )


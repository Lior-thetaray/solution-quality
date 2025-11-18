from thetaray.api.solution import DataSet, Field, DataType, IngestionMode


def customers_dataset():
    return DataSet(
        identifier='demo_ret_smb_customers',
        display_name='Retail SMB Customers',
        ingestion_mode=IngestionMode.UPDATE,
        publish=True,
        primary_key=['customer_id'],
        num_of_partitions=1,
        num_of_buckets=1,
        data_permission="dpv:demo_ret_smb",
        field_list=[
            Field(
                identifier='customer_id',
                display_name='Customer ID',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='business_name',
                display_name='Business name',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='registration_number',
                display_name='Registration Number',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='incorporation_country',
                display_name='Incorporation Country',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='incorporation_date',
                display_name='Incorporation Date',
                data_type=DataType.TIMESTAMP,
                comment='Format: yyyy-MM-dd'
            ),
            Field(
                identifier='industry',
                display_name='Industry',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='annual_revenue',
                display_name='Annual Revenue',
                data_type=DataType.DOUBLE,
                comment=None
            ),
            Field(
                identifier='num_employees',
                display_name='Number Of Employees',
                data_type=DataType.LONG
            ),
            
            Field(
                identifier='aml_risk_segment',
                display_name='AML Risk Segment',
                data_type=DataType.LONG,
                comment=None
            ),
            Field(
                identifier='pep',
                display_name='PEP',
                data_type=DataType.BOOLEAN,
                comment='Politically exposed person flag'
            ),
            Field(
                identifier='tax_residence',
                display_name='Tax Residence',
                data_type=DataType.STRING,
                comment='ISO-2 Code'
            )
        ],
    )


def entities():
    return [customers_dataset()]
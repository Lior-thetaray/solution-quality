from thetaray.api.solution import DataSet, Field, DataType, IngestionMode


def customers_dataset():
    return DataSet(
        identifier='demo_ret_indiv_customers',
        display_name='Retail Individual Customers',
        ingestion_mode=IngestionMode.UPDATE,
        publish=True,
        primary_key=['customer_id'],
        num_of_partitions=1,
        num_of_buckets=1,
        data_permission="dpv:demo_ret_indiv",
        field_list=[
            Field(
                identifier='customer_id',
                display_name='Customer ID',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='customer_num',
                display_name='Customer Num',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='type_of_document',
                display_name='Type of Document',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='document_number_id_code',
                display_name='Document Number (ID Code)',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='name',
                display_name='Name',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='date_of_birth',
                display_name='Date of Birth',
                data_type=DataType.TIMESTAMP,
                comment='Format: yyyy-MM-dd'
            ),
            Field(
                identifier='country_of_birth_nationality',
                display_name='Country of Birth/Nationality',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='tax_residency_countries',
                display_name='Tax Residency Countries',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='country_of_residence_code',
                display_name='Country of Residence Code',
                data_type=DataType.STRING,
                comment='ISO-3166 (2-letter code)'
            ),
            Field(
                identifier='country_of_residence',
                display_name='Country of Residence',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='citizenship_countries_code',
                display_name='Citizenship Countries Code',
                data_type=DataType.STRING,
                comment='ISO-3166 (2-letter code)'
            ),
            Field(
                identifier='citizenship_countries',
                display_name='Citizenship Countries',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='address',
                display_name='Address',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='phone_number',
                display_name='Phone Number',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='occupation',
                display_name='Occupation',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='is_unemployed',
                display_name='Is Unemployed',
                data_type=DataType.BOOLEAN,
                comment=None
            ),
            Field(
                identifier='customer_effective_date',
                display_name='Customer Effective Date',
                data_type=DataType.TIMESTAMP,
                comment='Format: yyyy-MM-dd'
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
                identifier='segment_type',
                display_name='Segment Type',
                data_type=DataType.STRING,
                comment='Code'
            ),
            Field(
                identifier='segment_type_description',
                display_name='Segment Type Description',
                data_type=DataType.STRING,
                comment='e.g., Personal, NPO, etc.'
            ),
            Field(
                identifier='sars_flag',
                display_name='Sars_Flag',
                data_type=DataType.BOOLEAN,
                comment='e.g., technical accounts'
            ),
        ],
    )


def entities():
    return [customers_dataset()]
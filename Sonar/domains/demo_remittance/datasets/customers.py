from thetaray.api.solution import DataSet, Field, DataType, IngestionMode


def customers_dataset():
    return DataSet(
        identifier='demo_remittance_customers',
        display_name='Remittance Individual Customers',
        ingestion_mode=IngestionMode.UPDATE,
        publish=True,
        primary_key=['customer_id'],
        num_of_partitions=1,
        num_of_buckets=1,
        data_permission="dpv:demo_remittance",
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
                identifier='document_type',
                display_name='Document Type',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='document_id',
                display_name='Document ID',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='name',
                display_name='Full Name',
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
                identifier='country_of_birth',
                display_name='Country of Birth',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='citizenship_countries',
                display_name='Citizenship Countries',
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
                identifier='email',
                display_name='Email',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='primary_source_of_income',
                display_name='Primary Source Of Income',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='estimated_annual_income_usd',
                display_name='Estimated Annual Income USD',
                data_type=DataType.LONG,
                comment=None
            ),
            Field(
                identifier='risk_rating',
                display_name='Risk Rating',
                data_type=DataType.LONG,
                comment=None
            ),

            Field(
                identifier='is_pep',
                display_name='PEP',
                data_type=DataType.BOOLEAN,
                comment='Politically exposed person flag'
            ),
            
            Field(
                identifier='is_sanctioned',
                display_name='Sanctioned',
                data_type=DataType.BOOLEAN,
                comment='If the person was sanctioned'
            ),
            Field(
                identifier='high_risk_country_exposure',
                display_name='High Risk Country Exposure',
                data_type=DataType.BOOLEAN,
                comment=None
            ),
            Field(
                identifier='daily_remittance_limit_usd',
                display_name='Daily Remittance Limit USD',
                data_type=DataType.LONG,
                comment=None
            ),
            Field(
                identifier='monthly_remittance_limit_usd',
                display_name='Monthly Remittance Limit USD',
                data_type=DataType.LONG,
                comment=None
            ),
            Field(
                identifier='customer_effective_date',
                display_name='Customer Effective Date',
                data_type=DataType.TIMESTAMP,
                comment='Format: yyyy-MM-dd'
            ),
            Field(
                identifier='kyc_last_review_date',
                display_name='KYC Last Review Date',
                data_type=DataType.TIMESTAMP,
                comment='Format: yyyy-MM-dd'
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
                display_name='Sars Flag',
                data_type=DataType.BOOLEAN,
                comment=None
            ),
        ],
    )


def entities():
    return [customers_dataset()]
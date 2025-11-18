from thetaray.api.solution import DataSet, Field, DataType, IngestionMode


def customers_dataset():
    return DataSet(
        identifier='demo_pay_proc_customers',
        display_name='Payment Processor Customers',
        ingestion_mode=IngestionMode.UPDATE,
        publish=True,
        primary_key=['customer_id'],
        num_of_partitions=1,
        num_of_buckets=1,
        data_permission="dpv:demo_pay_proc",
        field_list=[
            Field(identifier='customer_id', display_name='Customer ID', data_type=DataType.STRING),
            Field(identifier='customer_name', display_name='Customer Name', data_type=DataType.STRING),
            Field(identifier='customer_mcc_code', display_name='Customer MCC Code', data_type=DataType.STRING, comment='Merchant Category Code'),
            Field(identifier='registration_id', display_name='Registration ID', data_type=DataType.STRING),
            Field(identifier='incorporation_date', display_name='Incorporation Date', data_type=DataType.TIMESTAMP, comment='Format: yyyy-MM-dd'),
            Field(identifier='customer_country_id', display_name='Customer Country Code', data_type=DataType.STRING, comment='ISO-2 Country Code'),
            Field(identifier='customer_country_name', display_name='Customer Country Name', data_type=DataType.STRING),
            Field(identifier='tax_residence', display_name='Tax Residence', data_type=DataType.STRING, comment='ISO-2 Code'),
            Field(identifier='industry', display_name='Industry', data_type=DataType.STRING),
            Field(identifier='expected_revenue', display_name='Expected Revenue Range', data_type=DataType.STRING, comment='E.g., "$1M-$5M"'),
            Field(identifier='number_employees', display_name='Number of Employees', data_type=DataType.LONG),
            Field(identifier='aml_risk_rating', display_name='AML Risk Rating', data_type=DataType.LONG, comment='Scale: 1 (Low) to 10 (High)'),
            Field(identifier='primary_payment_channels', display_name='Primary Payment Channels', data_type=DataType.STRING, comment='Comma-separated values'),
            Field(identifier='onboarding_date', display_name='Onboarding Date', data_type=DataType.TIMESTAMP),
            Field(identifier='kyc_review_date', display_name='Last KYC Review Date', data_type=DataType.TIMESTAMP),
            Field(identifier='pep_flag', display_name='PEP Flag', data_type=DataType.BOOLEAN, comment='Politically exposed person indicator'),
            Field(identifier='sanctions_check_status', display_name='Sanctions Check Status', data_type=DataType.STRING, comment='E.g., Clear / Pending / Match'),
            Field(identifier='expected_transaction_volume', display_name='Expected Transaction Volume', data_type=DataType.STRING, comment='E.g., "1000-3000 transactions per month"'),
            Field(identifier='average_ticket_size', display_name='Average Ticket Size', data_type=DataType.STRING, comment='E.g., "$50"'),
            Field(identifier='jurisdiction_risk_level', display_name='Jurisdiction Risk Level', data_type=DataType.STRING, comment='Low / Moderate / High'),
            Field(identifier='risk_drivers', display_name='Risk Drivers', data_type=DataType.STRING, comment='Key reasons contributing to AML risk'),
            Field(identifier='ownership_structure', display_name='Ownership Structure', data_type=DataType.STRING, comment='E.g., Privately Held / Publicly Traded'),
            Field(identifier='compliance_officer_assigned', display_name='Compliance Officer Assigned', data_type=DataType.STRING),
        ],
    )


def entities():
    return [customers_dataset()]

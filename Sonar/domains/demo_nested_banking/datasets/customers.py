from typing import List
from thetaray.api.solution import DataSet, Field, DataType, IngestionMode


def customers_dataset():
    return DataSet(
        identifier='demo_nested_banking_customers',
        display_name='Nested Accounts/Correspondent Banking SWIFT MX Customers',
        ingestion_mode=IngestionMode.UPDATE,
        publish=True,
        primary_key=['customer_id'],
        num_of_partitions=1,
        num_of_buckets=1,
        data_permission="dpv:demo_nested_banking",
        field_list=[
            # Core identity
            Field(identifier='customer_id', display_name='Customer ID', data_type=DataType.STRING, comment='Respondent bank identifier'),
            Field(identifier='customer_name', display_name='Customer Name', data_type=DataType.STRING, comment='Respondent bank legal name'),
            Field(identifier='nested_account_id', display_name='Nested Account ID', data_type=DataType.STRING, comment='Internal correspondent account mapping (nostro/vostro)'),
            Field(identifier='registration_id', display_name='Registration ID', data_type=DataType.STRING),
            Field(identifier='swift_bic', display_name='SWIFT BIC', data_type=DataType.STRING, comment='Customer servicing BIC (8/11)'),

            # Corporate/Legal & Regulatory
            Field(identifier='incorporation_date', display_name='Incorporation Date', data_type=DataType.TIMESTAMP, comment='Format: yyyy-MM-dd'),
            Field(identifier='license_type', display_name='License Type', data_type=DataType.STRING, comment='Full Banking License / Representative Office / EMI'),
            Field(identifier='regulator', display_name='Primary Regulator', data_type=DataType.STRING),

            # Jurisdiction
            Field(identifier='head_office_country_code', display_name='Head Office Country Code', data_type=DataType.STRING, comment='ISO-2'),
            Field(identifier='head_office_country_name', display_name='Head Office Country Name', data_type=DataType.STRING),
            Field(identifier='tax_residence', display_name='Tax Residence', data_type=DataType.STRING, comment='ISO-2'),
            Field(identifier='jurisdiction_risk_level', display_name='Jurisdiction Risk Level', data_type=DataType.STRING, comment='Low / Medium / High'),

            # Business profile (correspondent banking)
            Field(identifier='expected_corr_volumes', display_name='Expected Correspondent Volumes', data_type=DataType.STRING, comment='e.g., "5k-20k payments per month"'),
            Field(identifier='expected_corr_value', display_name='Expected Correspondent Value', data_type=DataType.STRING, comment='e.g., "$50M-$250M"'),
            Field(identifier='corr_network_size', display_name='Correspondent Network Size', data_type=DataType.LONG, comment='Number of correspondent relationships'),

            # Risk & compliance
            Field(identifier='aml_risk_rating', display_name='AML Risk Rating', data_type=DataType.LONG, comment='Scale: 1 (Low) to 10 (High)'),
            Field(identifier='risk_drivers', display_name='Risk Drivers', data_type=DataType.STRING, comment='Reasons contributing to AML risk'),
            Field(identifier='pep_flag', display_name='PEP Flag', data_type=DataType.BOOLEAN),
            Field(identifier='sanctions_check_status', display_name='Sanctions Check Status', data_type=DataType.STRING, comment='Clear / Pending Review'),
            Field(identifier='ownership_structure', display_name='Ownership Structure', data_type=DataType.STRING, comment='State-Owned Bank / Privately Held Bank / Publicly Listed Bank'),
            Field(identifier='ultimate_beneficial_owner', display_name='Ultimate Beneficial Owner', data_type=DataType.STRING),

            # Governance & lifecycle
            Field(identifier='compliance_officer_assigned', display_name='Compliance Officer Assigned', data_type=DataType.STRING),
            Field(identifier='kyc_onboarding_date', display_name='KYC Onboarding Date', data_type=DataType.TIMESTAMP),
            Field(identifier='kyc_last_review_date', display_name='Last KYC Review Date', data_type=DataType.TIMESTAMP),
            Field(identifier='next_review_due', display_name='Next Review Due', data_type=DataType.TIMESTAMP),

            # Analyst-facing context
            Field(identifier='nested_relationship_type', display_name='Relationship Type', data_type=DataType.STRING, comment='Direct Nostro/Vostro / Nested / Indirect'),
            Field(identifier='expected_transaction_patterns', display_name='Expected Transaction Patterns', data_type=DataType.STRING, comment='Narrative of expected flows'),
            Field(identifier='monitoring_notes', display_name='Monitoring Notes', data_type=DataType.STRING, comment='EDD notes / watchpoints'),
        ],
    )


def entities() -> List[DataSet]:
    return [customers_dataset()]

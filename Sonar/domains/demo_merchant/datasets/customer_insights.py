from typing import List

from thetaray.api.solution import DataSet, DataType, Field, IngestionMode, BusinessType


def customer_insights_dataset() -> DataSet:
    return DataSet(
        identifier="demo_merchant_customer_insights",
        display_name="Merchant Acquiring - Customer Insights",
                field_list=[
            # Claves / Identidad
            Field(
                identifier="merchant_id",
                display_name="Merchant ID",
                data_type=DataType.STRING,
                encrypted=True,
                audited=True,
            ),
            Field(
                identifier="legal_name",
                display_name="Legal Name",
                data_type=DataType.STRING,
                encrypted=True,
                audited=True,
            ),
            Field(
                identifier="kyc_name",
                display_name="Name (KYC)",
                data_type=DataType.STRING,
                encrypted=True,
                audited=True,
            ),

            # KYC / Metadatos
            Field(
                identifier="kyc_classification",
                display_name="KYC Classification",
                data_type=DataType.STRING,
            ),
            Field(
                identifier="kyc_is_new",
                display_name="Is New Account",
                description="The customer has at least one account that has been recently opened.",
                data_type=DataType.BOOLEAN,
            ),
            Field(
                identifier="kyc_recently_updated",
                display_name="Recently Updated",
                description="The customer information has been recently updated.",
                data_type=DataType.BOOLEAN,
            ),
            Field(
                identifier="kyc_newly_incorporation",
                display_name="Newly Incorporated",
                description="The company has been recently incorporated.",
                data_type=DataType.BOOLEAN,
            ),
            Field(
                identifier="kyc_new_customer",
                display_name="New Customer",
                description="The customer has been recently onboarded.",
                data_type=DataType.BOOLEAN,
            ),
            Field(
                identifier="kyc_occupation",
                display_name="Customer Occupation",
                data_type=DataType.STRING,
                encrypted=True,
            ),
            Field(
                identifier="hr_cc",
                display_name="High Risk Countries",
                data_type=DataType.STRING,
                array_indicator=True,
            ),
            Field(
                identifier="mr_cc",
                display_name="Medium Risk Countries",
                data_type=DataType.STRING,
                array_indicator=True,
            ),
            Field(
                identifier="lr_cc",
                display_name="Low Risk Countries",
                data_type=DataType.STRING,
                array_indicator=True,
            ),
            Field(
                identifier="director_ad",
                display_name="Director Address",
                data_type=DataType.STRING,
                encrypted=True,
            ),
            Field(
                identifier="company_ad",
                display_name="Company Address",
                data_type=DataType.STRING,
                encrypted=True,
            ),
            Field(
                business_type=BusinessType.CURRENCY,
                units="USD",
                identifier="tr_in",
                display_name="Transaction In",
                data_type=DataType.DOUBLE,
            ),
            Field(
                business_type=BusinessType.CURRENCY,
                units="USD",
                identifier="tr_out",
                display_name="Transaction Out",
                data_type=DataType.DOUBLE,
            ),
            Field(
                identifier="tr_in_count",
                display_name="Transaction In Count",
                data_type=DataType.LONG,
            ),
            Field(
                identifier="tr_out_count",
                display_name="Transaction Out Count",
                data_type=DataType.LONG,
            ),
            Field(
                business_type=BusinessType.CURRENCY,
                units="USD",
                identifier="tr_in_seg",
                display_name="Transaction In Segment",
                data_type=DataType.DOUBLE,
            ),
            Field(
                business_type=BusinessType.CURRENCY,
                units="USD",
                identifier="tr_out_seg",
                display_name="Transaction Out Segment",
                data_type=DataType.DOUBLE,
            ),
            Field(
                identifier="tr_in_seg_count",
                display_name="Transaction In Segment Count",
                data_type=DataType.LONG,
            ),
            Field(
                identifier="tr_out_seg_count",
                display_name="Transaction Out Segment Count",
                data_type=DataType.LONG,
            ),
            Field(
                identifier="trx_from_date",
                display_name="Transaction From Date",
                data_type=DataType.TIMESTAMP,
            ),
            Field(
                identifier="trx_to_date",
                display_name="Transaction To Date",
                data_type=DataType.TIMESTAMP,
            ),
            Field(
                identifier="tm",
                display_name="Transaction Monitoring",
                data_type=DataType.STRING,
            ),
            Field(
                identifier="scrn",
                display_name="Screening",
                data_type=DataType.STRING,
            ),
            Field(
                identifier="customer_country",
                display_name="Customer Country",
                data_type=DataType.STRING,
            ),
            Field(
                identifier="wallet_age_days",
                display_name="Wallet Age (days)",
                data_type=DataType.LONG,
            ),
            Field(
                identifier="uses_crypto",
                display_name="Uses Crypto",
                data_type=DataType.BOOLEAN,
            ),
            Field(
                identifier="has_high_risk_country_tx",
                display_name="Has High-Risk Country Tx",
                data_type=DataType.BOOLEAN,
            ),
            Field(
                identifier="kyc_risk_level",
                display_name="KYC Risk Level",
                data_type=DataType.STRING,
            ),
            Field(
                identifier="effective_date",
                display_name="Effective date",
                data_type=DataType.TIMESTAMP,
            ),
            Field(
                identifier="low_value_trx_ratio",
                display_name="Low Value Transaction Ratio",
                data_type=DataType.DOUBLE,
            ),
            Field(
                identifier="is_dormant_account",
                display_name="Dormant Account (flag)",
                data_type=DataType.DOUBLE,
            ),
            Field(
                identifier="spike_of_trx",
                display_name="Spike of Transactions (flag)",
                data_type=DataType.DOUBLE,
            ),
            Field(
                identifier="refund_count_ratio",
                display_name="Refund Count Ratio",
                data_type=DataType.DOUBLE,
            ),
            Field(
                identifier="revenue_mismatch",
                display_name="Mismatch Revenue vs Activity",
                data_type=DataType.DOUBLE,
            ),
            Field(
                identifier="avg_txn_amt_ratio",
                display_name="Average Transaction Amount Ratio",
                data_type=DataType.DOUBLE,
            ),
            Field(
                identifier="rapid_load_transfer",
                display_name="Rapid Load & Immediate Transfer",
                data_type=DataType.DOUBLE,
            ),
            Field(
                identifier="mcc",
                display_name="MCC",
                data_type=DataType.STRING,
            ),
            Field(
                identifier="mcc_description",
                display_name="MCC Description",
                data_type=DataType.STRING,
            ),
            Field(
                identifier="state",
                display_name="State (US)",
                data_type=DataType.STRING,
            ),
            Field(
                identifier="risk_score",
                display_name="Merchant Risk Score",
                data_type=DataType.DOUBLE,
            ),
            Field(
                business_type=BusinessType.CURRENCY,
                units="USD",
                identifier="monthly_volume_declared",
                display_name="Monthly Volume Declared",
                data_type=DataType.DOUBLE,
            ),
            Field(
                business_type=BusinessType.CURRENCY,
                units="USD",
                identifier="average_ticket_declared",
                display_name="Average Ticket Declared",
                data_type=DataType.DOUBLE,
            ),
        ],
        ingestion_mode=IngestionMode.UPDATE,
        publish=True,
        primary_key=["merchant_id"],
        num_of_partitions=1,
        num_of_buckets=1,
        data_permission="dpv:demo_merchant",
    )


def entities() -> List[DataSet]:
    return [customer_insights_dataset()]

from typing import List

from thetaray.api.solution import DataSet, DataType, Field, IngestionMode, BusinessType


def customer_insights_dataset() -> DataSet:
    return DataSet(
        identifier="demo_ret_indiv_customer_insights",
        display_name="Customer Insights",
        field_list=[
            Field(
                identifier="customer_id",
                display_name="Customer ID",
                data_type=DataType.STRING,
                encrypted=True,
                audited=True,
            ),
            Field(
                identifier="kyc_classification",
                display_name="KYC Classification",
                data_type=DataType.STRING,
            ),
            Field(
                identifier="kyc_name",
                display_name="Name",
                data_type=DataType.STRING,
                encrypted=True,
                audited=True,
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
                identifier="kyc_null_field",
                display_name="Dummy field",
                data_type=DataType.STRING,
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
                identifier="effective_date",
                display_name="Effective date",
                data_type=DataType.TIMESTAMP,
            ),
        ],
        ingestion_mode=IngestionMode.UPDATE,
        publish=True,
        primary_key=["customer_id"],
        num_of_partitions=1,
        num_of_buckets=1,
        data_permission="dpv:demo_ret_indiv",
    )


def entities() -> List[DataSet]:
    return [customer_insights_dataset()]

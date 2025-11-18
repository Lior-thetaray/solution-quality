from thetaray.api.solution import DataSet, Field, DataType, IngestionMode, BusinessType
from thetaray.api.solution.explainability import (
    Explainability,
    ExplainabilityType,
    ExplainabilityValueType,
    ExplainabilityValueProperties,
    ExplainabilityValuesFilter,
    ExplainabilityValuesFilterType,
    TimeRangeUnit,
)


def customer_monthly_dataset():
    return DataSet(
        identifier='demo_human_trafficking_customer_monthly',
        display_name='Human Trafficking Customer Monthly',
        ingestion_mode=IngestionMode.APPEND,
        publish=True,
        primary_key=['customer_id'],
        data_permission='dpv:demo_ret_indiv',
        num_of_partitions=1,
        num_of_buckets=1,
        occurred_on_field='year_month',
        field_list=[
            Field(identifier='customer_id', display_name='Customer ID', data_type=DataType.STRING),
            Field(identifier='customer_name', display_name='Customer Name', data_type=DataType.STRING, is_explainability_column=True),
            Field(identifier='year_month', display_name='Year Month Date', data_type=DataType.TIMESTAMP),
            Field(identifier='year_month_str', display_name='Year Month', data_type=DataType.STRING),
            Field(
                identifier='income_websites_cnt',
                display_name='Adult Website Income — Distinct Sources',
                data_type=DataType.DOUBLE,
                category='Transaction',
                description='Monthly count of distinct adult‑content websites (matched via +18 keywords list) that send inbound payouts to the customer, based on the counterparty name.',
                dynamic_description=\
                    """
                    Customer **{{ activity.customer_name }}** has done **{{ activity.income_websites_cnt | round(2) | prettify_number }}** distinct transactions to distinct adult-content websites over the last month.
                    """,
                units='USD',
                business_type=BusinessType.CURRENCY,
                explainabilities=[
                    Explainability(
                        identifier="income_websites_cnt_expl",
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=3,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key="trnd",
                                name="Count Income Websites",
                                dynamic_value="income_websites_cnt",
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='income_websites_amt',
                display_name='Adult Website Income — Total Amount',
                data_type=DataType.DOUBLE,
                category='Amount',
                description='Sum of inbound payouts received from adult‑content websites during the month, expressed in the reference currency',
                dynamic_description=\
                    """
                    Customer **{{ activity.customer_name }}** has spent **{{ activity.income_websites_amt | round(2) | prettify_number }}** USD in adult-content websites in the same month.
                    """,
                explainabilities=[
                    Explainability(
                        identifier="income_websites_amt_expl",
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=3,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key="trnd",
                                name="Income Websites Amount",
                                dynamic_value="income_websites_amt",
                                type=ExplainabilityValueType.TREND,
                            ),
                        ]
                    )
                ]
            ),
            Field(
                identifier='ad_agency_out_cnt',
                display_name='Advertising Payments — Transactions',
                data_type=DataType.DOUBLE,
                category='Transactions',
                description='Number of outgoing transfers to merchants classified as advertising businesses during the month',
                dynamic_description=\
                    """
                    Customer **{{ activity.customer_name }}** has done a total of **{{ activity.ad_agency_out_cnt | round(2) | prettify_number }}** outgoing transactions to merchants classified as advertising businesses.
                    """,
                units='USD',
                business_type=BusinessType.CURRENCY,
                explainabilities=[
                    Explainability(
                        identifier="ad_agency_out_cnt_expl",
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=3,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key="trnd",
                                name="Ad Agengy Out Count",
                                dynamic_value="ad_agency_out_cnt",
                                type=ExplainabilityValueType.TREND,
                            ),
                        ]
                    )
                ]
            ),
            Field(
                identifier='ad_agency_out_amt',
                display_name='Advertising Payments — Total Amount',
                data_type=DataType.DOUBLE,
                category='Amount',
                description='Total value of outgoing transfers to advertising‑category merchants (MCC 7311/7333) during the month, in the reference currency',
                dynamic_description="""
                Customer **{{ activity.customer_name }}** has spent **{{ activity.ad_agency_out_amt | round(2) |  prettify_number }}** USD in outgoing transfers to advertising‑category merchants over the past month.
                """,
                explainabilities=[
                    Explainability(
                        identifier='ad_agency_out_amt_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=3,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Monthly Amount to Ad Agency',
                                dynamic_value='ad_agency_out_amt',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='risky_expenses_cnt',
                display_name='Logistics & Hospitality Spend — Transactions',
                data_type=DataType.DOUBLE,
                category='Transactions',
                description='Count of POS purchases at fast‑food (MCC 5814), hotels/motels (MCC 7011), and pharmacies (MCC 5912) during the month',
                dynamic_description="""
                Customer **{{ activity.customer_name }}** has done **{{ activity.risky_expenses_cnt | round(2) | prettify_number }}** transactions of POS purchases at fast-food, hotels/motels and pharmacies over the past month.
                """,
                explainabilities=[
                    Explainability(
                        identifier='risky_expenses_cnt_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=3,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Risky Expenses Count',
                                dynamic_value='risky_expenses_cnt',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='round_amounts',
                display_name='Round Amount Transactions',
                data_type=DataType.DOUBLE,
                category='Transactions',
                description='Count of customer transactions executed in round amounts (e.g., multiples of 1000).',
                dynamic_description="""
                Customer **{{ activity.customer_name }}** executed **{{ activity.round_amounts | round(2) |  prettify_number }}** transactions in round amounts (multiples of $1000) over the past month.
                """,
                explainabilities=[
                    Explainability(
                        identifier='round_amounts_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=3,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Monthly Count of Round Transactions',
                                dynamic_value='round_amounts',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='cnt_distinct_atm',
                display_name='Unusual ATM Activity',
                data_type=DataType.DOUBLE,
                category='Cash',
                description='Unusual number of distinct ATM used by the customer in the same day.',
                dynamic_description=\
                    """
                    Customer **{{ activity.customer_name }}** has used **{{ activity.cnt_distinct_atm | round(2) | prettify_number }}** distinct ATMs in the same month. This number is greater than the population average: **{{ activity.cnt_distinct_atm_pop | round(2) | prettify_number }}**
                    """,
                explainabilities=[
                    Explainability(
                        identifier="cnt_distinct_atm_expl",
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=3,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key="trnd",
                                name="Count Distinct ATMs",
                                dynamic_value="cnt_distinct_atm",
                                type=ExplainabilityValueType.TREND,
                            ),
                        ]
                    )
                ]
            )
            ],
        )


def entities():
    return [customer_monthly_dataset()]

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
        identifier='demo_ret_indiv_customer_monthly',
        display_name='Retail Individual Customer Monthly',
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
                identifier='structuring',
                display_name='Structuring',
                data_type=DataType.DOUBLE,
                category='Cash',
                description='Multiple transactions below the 10K Threshold over the last month.',
                dynamic_description=\
                    """
                    Customer **{{ activity.customer_name }}** has done **{{ activity.structuring | round(2) | prettify_number }}** USD cash transactions below the 10K reporting threshold over the last month.
                    """,
                units='USD',
                business_type=BusinessType.CURRENCY,
                explainabilities=[
                    Explainability(
                        identifier="structuring_expl",
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key="trnd",
                                name="Count Cash Trxs below 10K",
                                dynamic_value="structuring",
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
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key="trnd",
                                name="Count Distinct ATMs",
                                dynamic_value="cnt_distinct_atm",
                                type=ExplainabilityValueType.TREND,
                            ),
                            ExplainabilityValueProperties(
                                key="pop",
                                name="AVG Count Distinct ATMs - Population",
                                dynamic_value="cnt_distinct_atm_pop",
                                type=ExplainabilityValueType.POPULATION
                             ),
                        ]
                    )
                ]
            ),
            Field(identifier='cnt_distinct_atm_pop', display_name='Unusual ATM Activity (Pop Avg)', data_type=DataType.DOUBLE, is_explainability_column=True),
            Field(
                identifier='sum_trx_high_risk',
                display_name='High Risk Jurisdictions',
                data_type=DataType.DOUBLE,
                category='Country Risk',
                description='Unusual value of transactions to high risk jurisdictions.',
                dynamic_description=\
                    """
                    Customer **{{ activity.customer_name }}** has transacted a total of **{{ activity.sum_trx_high_risk | round(2) | prettify_number }}** USD to countries defined as high risks.
                    """,
                units='USD',
                business_type=BusinessType.CURRENCY,
                explainabilities=[
                    Explainability(
                        identifier="sum_trx_high_risk_expl",
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key="trnd",
                                name="High Risk Jurisdictions",
                                dynamic_value="sum_trx_high_risk",
                                type=ExplainabilityValueType.TREND,
                            ),
                            ExplainabilityValueProperties(
                                key="pop",
                                name="AVG High Risk Jurisdictions - Population",
                                dynamic_value="sum_trx_high_risk_pop",
                                type=ExplainabilityValueType.POPULATION
                             ),
                        ]
                    )
                ]
            ),
            Field(identifier='sum_trx_high_risk_pop', display_name='High Risk Jurisdictions (Pop Avg)', data_type=DataType.DOUBLE, is_explainability_column=True),
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
                        time_range_value=6,
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
                identifier='crypto_activity',
                display_name='Cryptocurrency Activity',
                data_type=DataType.DOUBLE,
                category='Cryptocurrency',
                description='Number of cryptocurrency-related transactions detected.',
                dynamic_description="""
                Customer **{{ activity.customer_name }}** performed **{{ activity.crypto_activity | round(2) | prettify_number }}** cryptocurrency transactions over the past month.
                """,
                explainabilities=[
                    Explainability(
                        identifier='crypto_activity_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=3,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Crypto Transaction Count',
                                dynamic_value='crypto_activity',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='deposit_withdrawal_pipe',
                display_name='Deposit-to-Withdrawal Ratio',
                data_type=DataType.DOUBLE,
                category='Pipe Activity',
                description='Ratio of total deposits to total withdrawals, indicating possible “layering” behavior when near 1:1 over a short period.',
                dynamic_description="""
                Customer **{{ activity.customer_name }}** has a deposits-to-withdrawals ratio of **{{ activity.deposit_withdrawal_pipe | round(2) | prettify_number }}** over the past 30 days.
                """,
                explainabilities=[
                    Explainability(
                        identifier='deposit_withdrawal_pipe_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Deposit/Withdrawal Ratio',
                                dynamic_value='deposit_withdrawal_pipe',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='check_deposit_value',
                display_name='Check Deposit Total Value',
                data_type=DataType.DOUBLE,
                category='Check',
                description='Total dollar value of check deposits, highlighting unusually large inflows via checks.',
                dynamic_description="""
                Customer **{{ activity.customer_name }}** deposited **{{ activity.check_deposit_value | round(2) | prettify_number }}** USD in checks over the past month.
                """,
                units='USD',
                business_type=BusinessType.CURRENCY,
                explainabilities=[
                    Explainability(
                        identifier='check_deposit_value_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=1,
                        time_range_unit=TimeRangeUnit.YEAR,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Check Deposit Value',
                                dynamic_value='check_deposit_value',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='overall_activity_spike',
                display_name='Spike in Overall Activity',
                data_type=DataType.DOUBLE,
                category='Transactions',
                description='Significant increase in total number of transactions compared to the customer’s baseline.',
                dynamic_description="""
                Customer **{{ activity.customer_name }}** executed **{{ activity.overall_activity_spike | round(2) | prettify_number }}** transactions in the past month.
                """,
                explainabilities=[
                    Explainability(
                        identifier='overall_activity_spike_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Transaction Volume Trend',
                                dynamic_value='overall_activity_spike',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            ],
        )


def entities():
    return [customer_monthly_dataset()]

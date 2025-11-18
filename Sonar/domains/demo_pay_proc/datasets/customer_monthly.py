from thetaray.api.solution import DataSet, Field, DataType, IngestionMode, BusinessType
from thetaray.api.solution.explainability import (
    Explainability,
    ExplainabilityType,
    ExplainabilityValueType,
    ExplainabilityValueProperties,
    TimeRangeUnit,
)


def customer_monthly_dataset():
    return DataSet(
        identifier='demo_pay_proc_customer_monthly',
        display_name='Payment Processor Customer Monthly',
        ingestion_mode=IngestionMode.APPEND,
        publish=True,
        primary_key=['customer_id'],
        data_permission='dpv:demo_pay_proc',
        num_of_partitions=1,
        num_of_buckets=1,
        occurred_on_field='year_month',
        field_list=[
            Field(identifier='customer_id', display_name='Customer ID', data_type=DataType.STRING),
            Field(identifier='customer_name', display_name='Customer Name', data_type=DataType.STRING, is_explainability_column=True),
            Field(identifier='year_month', display_name='Year Month Date', data_type=DataType.TIMESTAMP),
            Field(identifier='year_month_str', display_name='Year Month', data_type=DataType.STRING),
            Field(identifier='txn_count', display_name='Transactions Count', data_type=DataType.LONG, is_explainability_column=True),
            Field(identifier='population_txn_count', display_name='Population Transactions Count', data_type=DataType.LONG, is_explainability_column=True),
            Field(identifier='avg_amount', display_name='Average USD Amount', data_type=DataType.DOUBLE, is_explainability_column=True),
            Field(identifier='terminals', display_name='Number of Terminals', data_type=DataType.LONG, is_explainability_column=True),
            Field(identifier='reversals', display_name='Reversals Count', data_type=DataType.LONG, is_explainability_column=True),
            Field(identifier='population_reversals', display_name='Population Reversals Count', data_type=DataType.LONG, is_explainability_column=True),
            Field(identifier='rare_currency_count', display_name='Rare Currency Count', data_type=DataType.LONG, is_explainability_column=True),

            # 1. Transaction Count Ratio
            Field(
                identifier='txn_count_ratio',
                display_name='Transaction Count Ratio',
                data_type=DataType.DOUBLE,
                category='Transactions',
                description='Comparison in number of transactions in current month vs. past time frame for the merchant. High values indicate abnormal spikes.',
                dynamic_description="""
                Customer **{{ activity.customer_name }}** recorded **{{ activity.txn_count | round | int }}** transactions this month, significantly higher than historical averages.
                """,
                explainabilities=[
                    Explainability(
                        identifier="txn_count_ratio_expl",
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key="trnd",
                                name="Transaction Volume Trend",
                                dynamic_value="txn_count",
                                type=ExplainabilityValueType.TREND,
                            ),
                            ExplainabilityValueProperties(
                                 key="st",
                                 name="Segment Trend",
                                 dynamic_value="population_txn_count",
                                 type=ExplainabilityValueType.POPULATION,
                            ),
                        ]
                    )
                ]
            ),

            # 2. Reversal Ratio
            Field(
                identifier='reversal_ratio',
                display_name='Reversal Count Ratio',
                data_type=DataType.DOUBLE,
                category='Reversals',
                description='Comparison in number of reversal counts in current month vs. past time frame for the merchant. High spikes suggest suspicious refund patterns.',
                dynamic_description="""
                Customer **{{ activity.customer_name }}** recorded **{{ activity.reversals | round | int }}** reversals this month, significantly higher than historical averages.
                """,
                explainabilities=[
                    Explainability(
                        identifier="reversal_ratio_expl",
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key="trnd",
                                name="Reversal Ratio Trend",
                                dynamic_value="reversals",
                                type=ExplainabilityValueType.TREND),
                            ExplainabilityValueProperties(
                                key="st",
                                name="Segment Trend",
                                dynamic_value="population_reversals",
                                type=ExplainabilityValueType.POPULATION,
                            ),
                        ]
                    )
                ]
            ),

            # 3. Rare Currency Percentage
            Field(
                identifier='rare_currency_pct',
                display_name='Rare Currency Percentage',
                data_type=DataType.DOUBLE,
                category='Currency Risk',
                description='Percentage of transactions in currencies outside the top-20 most used.',
                dynamic_description="""
                Customer **{{ activity.customer_name }}** conducted **{{ activity.rare_currency_pct | round(2) }}%** of transactions in uncommon or rare currencies this month, which may indicate cross-border or unusual payment behavior.
                """,
                explainabilities=[
                    Explainability(
                        identifier="rare_currency_pct_expl",
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key="trnd",
                                name="Rare Currency Count Trend",
                                dynamic_value="rare_currency_count",
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),

            # 4. New Terminal Ratio
            Field(
                identifier='new_terminal_ratio',
                display_name='New Terminal Ratio',
                data_type=DataType.DOUBLE,
                category='Device/Terminal Behavior',
                description='Ratio of newly added terminals this month compared to historical average. Sudden bursts may indicate account compromise or fraud setup.',
                dynamic_description="""
                Customer **{{ activity.customer_name }}** used **{{ activity.terminals | round | int }}** terminals this month, indicating a significant change in the number of terminals compared to historical activity.
                """,
                explainabilities=[
                    Explainability(
                        identifier="new_terminal_ratio_expl",
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key="trnd",
                                name="Terminal Usage Trend",
                                dynamic_value="terminals",
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),

            # 5. Average Transaction Amount Ratio
            Field(
                identifier='avg_txn_amt_ratio',
                display_name='Average Transaction Amount Ratio',
                data_type=DataType.DOUBLE,
                category='Transactions',
                description='Change in average transaction amount compared to historical baseline. Spikes may indicate layering or mule activity.',
                dynamic_description="""
                Customer **{{ activity.customer_name }}** shows an average transaction amount of $**{{ activity.avg_amount | round(2) }}** compared to historical records.
                """,
                units='USD',
                business_type=BusinessType.CURRENCY,
                explainabilities=[
                    Explainability(
                        identifier='avg_txn_amt_ratio_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Average Transaction Amount Trend',
                                dynamic_value='avg_amount',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),

            # 6. Foreign vs Domestic Ratio Change
            Field(
                identifier='domestic_ratio_change',
                display_name='Domestic Ratio Change',
                data_type=DataType.DOUBLE,
                category='Geographic Behavior',
                description='Change in proportion of domestic transactions compared to historical behavior.',
                dynamic_description="""
                Customer **{{ activity.customer_name }}** presents a **{{ activity.domestic_ratio_change | round(2) }}**% of transactions occurring in its country of incorporation.
                """,
                explainabilities=[
                    Explainability(
                        identifier='domestic_ratio_change_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Domestic Ratio Trend',
                                dynamic_value='domestic_ratio_change',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),

            # 7. Pipe Account Behavior Score
            Field(
                identifier='pipe_account_behaviour_score',
                display_name='Pipe Account Behavior Score',
                data_type=DataType.DOUBLE,
                category='Behavioral Risk',
                description='Score representing alternating IN/OUT transaction pattern. High values may indicate pass-through accounts.',
                dynamic_description="""
                Customer **{{ activity.customer_name }}** shows a pipe account behavior score of **{{ activity.pipe_account_behaviour_score | round(2) }}**.
                """,
                explainabilities=[
                    Explainability(
                        identifier='pipe_account_behaviour_score_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Pipe Account Behavior Trend',
                                dynamic_value='pipe_account_behaviour_score',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),

            
        ]
    )


def entities():
    return [customer_monthly_dataset()]

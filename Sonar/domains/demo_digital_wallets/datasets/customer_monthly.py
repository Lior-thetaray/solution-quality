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
        identifier='demo_digital_wallets_customer_monthly',
        display_name='Digital Wallets Individual Customer Monthly',
        ingestion_mode=IngestionMode.APPEND,
        publish=True,
        primary_key=['client_id'],               
        data_permission='dpv:demo_digital_wallets',
        num_of_partitions=1,
        num_of_buckets=1,
        occurred_on_field='year_month',         
        field_list=[
            
            Field(identifier='client_id', display_name='Client ID', data_type=DataType.STRING),
            Field(identifier='client_name', display_name='Client Name', data_type=DataType.STRING, is_explainability_column=True),
            Field(identifier='year_month', display_name='Year Month Date', data_type=DataType.TIMESTAMP),
            Field(identifier='year_month_str', display_name='Year Month', data_type=DataType.STRING),

            
            Field(
                identifier='struct_score',
                display_name='Structuring Score',
                data_type=DataType.DOUBLE,
                category='Transactions',
                description='Multiple deposits below the EUR 1,000 reporting threshold in a short period.',
                dynamic_description="""
                Client **{{ activity.client_name }}** shows a structuring score of **{{ activity.struct_score | round(2) }}**
                based on deposits below the **EUR 1,000** reporting threshold in the last month.
                """,
                explainabilities=[
                    Explainability(
                        identifier='struct_score_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Structuring Score',
                                dynamic_value='struct_score',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='rapid_spend',
                display_name='Rapid Load and Immediate Spend',
                data_type=DataType.DOUBLE,
                category='Velocity',
                description='Large inflow (“top-up”) followed by quick outflow within minutes/hours.',
                dynamic_description="""
                In {{ activity.year_month_str }}, **{{ activity.client_name }}** carried out load-and-spend sequences (funds received followed by withdrawal/spending within 3 hours with an intensity of **{{ (100 * activity.rapid_spend) | round(1) }}%** of total monthly transactions. Higher values indicate a stronger tendency to convert incoming funds immediately.
                """,
                explainabilities=[
                    Explainability(
                        identifier='rapid_spend_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Rapid Load & Spend',
                                dynamic_value='rapid_spend',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='crypto_score',
                display_name='Crypto Usage',
                data_type=DataType.DOUBLE,
                category='Crypto',
                description='Usage intensity of crypto exchanges (count/amount normalized).',
                dynamic_description="""
                During {{ activity.year_month_str }}, **{{ activity.client_name }}** engaged with cryptocurrency exchanges, reaching a crypto usage score of **{{ activity.crypto_score | round(2) }}**. Higher values reflect greater dependency on crypto channels.""",
                explainabilities=[
                    Explainability(
                        identifier='crypto_score_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Crypto Usage',
                                dynamic_value='crypto_score',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='mto_score',
                display_name='Many-to-One',
                data_type=DataType.DOUBLE,
                category='Network',
                description='Convergence of payments to a small set of counterpart hubs.',
                dynamic_description="""
                During {{ activity.year_month_str }}, **{{ activity.client_name }}** channeled most of their funds toward a limited set of recipients, with a many-to-one concentration score of **{{ activity.mto_score | round(2) }}**. Higher values indicate greater dependency on a single beneficiary.
                """,
                explainabilities=[
                    Explainability(
                        identifier='mto_score_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Many-to-One',
                                dynamic_value='mto_score',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='act_spike',
                display_name='Activity Spike',
                data_type=DataType.DOUBLE,
                category='Spike',
                description='Sudden increase in activity vs. historical baseline.',
                dynamic_description="""
                Client **{{ activity.client_name }}** activity spike score is **{{ activity.act_spike | round(2) }}** this month.
                """,
                explainabilities=[
                    Explainability(
                        identifier='act_spike_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Activity Spike',
                                dynamic_value='act_spike',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='pct_domestic',
                display_name='Pct Domestic Transactions',
                data_type=DataType.DOUBLE,
                category='Geography',
                description='Fraction (0–1) of transactions with origin and destination in the same country.',
                dynamic_description="""
               During {{ activity.year_month_str }}, **{{ activity.client_name }}**
conducted **{{ (100 * activity.pct_domestic) | round(0) }}%** of their
transactions domestically. Higher values reflect a focus on local activity,
while lower values suggest stronger international exposure.
                """,
                explainabilities=[
                    Explainability(
                        identifier='pct_domestic_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Pct Domestic Transactions',
                                dynamic_value='pct_domestic',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='rev_ratio',
                display_name='Reversal Ratio',
                data_type=DataType.DOUBLE,
                category='Reversals',
                description='Current month reversals vs. historical baseline.',
                dynamic_description="""
                Client **{{ activity.client_name }}** reversal ratio is **{{ activity.rev_ratio | round(2) }}** this month.
                """,
                explainabilities=[
                    Explainability(
                        identifier='rev_ratio_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Reversal Ratio',
                                dynamic_value='rev_ratio',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),

            
            Field(
                identifier='total_tx_amount',
                display_name='Total Transaction Amount',
                data_type=DataType.DOUBLE,
                category='Amount',
                description='Total amount transacted during the month.',
                dynamic_description="""
                Client **{{ activity.client_name }}** transacted a total of **{{ activity.total_tx_amount | round(2) | prettify_number }}** EUR in the last month.
                """,
                units='EUR',
                business_type=BusinessType.CURRENCY,
                explainabilities=[
                    Explainability(
                        identifier='total_tx_amount_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Total Transaction Amount',
                                dynamic_value='total_tx_amount',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='avg_tx_amount',
                display_name='Average Transaction Amount',
                data_type=DataType.DOUBLE,
                category='Amount',
                description='Average amount per transaction during the month.',
                dynamic_description="""
                Client **{{ activity.client_name }}** average transaction is **{{ activity.avg_tx_amount | round(2) | prettify_number }}** EUR in the last month.
                """,
                units='EUR',
                business_type=BusinessType.CURRENCY,
                explainabilities=[
                    Explainability(
                        identifier='avg_tx_amount_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Average Transaction Amount',
                                dynamic_value='avg_tx_amount',
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

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
        identifier='demo_merchant_customer_monthly',
        display_name='Merchant Acquiring - Merchant Monthly',
        ingestion_mode=IngestionMode.APPEND,
        publish=True,
        primary_key=['merchant_id'],              
        data_permission='dpv:demo_merchant',
        num_of_partitions=1,
        num_of_buckets=1,
        occurred_on_field='year_month',          
        field_list=[
            # ---- Identity / Time ----
            Field(
                identifier='merchant_id',
                display_name='Merchant ID',
                data_type=DataType.STRING,
                description='Unique merchant identifier.'
            ),
            Field(
                identifier='year_month_str',
                display_name='Year Month',
                data_type=DataType.STRING,
                description='Monthly period in YYYY-MM format.'
            ),
            Field(
                identifier='year_month',
                display_name='Year Month Date',
                data_type=DataType.TIMESTAMP,
                description='Monthly period in YYYY-MM format.'
            ),

            # ---- Features with explainability ----
            Field(
                identifier='low_value_trx_ratio',
                display_name='Low Value Transaction Ratio',
                data_type=DataType.DOUBLE,
                category='Velocity and Micro-Charge Patterns',
                description='Ratio of low-value transactions relative to all transactions in the month.',
                dynamic_description="""
{% set pct = (activity.low_value_trx_ratio * 100) | round(1) -%}
Low-value transactions represent {{ pct }}% of all transactions for merchant {{ activity.merchant_id }} in {{ activity.year_month_str }}.
{% if pct >= 5.0 %}
This level is high for typical merchant behavior and may indicate card testing or intentional ticket splitting to avoid thresholds.
{% elif pct >= 2.0 %}
This level is elevated and warrants monitoring for micro-charges or refund-driven cash-out schemes.
{% else %}
This level is within expected ranges for most merchants in comparable verticals.
{% endif %}
""",
                explainabilities=[
                    Explainability(
                        identifier='low_value_trx_ratio_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Low Value Transaction Ratio',
                                dynamic_value='low_value_trx_ratio',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='is_dormant_account',
                display_name='Dormant Account Indicator',
                data_type=DataType.DOUBLE,
                category='Account Lifecycle Anomalies',
                description='Indicator (0–1) of merchant dormancy based on activity thresholds.',
                dynamic_description="""
This feature flags a reactivation pattern: it equals 1 when the merchant shows near-zero activity over a defined dormancy window and then resumes transactions in the current month. Reactivations can indicate sleeper accounts being repurposed for laundering once controls relax or scrutiny fades.

In {{ activity.year_month_str }}, the indicator value for merchant {{ activity.merchant_id }} is {{ activity.is_dormant_account | round(0) }}. A value of 1 suggests prior inactivity followed by renewed activity; 0 indicates no such dormancy/reactivation pattern this month.
""",
                explainabilities=[
                    Explainability(
                        identifier='is_dormant_account_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Dormant Account Indicator',
                                dynamic_value='is_dormant_account',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='spike_of_trx',
                display_name='Transaction Spike',
                data_type=DataType.DOUBLE,
                category='Transaction Volume Anomalies',
                description='Index of transaction spike compared to historical baseline.',
                dynamic_description="""
The indicator quantifies how sharply activity has grown compared with the past months. A value above 1.5 implies volumes 50% higher than recent norms. Such bursts can suggest attempts to push large numbers of transactions through a merchant channel before controls react.

For {{ activity.merchant_id }} in {{ activity.year_month_str }}, the value is {{ activity.spike_of_trx | round(2) }}.
""",
                explainabilities=[
                    Explainability(
                        identifier='spike_of_trx_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Transaction Spike',
                                dynamic_value='spike_of_trx',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='refund_count_ratio',
                display_name='Refund Count Ratio',
                data_type=DataType.DOUBLE,
                category='Chargeback and Refund Signals',
                description='Ratio of refunds relative to all transactions in the month.',
                dynamic_description="""
This feature quantifies refund pressure on the merchant’s flow. Elevated refund proportions may reflect policy abuse, laundering via refunds, or orchestration between buyers and merchant staff. Use operational checks to validate legitimacy of return reasons and timing.

Status for merchant {{ activity.merchant_id }} in {{ activity.year_month_str }}: {{ (activity.refund_count_ratio * 100) | round(1) }}% of transactions ended as refunds. If above internal thresholds, review refund timing, repeated customer profiles, refund-to-sale latency, and refund methods to detect cash-out routes.
""",
                explainabilities=[
                    Explainability(
                        identifier='refund_count_ratio_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Refund Count Ratio',
                                dynamic_value='refund_count_ratio',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='revenue_mismatch',
                display_name='Revenue Mismatch',
                data_type=DataType.DOUBLE,
                category='Sales vs Settlement Integrity',
                description='Misalignment between reported sales and observed settlement amounts in the month.',
                dynamic_description="""
The metric quantifies misalignment between declared revenue and funds observed settling through the payment channel. While modest discrepancies may arise from tips or rounding, elevated values raise AML concerns such as skimming, shadow accounts, or deliberate misstatement.

Current month for {{ activity.merchant_id }} ({{ activity.year_month_str }}): {{ (activity.revenue_mismatch * 100) | round(1) }}% mismatch detected.
""",
                explainabilities=[
                    Explainability(
                        identifier='revenue_mismatch_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Revenue Mismatch',
                                dynamic_value='revenue_mismatch',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='avg_txn_amt_ratio',
                display_name='Average Transaction Amount Ratio',
                data_type=DataType.DOUBLE,
                category='Transaction Amount Distribution',
                description='Ratio of the average transaction amount compared to historical baseline.',
                dynamic_description="""
This feature measures how the current month’s average transaction size compares to the merchant’s ~6-month median. A ratio above 1 means higher than usual tickets; below 1 means smaller than usual. Significant deviations may reveal bundling, upsizing, or conversely micro-charges and ticket splitting.

For merchant {{ activity.merchant_id }} in {{ activity.year_month_str }}, the ratio is {{ activity.avg_txn_amt_ratio | round(2) }}.
""",
                explainabilities=[
                    Explainability(
                        identifier='avg_txn_amt_ratio_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Average Transaction Amount Ratio',
                                dynamic_value='avg_txn_amt_ratio',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='rapid_load_transfer',
                display_name='Rapid Load Transfer',
                data_type=DataType.DOUBLE,
                category='Load-to-Transfer Sequences',
                description='Index of load followed by immediate transfer (inflow followed by outflow within minutes/hours).',
                dynamic_description="""
This feature measures whether funds loaded into the account (via bank transfer or similar) are rapidly sent out within a short window. A value above 1 indicates detection of such sequences. This pattern is risky as it reflects classic layering: money enters and quickly leaves before oversight.

For merchant {{ activity.merchant_id }} in {{ activity.year_month_str }}, the indicator value is {{ activity.rapid_load_transfer | round(0) }}.
""",
                explainabilities=[
                    Explainability(
                        identifier='rapid_load_transfer_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Rapid Load Transfer',
                                dynamic_value='rapid_load_transfer',
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

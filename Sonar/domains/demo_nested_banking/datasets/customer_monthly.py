from typing import List
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
        identifier='demo_nested_banking_customer_monthly',
        display_name='Nested Accounts/Correspondent Banking SWIFT MX Customer Monthly',
        ingestion_mode=IngestionMode.APPEND,
        publish=True,
        primary_key=['customer_id'],
        data_permission='dpv:demo_nested_banking',
        num_of_partitions=1,
        num_of_buckets=1,
        occurred_on_field='year_month',
        field_list=[
            # Core keys
            Field(identifier='customer_id', display_name='Customer ID', data_type=DataType.STRING),
            Field(identifier='customer_name', display_name='Customer Name', data_type=DataType.STRING, is_explainability_column=True),
            Field(identifier='year_month', display_name='Year-Month (date)', data_type=DataType.TIMESTAMP),
            Field(identifier='year_month_str', display_name='Year-Month', data_type=DataType.STRING),

            # Context (aggregates)
            Field(identifier='total_amt', display_name='Total Instructed Amount', data_type=DataType.DOUBLE,
                  business_type=BusinessType.CURRENCY, units='USD', is_explainability_column=True),
            Field(identifier='avg_amt', display_name='Average Instructed Amount', data_type=DataType.DOUBLE,
                  business_type=BusinessType.CURRENCY, units='USD', is_explainability_column=True),
            Field(identifier='new_intr_bic_txn_count', display_name='New Intermediary BIC Txn Count', data_type=DataType.LONG),
            Field(identifier='new_intr_bic_count', display_name='New Intermediary BIC Count', data_type=DataType.LONG),

            # ---------- Triggering features (use these for alerts) ----------
            # 1) Activity spike
            Field(
                identifier='txn_count',
                display_name='Transactions Count',
                data_type=DataType.LONG,
                category='Activity',
                description='Number of transactions this month for the respondent.',
                explainabilities=[
                    Explainability(
                        identifier='txn_count_trend',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Transactions Trend',
                                dynamic_value='txn_count',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),

            # 2) Not Seen Currency
            Field(
                identifier='new_currency_count',
                display_name='New Currency Count',
                data_type=DataType.LONG,
                category='Currency Risk',
                description='Count of transactions that used a currency not seen in the lookback window for this customer.',
                explainabilities=[
                    Explainability(
                        identifier='new_currency_trend',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='New Currency Trend',
                                dynamic_value='new_currency_count',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),

            # 3) Not Seen BIC (intermediary-only, distinct)
            Field(
                identifier='new_intr_bic_unique_count',
                display_name='New Intermediary BIC (Unique) Count',
                data_type=DataType.LONG,
                category='Routing Changes',
                description='Number of distinct intermediary BIC8s first seen this month for this customer.',
                explainabilities=[
                    Explainability(
                        identifier='new_intr_bic_unique_trend',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='New Intermediary BIC (Unique) Trend',
                                dynamic_value='new_intr_bic_unique_count',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),

            # 4) High-Risk Jurisdictions
            Field(
                identifier='high_risk_count',
                display_name='High-Risk Jurisdiction Count',
                data_type=DataType.LONG,
                category='Jurisdiction Risk',
                description='Transactions touching high-risk jurisdictions this month.',
                explainabilities=[
                    Explainability(
                        identifier='high_risk_trend',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='High-Risk Jurisdiction Trend',
                                dynamic_value='high_risk_count',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),

            # 5) Round Amount Ratio (corporates)
            Field(
                identifier='round_amount_ratio',
                display_name='Round Amount Ratio',
                data_type=DataType.DOUBLE,
                category='Amount Patterns',
                description='Share of corporate-originated payments with round-thousand amounts.',
                explainabilities=[
                    Explainability(
                        identifier='round_amount_ratio_trend',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Round Amount Ratio Trend',
                                dynamic_value='round_amount_ratio',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),

            # ---------- Additional context (non-trigger) ----------
            Field(identifier='many_to_one_count', display_name='Many-to-One Counterparties', data_type=DataType.LONG,
                  description='Distinct originators sending to this customer in the month.', is_explainability_column=True),
            Field(identifier='pipe_account_behaviour_score', display_name='Pipe Account Behaviour Score', data_type=DataType.DOUBLE,
                  description='IN/OUT alternation rate within the month.', is_explainability_column=True),

            # Z-scores from MX aggregator (kept for diagnostics/optional use)
            Field(identifier='z_txn_count', display_name='Z: Transactions Count', data_type=DataType.DOUBLE),
            Field(identifier='z_total_amt', display_name='Z: Total Instructed Amount', data_type=DataType.DOUBLE),
            Field(identifier='z_new_currency_count', display_name='Z: New Currency Count', data_type=DataType.DOUBLE),
            Field(identifier='z_new_intr_bic_txn_count', display_name='Z: New Intermediary BIC – Txn Count', data_type=DataType.DOUBLE),
            Field(identifier='z_new_intr_bic_count', display_name='Z: New Intermediary BIC – Occurrence Count', data_type=DataType.DOUBLE),
            Field(identifier='z_new_intr_bic_unique_count', display_name='Z: New Intermediary BIC – Unique Count', data_type=DataType.DOUBLE),
            Field(identifier='z_high_risk_count', display_name='Z: High-Risk Jurisdiction Count', data_type=DataType.DOUBLE),
            Field(identifier='z_round_amount_ratio', display_name='Z: Round Amount Ratio', data_type=DataType.DOUBLE),
        ]
    )


def entities() -> List[DataSet]:
    return [customer_monthly_dataset()]

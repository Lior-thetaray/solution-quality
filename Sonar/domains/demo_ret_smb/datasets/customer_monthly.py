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
        identifier='demo_ret_smb_customer_monthly',
        display_name='Retail smbidual Customer Monthly',
        ingestion_mode=IngestionMode.APPEND,
        publish=True,
        primary_key=['customer_id'],
        data_permission='dpv:demo_ret_smb',
        num_of_partitions=1,
        num_of_buckets=1,
        occurred_on_field='year_month',
        field_list=[
            Field(identifier='customer_id', display_name='Customer ID', data_type=DataType.STRING),
            Field(identifier='customer_name', display_name='Customer Name', data_type=DataType.STRING, is_explainability_column=True),
            Field(identifier='year_month', display_name='Year Month Date', data_type=DataType.TIMESTAMP),
            Field(identifier='year_month_str', display_name='Year Month', data_type=DataType.STRING),
            Field(
                identifier='pipe_accnt_behv',
                display_name='Pipe Account Behaviour',
                data_type=DataType.DOUBLE,
                category='Pipe Activity',
                description='Ratio of incoming to outgoing amounts for the account; unusually high values signal “pipe” activity—funds merely pass through',
                dynamic_description=\
                    """
                    Customer **{{ activity.customer_name }}** has done **{{ activity.pipe_accnt_behv | round(2) | prettify_number }}** ratio of incoming to outgoing amount.
                    """,
                units='USD',
                business_type=BusinessType.CURRENCY,
                explainabilities=[
                    Explainability(
                        identifier="pipe_accnt_behv_expl",
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key="trnd",
                                name="Pipe in ratio of incoming to outgoing amounts",
                                dynamic_value="pipe_accnt_behv",
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='tax_heaven_jurisd',
                display_name='Tax Heaven Jurisdiction',
                data_type=DataType.DOUBLE,
                category='Country Risk',
                description='Count of monthly transactions involving counterparties in tax-haven jurisdictions.',
                units='USD',
                business_type=BusinessType.CURRENCY,
                dynamic_description=\
                    """
                    Customer **{{ activity.customer_name }}** has done **{{ activity.tax_heaven_jurisd | round(2) | prettify_number }}** USD amount to Tax Heaven Jurisdictions.
                    """,
                explainabilities=[
                    Explainability(
                        identifier="tax_heaven_jurisd_expl",
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key="trnd",
                                name="Amount to Tax Heaven Jurisdictions",
                                dynamic_value="tax_heaven_jurisd",
                                type=ExplainabilityValueType.TREND),
                            ExplainabilityValueProperties(
                                key="pop",
                                name="AVG High Risk Jurisdiction - Population",
                                dynamic_value="tax_heaven_jurisd_pop",
                                type=ExplainabilityValueType.POPULATION
                             )
                        ]
                    )
                ]
            ),
            Field(identifier='tax_heaven_jurisd_pop', display_name='High Risk Jurisdictions (Pop Avg)', data_type=DataType.DOUBLE, is_explainability_column=True),
            
            Field(
                identifier='spike_of_trx',
                display_name='Spike of Transactions',
                data_type=DataType.DOUBLE,
                category='Transactions',
                description='Total number of transactions in the month; sharp increases reveal bursts of atypical activity.',
                dynamic_description=\
                    """
                    Customer **{{ activity.customer_name }}** has transacted a total of **{{ activity.spike_of_trx | round(2) | prettify_number }}** to countries defined as high risks.
                    """,
                explainabilities=[
                    Explainability(
                        identifier="spike_of_trx_expl",
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key="trnd",
                                name="Spike of Transactions",
                                dynamic_value="spike_of_trx",
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),

            Field(
                identifier='many_to_one',
                display_name='Many To One',
                data_type=DataType.DOUBLE,
                category='Transactions',
                description='Count of unique counterparties that send to the same customer.',
                dynamic_description="""
                Customer **{{ activity.customer_name }}** has received from **{{ activity.many_to_one }}** unique counterparties over the month.
                """,
                explainabilities=[
                    Explainability(
                        identifier='many_to_one_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Monthly Count of unique sender counterparties',
                                dynamic_value='many_to_one',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='one_to_many',
                display_name='One To Many',
                data_type=DataType.DOUBLE,
                category='Transactions',
                description='Count of unique counterparties that receive to the same customer.',
                dynamic_description="""
                 Customer **{{ activity.customer_name }}** has sent to **{{ activity.one_to_many }}** unique counterparties over the month
                """,
                explainabilities=[
                    Explainability(
                        identifier='one_to_many_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=3,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Monthly Count of unique receiver counterparties',
                                dynamic_value='one_to_many',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='avg_tx_amount_monthly',
                display_name='AVG Transaction Amount in the month.',
                data_type=DataType.DOUBLE,
                category='Transactions',
                description='Average transaction amount (USD) during the month—helps spot sudden shifts in ticket size.',
                dynamic_description="""
                Customer **{{ activity.customer_name }}** has an transacted an average of **{{ activity.avg_tx_amount_monthly | round(2) | prettify_number }}** USD over the past 30 days.
                """,
                units='USD',
                business_type=BusinessType.CURRENCY,
                explainabilities=[
                    Explainability(
                        identifier='avg_tx_amount_monthly_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='AVG Transaction Amoun in the month',
                                dynamic_value='avg_tx_amount_monthly',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='pct_domestic_transactions',
                display_name='PCT of Domestic Transactions',
                data_type=DataType.DOUBLE,
                category='Transactions',
                description='Fraction (0–1) of transactions whose origin and destination stay within the customer’s tax-residence country.',
                dynamic_description="""
                Customer **{{ activity.customer_name }}** has done **{{ activity.pct_domestic_transactions | round(2) | prettify_number }}** in the same tax residency country over the past month.
                """,
                units='USD',
                business_type=BusinessType.CURRENCY,
                explainabilities=[
                    Explainability(
                        identifier='pct_domestic_transactions_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=1,
                        time_range_unit=TimeRangeUnit.YEAR,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Domestic Transactions PTC Value',
                                dynamic_value='pct_domestic_transactions',
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='atm_withdrawal_ratio',
                display_name='ATM Withdrawal Ratio',
                data_type=DataType.DOUBLE,
                category='ATM',
                description='Fraction (0–1) of debit transactions executed as ATM cash withdrawals.',
                dynamic_description="""
                Customer **{{ activity.customer_name }}** has done **{{ activity.atm_withdrawal_ratio | round(2) | prettify_number }}** of ATM withdrawals of its total transactions in the past month.
                """,
                explainabilities=[
                    Explainability(
                        identifier='atm_withdrawal_ratio_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='Ratio of ATM WithDrawal',
                                dynamic_value='atm_withdrawal_ratio',
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

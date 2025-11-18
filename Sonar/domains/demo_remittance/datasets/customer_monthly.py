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
        identifier='demo_remittance_customer_monthly',
        display_name='Remittance Individual Customer Monthly',
        ingestion_mode=IngestionMode.APPEND,
        publish=True,
        primary_key=['customer_id'],
        data_permission='dpv:demo_remittance',
        num_of_partitions=1,
        num_of_buckets=1,
        occurred_on_field='year_month',
        field_list=[
            Field(identifier='customer_id', display_name='Customer ID', data_type=DataType.STRING),
            Field(identifier='customer_name', display_name='Customer Name', data_type=DataType.STRING, is_explainability_column=True),
            Field(identifier='year_month', display_name='Year Month Date', data_type=DataType.TIMESTAMP),
            Field(identifier='year_month_str', display_name='Year Month', data_type=DataType.STRING),
            Field(
                identifier='multpl_tx_bl_lim',
                display_name='Multiple Transactions Below Limit',
                data_type=DataType.LONG,
                category='Transactions',
                description='Multiple transactions below the 10K Threshold in a short period of time (3 days).',
                dynamic_description=\
                    """
                    Customer **{{ activity.customer_name }}** has sent **{{ activity.multpl_tx_bl_lim | round(2) | prettify_number }}** remittance  below the 10K reporting threshold.
                    """,
                explainabilities=[
                    Explainability(
                        identifier="multpl_tx_bl_lim_expl",
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key="trnd",
                                name="Count Remittance Trxs below 10K",
                                dynamic_value="multpl_tx_bl_lim",
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='vel_spike',
                display_name='Velocity Spike',
                data_type=DataType.LONG,
                category='Spike',
                description='Frequent money transfers in a short period to the same recipient or different recipients.',
                dynamic_description=\
                    """
                    Customer **{{ activity.customer_name }}** has done **{{ activity.vel_spike | round(2) | prettify_number }}** frequent money transfer in a short period (3 days) in the last month.
                    """,
                explainabilities=[
                    Explainability(
                        identifier="vel_spike_expl",
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key="trnd",
                                name="Velocity Spike",
                                dynamic_value="vel_spike",
                                type=ExplainabilityValueType.TREND,
                            )
                        ]
                    )
                ]
            ),
            Field(
                identifier='multi_party_actv',
                display_name='Multi Party Activity',
                data_type=DataType.LONG,
                category='Activity',
                description='One individual receiving remittances from multiple unrelated senders or sending funds to multiple recipients.',
                dynamic_description=\
                    """
                    Customer **{{ activity.customer_name }}** has transacted with a total of **{{ activity.multi_party_actv | round(2) | prettify_number }}** unique counterparties.
                    """,
                explainabilities=[
                    Explainability(
                        identifier="multi_party_actv_expl",
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key="trnd",
                                name="Multiple Parties",
                                dynamic_value="multi_party_actv",
                                type=ExplainabilityValueType.TREND,
                            ),
                        ]
                    )
                ]
            ),
            Field(
                identifier='hr_jurid_vol',
                display_name='High Risk Jurisdiction Transactions',
                data_type=DataType.DOUBLE,
                category='Transactions',
                description='Frequent remittances to or from countries with weak AML controls or high corruption risks.',
                dynamic_description="""
                Customer **{{ activity.customer_name }}** has executed **{{ activity.hr_jurid_vol }}** transactions to high risk jurisdictions over the past month.
                """,

                explainabilities=[
                    Explainability(
                        identifier='hr_jurid_vol_expl',
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key='trnd',
                                name='High Risk Jurisdiction Transactions',
                                dynamic_value='hr_jurid_vol',
                                type=ExplainabilityValueType.TREND,
                            ),
                            ExplainabilityValueProperties(
                                key="pop",
                                name="AVG High Risk Jurisdiction Transactions - Population",
                                dynamic_value="hr_jurid_vol_pop",
                                type=ExplainabilityValueType.POPULATION
                             ),
                        ]
                    )
                ]
            ),
            Field(identifier='hr_jurid_vol_pop', display_name='High Risk Jurisdictions Transactions (Pop Avg)', data_type=DataType.DOUBLE, is_explainability_column=True),

            Field(
                identifier='total_tx_amount',
                display_name='Total Transaction Amount',
                data_type=DataType.DOUBLE,
                category='Amount',
                description='Total amount transacted over the past month.',
                dynamic_description="""
                Customer **{{ activity.customer_name }}** has transacted an total of **{{ activity.total_tx_amount | round(2) | prettify_number }}** USD over the past 30 days.
                """,
                units='USD',
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
                description='Average amount transacted over the past month.',
                dynamic_description="""
                Customer **{{ activity.customer_name }}** has transacted an average of **{{ activity.avg_tx_amount | round(2) | prettify_number }}** USD over the past 30 days.
                """,
                units='USD',
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
            )
        ]
    )


def entities():
    return [customer_monthly_dataset()]

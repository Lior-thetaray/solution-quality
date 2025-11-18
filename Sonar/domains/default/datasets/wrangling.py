from typing import List

from thetaray.api.solution import DataSet, DataType, Field, IngestionMode, BusinessType
from thetaray.api.solution.explainability import (
    Explainability,
    ExplainabilityType,
    ExplainabilityValueType,
    ExplainabilityValueProperties,
    ExplainabilityValuesFilter,
    ExplainabilityValuesFilterType,
    TimeRangeUnit,
)


def wrangling_dataset() -> DataSet:
    return DataSet(
        identifier="wrangling",
        display_name="wrangling",
        field_list=[
            Field(
                identifier="account_id",
                display_name="Account ID",
                data_type=DataType.STRING,
                encrypted=True,
                audited=True,
                description="This is the unique identifier of the account.",
            ),
            Field(
                display_name="Party ID",
                data_type=DataType.STRING,
                identifier="party_id",
                description="This is the unique identifier of the party.",
            ),
            Field(
                display_name="Party Accounts",
                data_type=DataType.STRING,
                identifier="party_accounts",
                encrypted=True,
                audited=True,
                description="This is the aggregated list of accounts for the party.",
            ),
            Field(
                display_name="District ID Bank",
                dynamic_description="""
                    This is value of the district ID of the bank - {{ activity.district_id_bank }}.
                """,
                data_type=DataType.LONG,
                identifier="district_id_bank",
                description="This is the unique identifier of the district of the bank.",
            ),
            Field(
                display_name="Frequency",
                data_type=DataType.STRING,
                identifier="frequency",
                category="Additional Features",
                description="This is the frequency of something for the account.",
            ),
            Field(
                display_name="Date Acct",
                data_type=DataType.TIMESTAMP,
                identifier="date_acct",
                description="This is the date of the account activation.",
            ),
            Field(
                display_name="Disp ID",
                data_type=DataType.LONG,
                identifier="disp_id",
                description="This is the unique identifier of the disposition.",
            ),
            Field(
                display_name="Client ID",
                data_type=DataType.LONG,
                identifier="client_id",
                description="This is the unique identifier of the client.",
            ),
            Field(
                display_name="Type Disp",
                data_type=DataType.STRING,
                identifier="type_disp",
                category="Additional Features",
                description="This is the type of the disposition.",
            ),
            Field(
                display_name="Loan ID",
                data_type=DataType.LONG,
                identifier="loan_id",
                description="This is the unique identifier of the loan.",
            ),
            Field(
                display_name="Date Loan",
                data_type=DataType.TIMESTAMP,
                identifier="date_loan",
                description="This is the date of the loan.",
            ),
            Field(
                display_name="Amount",
                data_type=DataType.LONG,
                identifier="amount",
                indexed=True,
                category="Transactions",
                description="This is the aggregated amount of transactions for the account within the analysis period.",
                units="EUR",
                business_type=BusinessType.CURRENCY,
                dynamic_description="""
                    {% set total_6m = explainability.amount.hist_expl | sum(attribute='a') %}
                    {% set md = metadata.amount %}
                    {% set expl_md = md.explainabilities.hist_expl %}
                    {% set avg_monthly = total_6m / expl_md.time_range_value %}
                    Customer **{{ activity.name }} spent {{ activity.amount | prettify_number }}{{ md.units | currency_symbol }}** for analysis 
                    period and **{{ total_6m | round(2) | prettify_number }}{{ md.units | currency_symbol }}** in the last {{ expl_md.time_range_value }} 
                    {{ expl_md.time_range_unit | lower }}s.\n 
                    This is **{{ avg_monthly | prettify_number }}{{ md.units | currency_symbol }} on average per {{ expl_md.time_range_unit | lower }}**.\n
                    {% set percentage_difference = ((activity.amount - avg_monthly) / avg_monthly * 100) | round(2) %}
                    Which is {{ percentage_difference }}% different than the average monthly spending.
                """,
                explainabilities=[
                    Explainability(
                        identifier="hist_expl",
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key="a",
                                name="Transactions Trend",
                                dynamic_value="amount",
                                type=ExplainabilityValueType.TREND,
                            ),
                            ExplainabilityValueProperties(
                                key="st",
                                name="Segment Trend",
                                dynamic_value="population_amount",
                                type=ExplainabilityValueType.POPULATION,
                            ),
                            ExplainabilityValueProperties(
                                key="tr",
                                name="Threshold",
                                static_value=50_000,
                                type=ExplainabilityValueType.THRESHOLD,
                            ),
                        ],
                    )
                ],
            ),
            Field(
                display_name="Population Amount",
                data_type=DataType.DOUBLE,
                identifier="population_amount",
                description="This is the aggregated amount of transactions for the segment within the analysis period.",
            ),
            Field(
                display_name="Duration",
                data_type=DataType.LONG,
                identifier="duration",
                category="Transactions",
                description="This is number of months the loan is for.",
            ),
            Field(
                display_name="Payments",
                data_type=DataType.LONG,
                identifier="payments",
                indexed=True,
                units="USD",
                business_type=BusinessType.CURRENCY,
                category="Transactions",
                description="This is the aggregated amount of payments for the account within the analysis period.",
                dynamic_description="""
                    {% set total_90d = explainability.payments.hist_expl | sum(attribute='p') %}
                    {% set pay_md = metadata.payments %}
                    {% set expl_md = pay_md.explainabilities.hist_expl %}
                    {% set avg_daily = total_90d / expl_md.time_range_value %}
                    Customer **{{ activity.name }}** made **{{ activity.payments | prettify_number }}{{ pay_md.units | currency_symbol }}**
                    in payments for the analysis period and **{{ total_90d | prettify_number }}{{ pay_md.units | currency_symbol }}**
                    in the last {{ expl_md.time_range_value }} {{ expl_md.time_range_unit | lower }}s.\n
                    {% set percentage = (total_90d / activity.amount * 100) | round(2) %}
                    This is {{ percentage }}% of the total amount of the loan 
                    ({{ activity.amount | prettify_number }}{{ pay_md.units | currency_symbol }}).\n
                """,
                explainabilities=[
                    Explainability(
                        identifier="hist_expl",
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=90,
                        time_range_unit=TimeRangeUnit.DAY,
                        values=[
                            ExplainabilityValueProperties(
                                key="p",
                                name="Payments Trend",
                                dynamic_value="payments",
                                type=ExplainabilityValueType.TREND,
                            ),
                            ExplainabilityValueProperties(
                                key="dt",
                                name="Payments Threshold",
                                dynamic_value="population_amount",
                                type=ExplainabilityValueType.THRESHOLD,
                            ),
                        ],
                    ),
                ],
            ),
            Field(
                display_name="Response",
                data_type=DataType.LONG,
                identifier="response",
                description="c11-description",
            ),
            Field(
                display_name="Birth Number",
                data_type=DataType.LONG,
                identifier="birth_number",
                category="Additional Features",
                description="This is the birth number of the client.",
            ),
            Field(
                display_name="District ID Client",
                data_type=DataType.LONG,
                identifier="district_id_client",
                description="This is the unique identifier of the district of the client.",
            ),
            Field(
                display_name="Card ID",
                data_type=DataType.LONG,
                identifier="card_id",
                description="This is the unique identifier of the card.",
            ),
            Field(
                display_name="Type Card",
                data_type=DataType.STRING,
                identifier="type_card",
                category="Additional Features",
                description="This is the type of the card.",
            ),
            Field(
                display_name="Min 1",
                data_type=DataType.DOUBLE,
                identifier="min1",
                category="Aggregation 1",
                description="This is the minimum value of something.",
            ),
            Field(
                display_name="Max 1",
                data_type=DataType.DOUBLE,
                identifier="max1",
                category="Aggregation 1",
                description="This is the maximum value of something.",
            ),
            Field(
                display_name="Mean 1",
                data_type=DataType.DOUBLE,
                identifier="mean1",
                category="Aggregation 1",
                description="This is the mean value of something.",
            ),
            Field(
                display_name="Min 2",
                data_type=DataType.DOUBLE,
                identifier="min2",
                category="Aggregation 2",
                description="This is the second minimum value of something.",
            ),
            Field(
                display_name="Max 2",
                data_type=DataType.DOUBLE,
                identifier="max2",
                category="Aggregation 2",
                description="This is the second maximum value of something.",
            ),
            Field(
                display_name="Mean 2",
                data_type=DataType.DOUBLE,
                identifier="mean2",
                category="Aggregation 2",
                description="This is the second mean value of something.",
            ),
            Field(
                display_name="Min 3",
                data_type=DataType.DOUBLE,
                identifier="min3",
                category="Aggregation 3",
                description="This is the third minimum value of something.",
            ),
            Field(
                display_name="Max 3",
                data_type=DataType.DOUBLE,
                identifier="max3",
                category="Aggregation 3",
                description="This is the third maximum value of something.",
            ),
            Field(
                display_name="Mean 3",
                data_type=DataType.DOUBLE,
                identifier="mean3",
                category="Aggregation 3",
                description="This is the third mean value of something.",
            ),
            Field(
                display_name="Min 4",
                data_type=DataType.DOUBLE,
                identifier="min4",
                category="Aggregation 4",
                description="This is the fourth minimum value of something.",
            ),
            Field(
                display_name="Max 4",
                data_type=DataType.DOUBLE,
                identifier="max4",
                category="Aggregation 4",
                description="This is the fourth maximum value of something.",
            ),
            Field(
                display_name="Mean 4",
                data_type=DataType.DOUBLE,
                identifier="mean4",
                category="Aggregation 4",
                description="This is the fourth mean value of something.",
            ),
            Field(
                display_name="Min 5",
                data_type=DataType.DOUBLE,
                identifier="min5",
                category="Aggregation 5",
                description="This is the fifth minimum value of something.",
            ),
            Field(
                display_name="Max 5",
                data_type=DataType.DOUBLE,
                identifier="max5",
                category="Aggregation 5",
                description="This is the fifth maximum value of something.",
            ),
            Field(
                display_name="Mean 5",
                data_type=DataType.DOUBLE,
                identifier="mean5",
                category="Aggregation 5",
                description="This is the fifth mean value of something.",
            ),
            Field(
                display_name="Min 6",
                data_type=DataType.DOUBLE,
                identifier="min6",
                category="Aggregation 6",
                description="This is the sixth minimum value of something.",
            ),
            Field(
                display_name="Max 6",
                data_type=DataType.DOUBLE,
                identifier="max6",
                category="Aggregation 6",
                description="This is the sixth maximum value of something.",
            ),
            Field(
                display_name="Mean 6",
                data_type=DataType.DOUBLE,
                identifier="mean6",
                category="Aggregation 6",
                description="This is the sixth mean value of something.",
            ),
            Field(
                identifier="has_card",
                display_name="Customer Has Card",
                data_type=DataType.LONG,
                category="Additional Features",
                description="This is the flag if the customer has a card.",
                business_type=BusinessType.CURRENCY,
                units="USD",
                dynamic_description="""
                    Customer **{{ activity.name }}** born on **{{ activity.birth_number }}**
                    {% if activity.has_card > 0 %}
                        has a card.
                    {% else %}
                        does not have a card.
                    {% endif %}
                """,
                explainabilities=[
                    Explainability(
                        identifier="binary_expl",
                        type=ExplainabilityType.BINARY,
                        values=[
                            ExplainabilityValueProperties(
                                key="cn",
                                name="Customer Name",
                                dynamic_value="name",
                                type=ExplainabilityValueType.TITLE,
                            ),
                            ExplainabilityValueProperties(
                                key="ca",
                                name="Customer Address",
                                dynamic_value="address",
                                type=ExplainabilityValueType.DESCRIPTION,
                            ),
                            ExplainabilityValueProperties(
                                key="chs",
                                name="Customer has card",
                                dynamic_value="has_card",
                            ),
                            ExplainabilityValueProperties(
                                key="ts",
                                name="Transactions Sum",
                                dynamic_value="amount",
                                type=ExplainabilityValueType.SUM,
                            ),
                            ExplainabilityValueProperties(
                                key="cbn",
                                name="Customer Birth Number",
                                dynamic_value="birth_number",
                            ),
                        ],
                    )
                ],
            ),
            Field(
                data_type=DataType.BOOLEAN,
                identifier="high_risk_countries",
                display_name="High Risk Countries",
                category="Matches",
                description="Accumulation of transactions sent to high risk countries.",
                dynamic_description="""
                    {% set expl_data = explainability.high_risk_countries.hrc_categorical %}
                    {% set high_risk_countries = expl_data | selectattr('cr', 'in', ['High', 'Very High']) | list %}
                    {% set sum_high_risk = high_risk_countries | sum(attribute='s') %}
                    {% set total_transaction_sum = activity.amount %}
                    {% set percentage = (sum_high_risk / total_transaction_sum * 100) | round(2) %}
                    {% set country_count = high_risk_countries | length %}
                    {% set highest_amount_country = high_risk_countries | sort(attribute='s', reverse=True) | first %}
                    The sum of customer's transactions to countries with risk defined 
                    as High or Very High is **{{ sum_high_risk | prettify_number }}{{ metadata.amount.units | currency_symbol }}**. 
                    It is {{ percentage }}% of the total transaction sum for the analysis period. 
                    In total, there are {{ country_count }} countries like this. 
                    The highest amount was sent to 
                    **{{ highest_amount_country.ct | country_full }} - 
                    {{ highest_amount_country.s | prettify_number }}{{ metadata.amount.units | currency_symbol }}**.
                """,
                business_type=BusinessType.CURRENCY,
                units="EUR",
                explainabilities=[
                    Explainability(
                        identifier="hrc_categorical",
                        type=ExplainabilityType.CATEGORICAL,
                        category_lbl="ct",
                        category_var="s",
                        json_column_reference="high_risk_countries_explainability",
                        priority=2,
                        values=[
                            ExplainabilityValueProperties(
                                key="ct",
                                name="Receiver Country",
                                type=ExplainabilityValueType.COUNTRY,
                            ),
                            ExplainabilityValueProperties(
                                key="s",
                                name="Transactions Sum",
                                type=ExplainabilityValueType.SUM,
                            ),
                            ExplainabilityValueProperties(
                                key="c",
                                name="Transactions Count",
                                type=ExplainabilityValueType.COUNT,
                            ),
                            ExplainabilityValueProperties(
                                key="cr",
                                name="Criticality",
                                type=ExplainabilityValueType.CRITICALITY,
                                filter=ExplainabilityValuesFilter(
                                    type=ExplainabilityValuesFilterType.EQ,
                                    values=["Very High", "High"],
                                ),
                            ),
                        ],
                    ),
                    Explainability(
                        identifier="hrc_behavioral",
                        type=ExplainabilityType.BEHAVIORAL,
                        time_range_value=6,
                        time_range_unit=TimeRangeUnit.MONTH,
                        category_lbl="ct",
                        category_var="s",
                        json_column_reference="high_risk_countries_explainability",
                        priority=1,
                        values=[
                            ExplainabilityValueProperties(
                                key="ct",
                                name="Country of Receiver",
                                type=ExplainabilityValueType.COUNTRY,
                            ),
                            ExplainabilityValueProperties(
                                key="s",
                                name="Sum of Transactions",
                                type=ExplainabilityValueType.TREND,
                            ),
                            ExplainabilityValueProperties(
                                key="cr",
                                name="Criticality",
                                type=ExplainabilityValueType.CRITICALITY,
                            ),
                            ExplainabilityValueProperties(
                                key="c",
                                name="Count of Transactions",
                                type=ExplainabilityValueType.COUNT,
                            ),
                        ],
                    ),
                ],
            ),
            Field(
                data_type=DataType.BOOLEAN,
                identifier="keyword_matches",
                display_name="Keyword Matches",
                category="Matches",
                description="Accumulation of transactions witch matching keywords per keyword group.",
                dynamic_description="""
                    {% set expl_data = explainability.keyword_matches.km_categorical %}
                    The sum of customer’s transactions witch matching keywords is 
                    {{ expl_data | sum(attribute='s') | prettify_number }}{{ metadata.keyword_matches.units | currency_symbol }}.
                    Keywords are: {{ expl_data | map(attribute='kw') | join(', ') }}.
                """,
                business_type=BusinessType.CURRENCY,
                units="EUR",
                explainabilities=[
                    Explainability(
                        identifier="km_categorical",
                        type=ExplainabilityType.CATEGORICAL,
                        category_lbl="kw",
                        category_var="s",
                        json_column_reference="keyword_matches_explainability",
                        values=[
                            ExplainabilityValueProperties(
                                key="kw",
                                name="Keyword Group",
                            ),
                            ExplainabilityValueProperties(
                                key="s",
                                name="Sum of Transactions",
                                type=ExplainabilityValueType.SUM,
                            ),
                            ExplainabilityValueProperties(
                                key="c",
                                name="Transactions Count",
                                type=ExplainabilityValueType.COUNT,
                            ),
                        ],
                    )
                ],
            ),
            Field(
                data_type=DataType.STRING,
                identifier="high_risk_countries_explainability",
                display_name="High Risk Countries Explainability",
                is_explainability_column=True,
            ),
            Field(
                data_type=DataType.STRING,
                identifier="keyword_matches_explainability",
                display_name="Keyword Matches Explainability",
                is_explainability_column=True,
            ),
            Field(
                display_name="name",
                data_type=DataType.STRING,
                identifier="name",
                encrypted=True,
                is_explainability_column=True,
            ),
            Field(
                display_name="address",
                data_type=DataType.STRING,
                identifier="address",
                encrypted=True,
                is_explainability_column=True,
            ),
        ],
        ingestion_mode=IngestionMode.APPEND,
        publish=True,
        primary_key=["account_id"],
        num_of_partitions=4,
        num_of_buckets=7,
        occurred_on_field="date_loan",
        data_permission="dpv:public",
    )


def entities() -> List[DataSet]:
    return [wrangling_dataset()]

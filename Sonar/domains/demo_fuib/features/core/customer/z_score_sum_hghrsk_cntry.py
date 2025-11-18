from typing import List, Set, Dict
from pyspark.sql import DataFrame, Window, functions as f, Column

from common.libs.feature_engineering import AggFeature, FeatureDescriptor
from common.libs.zscore import enrich_with_z_score

import typing
from collections import OrderedDict

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


class SumHghrskCntry(AggFeature, FeatureDescriptor):

    @property
    def identifier(self) -> str:
        return 'z_score_sum_hghrsk_cntry'

    @property
    def version(self) -> int:
        return 1

    @property
    def description(self) -> str:
        return "Unusual value of incoming/outgoing transactions involving High-Risk Juristictions compared to the customer historical behavior in the last 12 months"

    @property
    def required_columns(self) -> Set[str]:
        return {'customer_id', 'month_offset', 'cp_country_risk_level', 'amount_usd'}

    @property
    def group_by_keys(self) -> List[str]:
        return ['customer_id', 'month_offset']

    def trace_query(self, params: dict) -> str:
        return "(cp_country_risk_level = 'High')"

    def pre_aggs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = OrderedDict()
        columns['hghrsk_cntry_val'] = f.when(
            (f.col('cp_country_risk_level')=='High')
            , f.col("amount_usd")).otherwise(0)
        return columns

    def get_agg_exprs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = OrderedDict()
        columns['sum_hghrsk_cntry'] = f.round(f.sum(f.col('hghrsk_cntry_val')),2)
        return columns

    def post_aggs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = OrderedDict()
        n_past_months_window = Window.partitionBy('customer_id').orderBy('month_offset').rangeBetween(-params['monthly_features_look_back_in_months'], -1)
        return enrich_with_z_score('sum_hghrsk_cntry', n_past_months_window, round_digits=2, output_column=self.identifier)
        return columns

    @property
    def output_fields(self) -> Set[Field]:
        return {Field(identifier="sum_hghrsk_cntry",
                      display_name='Value High Risk Country',
                      data_type=DataType.DOUBLE,
                      description="Unusual value of incoming/outgoing transactions involving High-Risk Juristictions in the current month",
                      category="Geography",
                      units="$",
                      business_type=BusinessType.CURRENCY,
                      dynamic_description =
                     """
                     {% set expl_data = explainability.sum_hghrsk_cntry.hrc_behavioral %}
                     {% set high_risk_countries = expl_data | selectattr('cr', 'in', ['High']) | list %}
                     {% set sum_high_risk = high_risk_countries | sum(attribute='s') | default(0, true) %}
                     {% set total_transaction_sum = activity.sum_trx %}
                     {% set percentage = ((sum_high_risk / total_transaction_sum * 100) | round(0)) if total_transaction_sum != 0 else 0 %}
                     {% set country_count = high_risk_countries | length %}
                     {% set sorted_high_risk_countries = high_risk_countries | sort(attribute='s', reverse=True) | default([], true) %}
                     {% set highest_amount_country = sorted_high_risk_countries | first | default({}, true) %}

                     Customer **{{ activity.customer_id }}** total amount transacted with High risk countries is **${{ activity.sum_hghrsk_cntry }}** in the current month.
                     This amount represents {{ percentage }}% of the total transaction amount for the analysis period.
                     In total, the customer transacted with {{ country_count }} unique High risk countries.

                     {% if highest_amount_country.ct is defined and highest_amount_country.s is defined %}
                     The highest amount was transacted with **{{ highest_amount_country.ct | country_full }} - ${{ highest_amount_country.s | prettify_number }}**.
                     {% else %}
                     No high-risk countries were transacted with this month.
                     {% endif %}
                     """,
                      explainabilities=[
                          Explainability(
                              identifier="hrc_behavioral",
                              type=ExplainabilityType.CATEGORICAL,
                              # time_range_value=12,
                              # time_range_unit=TimeRangeUnit.MONTH,
                              category_lbl="ct",
                              category_var="s",
                              json_column_reference="high_risk_country_explainability",
                              values=[
                                  ExplainabilityValueProperties(
                                      key="ct",
                                      name="Counterparty Country",
                                      type=ExplainabilityValueType.COUNTRY,
                                  ),
                                  ExplainabilityValueProperties(
                                      key="s",
                                      name="Sum of Transactions",
                                      type=ExplainabilityValueType.SUM,
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
                                  )
                              ]
                          )
                      ]
                     ),
               Field(identifier=self.identifier,
                     display_name='Value High Risk Country History',
                     data_type=DataType.DOUBLE,
                     description=self.description,
                     category="Geography",
                     units="$",
                     business_type=BusinessType.CURRENCY,
                     dynamic_description =
                     """
                     {% set hist_data = explainability.z_score_sum_hghrsk_cntry.hrc_behavioral %}
                     {% set total_12m = hist_data | sum(attribute='s') | default(0, true) %}
                     {% set md = metadata.z_score_sum_hghrsk_cntry %}
                     {% set expl_md = md.explainabilities.hrc_behavioral %}
                     {% set avg_monthly = (total_12m / expl_md.time_range_value) if expl_md.time_range_value != 0 else 0 %}

                     Customer **{{ activity.customer_id }}** total amount transacted with High risk countries is **${{ activity.sum_hghrsk_cntry | prettify_number }}** in the current month.

                     This number corresponds to a **Z-score of {{ activity.z_score_sum_hghrsk_cntry }}**, indicating a significant deviation from the customer's historical behavior.

                     Over the past 12 months, the customer performed a total amount of **${{ total_12m | round(2) | prettify_number }}** involving High risk countries — an average of **${{ avg_monthly | round(2) | prettify_number }} per month**.
                     """,
                      explainabilities=[
                          Explainability(
                              identifier="hrc_behavioral",
                              type=ExplainabilityType.BEHAVIORAL,
                              time_range_value=12,
                              time_range_unit=TimeRangeUnit.MONTH,
                              category_lbl="ct",
                              category_var="s",
                              json_column_reference="high_risk_country_explainability",
                              values=[
                                  ExplainabilityValueProperties(
                                      key="ct",
                                      name="Counterparty Country",
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
                                  )
                              ]
                          )
                      ]
                     )
               }
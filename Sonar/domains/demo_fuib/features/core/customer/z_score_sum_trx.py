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


class ZScoreSumTrx(AggFeature, FeatureDescriptor):

    @property
    def identifier(self) -> str:
        return 'z_score_sum_trx'

    @property
    def version(self) -> int:
        return 1

    @property
    def description(self) -> str:
        return 'Unusual value of incoming/outgoing transactions compared to the customer historical behavior in the last 12 months'

    @property
    def required_columns(self) -> Set[str]:
        return {'customer_id', 'month_offset', 'amount_usd'}

    @property
    def group_by_keys(self) -> List[str]:
        return ['customer_id', 'month_offset']

    def get_agg_exprs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = OrderedDict()
        columns['sum_trx'] = f.round(f.sum(f.col('amount_usd')),2)
        return columns

    def post_aggs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = OrderedDict()
        n_past_months_window = Window.partitionBy('customer_id').orderBy('month_offset').rangeBetween(-params['monthly_features_look_back_in_months'], -1)
        return enrich_with_z_score('sum_trx', n_past_months_window, round_digits=2, output_column=self.identifier)
        return columns

    @property
    def output_fields(self) -> Set[Field]:
        return {Field(identifier="sum_trx",
                      display_name='Total Value',
                      data_type=DataType.DOUBLE, 
                      description="Unusual value of incoming/outgoing transactions in the current period",
                      category="Transactional",
                      dynamic_description=
                      """
                      {% set md = metadata.sum_trx %}
                      {% set percentage_difference = ((activity.sum_trx - activity.pop_avg_sum_trx) / activity.pop_avg_sum_trx * 100) | round(0) %}

                      {% if percentage_difference > 5 %}
                      Customer **{{ activity.customer_id }}** conducted transactions totaling **{{ md.units | currency_symbol }}{{ activity.sum_trx | prettify_number }}** in the current month.
                      This amount is **{{ percentage_difference }}%** higher than the average monthly transaction value observed across the customer population, which stands at **{{ md.units | currency_symbol }}{{ activity.pop_avg_sum_trx| prettify_number }}**.
                      The comparison is based on a peer group of **{{ activity.pop_dstnct_cust_trx | prettify_number }} other customers** who also transacted during the same period.
                      {% else %}
                      Customer **{{ activity.customer_id }}** conducted transactions totaling **{{ md.units | currency_symbol }}{{ activity.sum_trx | prettify_number }}** in the current month.
                      {% endif %}
                      """,
                      units="$",
                      business_type = BusinessType.CURRENCY,
                      explainabilities=[
                          Explainability(
                            identifier="hist_expl",
                            type=ExplainabilityType.HISTORICAL,
                            time_range_value=12,
                            time_range_unit=TimeRangeUnit.MONTH,
                            values=[ExplainabilityValueProperties(
                                        key="zval",
                                        name="Total Value",
                                        dynamic_value="sum_trx",
                                        type=ExplainabilityValueType.TREND),
                                    ExplainabilityValueProperties(
                                        key='st',
                                        name="Pop Value",
                                        dynamic_value = "pop_avg_sum_trx",
                                        type = ExplainabilityValueType.POPULATION)])]),
               Field(identifier=self.identifier,
                     display_name='Unusual Value History',
                     data_type=DataType.DOUBLE, 
                     description=self.description,
                     category="Transactional"
                     # dynamic_description =
                     # """
                     # {% set total_12m = explainability.sum_trx.hist_expl | sum(attribute='zval') %}
                     # {% set md = metadata.z_score_sum_trx %}
                     # {% set expl_md = md.explainabilities.hist_expl %}
                     # {% set avg_monthly = total_12m / expl_md.time_range_value %}

                     # Customer **{{ activity.customer_id }}** conducted transactions totaling **{{ md.units | currency_symbol }}{{ activity.sum_trx | prettify_number }}** in the current month. 

                     # This amount corresponds to a **Z-score of {{ activity.z_score_sum_trx }}**, indicating a significant deviation from the customer's historical behavior. Over the past {{ expl_md.time_range_value }} {{ expl_md.time_range_unit | lower }}, the customer transacted a total of **{{ md.units | currency_symbol }}{{ total_12m | round(2) | prettify_number }}**, with an average of **{{ md.units | currency_symbol }}{{ avg_monthly | round(2) | prettify_number }} per {{ expl_md.time_range_unit | lower }}**.

                     # Such deviation may signal **potential financial anomalies or fraud**.
                     # """,
                     # business_type = BusinessType.CURRENCY,
                     # units="$",
                     # explainabilities=[
                     #    Explainability(
                     #        identifier="hist_expl",
                     #        type=ExplainabilityType.HISTORICAL,
                     #        time_range_value=12,
                     #        time_range_unit=TimeRangeUnit.MONTH,
                     #        values=[ExplainabilityValueProperties(
                     #                key="zval",
                     #                name="Total Amount",
                     #                dynamic_value="sum_trx",
                     #                type=ExplainabilityValueType.TREND)])]
                    )}
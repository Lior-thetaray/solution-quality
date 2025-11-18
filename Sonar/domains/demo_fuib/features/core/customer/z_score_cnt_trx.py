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



class ZScoreCntTrx(AggFeature, FeatureDescriptor):

    @property
    def identifier(self) -> str:
        return 'z_score_cnt_trx'

    @property
    def version(self) -> int:
        return 1

    @property
    def description(self) -> str:
        return ''

    @property
    def required_columns(self) -> Set[str]:
        return {'customer_id', 'month_offset'}

    @property
    def group_by_keys(self) -> List[str]:
        return ['customer_id', 'month_offset']

    def get_agg_exprs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = OrderedDict()
        columns['cnt_trx'] = f.count(f.col('customer_id'))
        return columns

    def post_aggs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = OrderedDict()
        n_past_months_window = Window.partitionBy('customer_id').orderBy('month_offset').rangeBetween(-params['monthly_features_look_back_in_months'], -1)
        return enrich_with_z_score('cnt_trx', n_past_months_window, round_digits=2, output_column=self.identifier)
        return columns

    @property
    def output_fields(self) -> Set[Field]:
        return {Field(identifier="cnt_trx",
                      display_name='Total Volume',
                      data_type=DataType.LONG, 
                      description="Unusual volume of incoming/outgoing transactions in the current period",
                      category="Transactional",
                      dynamic_description=
                      """
                      {% set md = metadata.cnt_trx %}
                      {% set percentage_difference = ((activity.cnt_trx - activity.pop_avg_cnt_trx) / activity.pop_avg_cnt_trx * 100) | round(0) %}

                      {% if percentage_difference > 5 %}
                      Customer **{{ activity.customer_id }}** conducted a total of **{{ activity.cnt_trx | prettify_number }} transactions** in the current month.
                      
                      This number is **{{ percentage_difference }}%** higher than the average monthly transaction volume observed across the customer population, which stands at **{{ activity.pop_avg_cnt_trx | prettify_number}}**.
                      The comparison is based on a peer group of **{{ activity.pop_dstnct_cust_trx | prettify_number }} other customers** who also transacted during the same period.
                      {% else %}
                      Customer **{{ activity.customer_id }}** conducted a total of **{{ activity.cnt_trx | prettify_number }} transactions** in the current month.
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
                                        name="Total Volume",
                                        dynamic_value="cnt_trx",
                                        type=ExplainabilityValueType.TREND),
                                    ExplainabilityValueProperties(
                                        key='st',
                                        name="Pop Volume",
                                        dynamic_value = "pop_avg_cnt_trx",
                                        type = ExplainabilityValueType.POPULATION)])]),
               Field(identifier=self.identifier,
                     display_name='Unusual Volume History',
                     data_type=DataType.DOUBLE, 
                     description=self.description,
                     category="Transactional",
                    # )}
                     dynamic_description =
                     """
                     {% set total_12m = explainability.cnt_trx.hist_expl | sum(attribute='zval') %}
                     {% set md = metadata.z_score_cnt_trx %}
                     {% set expl_md = md.explainabilities.hist_expl %}
                     {% set avg_monthly = total_12m / expl_md.time_range_value %}

                     Customer **{{ activity.customer_id }}** conducted a total of **{{ activity.cnt_trx | prettify_number }} transactions** in the current month. 

                     This number corresponds to a **Z-score of {{ activity.z_score_cnt_trx }}**, indicating a significant deviation from the customer's historical behavior. Over the past {{ expl_md.time_range_value }} {{ expl_md.time_range_unit | lower }}, the customer performed a total of **{{ md.units | currency_symbol }}{{ total_12m | round(2) | prettify_number }} transactions** - an average of **{{ md.units | currency_symbol }}{{ avg_monthly | round(2) | prettify_number }} per {{ expl_md.time_range_unit | lower }}**.

                     Such deviation may signal **potential financial anomalies or fraud**.
                     """,
                     business_type = BusinessType.CURRENCY,
                     units="$",
                     explainabilities=[
                        Explainability(
                            identifier="hist_expl",
                            type=ExplainabilityType.HISTORICAL,
                            time_range_value=12,
                            time_range_unit=TimeRangeUnit.MONTH,
                            values=[ExplainabilityValueProperties(
                                    key="zval",
                                    name="Total Volume",
                                    dynamic_value="cnt_trx",
                                    type=ExplainabilityValueType.TREND)])])}
               # Field(identifier='total_zelle_value_seg',
               #       display_name='Unusual Zelle Amount Activity Segment',
               #       data_type=DataType.DOUBLE, 
               #       description=self.description,
               #       category="Transactional")
               # }
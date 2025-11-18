from thetaray.api.solution import Field, DataType
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


class CntTrxNDay(AggFeature, FeatureDescriptor):

    @property
    def identifier(self) -> str:
        return 'cnt_trx_n_day'

    @property
    def version(self) -> int:
        return 1

    @property
    def description(self) -> str:
        return 'Unusual incoming/outgoing volume of transactions in a short period of time'

    @property
    def required_columns(self) -> Set[str]:
        return {'customer_id', 'month_offset', 'day_offset'}

    @property
    def group_by_keys(self) -> List[str]:
        return ['customer_id', 'month_offset']

    def pre_aggs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = OrderedDict()
        nday_window = Window().partitionBy("customer_id").orderBy("day_offset").rangeBetween(-2, 0)
        columns["n_day_trx"] = f.count(f.col('customer_id')).over(nday_window)
        return columns

    def get_agg_exprs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = OrderedDict()
        columns['cnt_trx_n_day'] = f.round(f.max(f.col('n_day_trx')),2)
        return columns

    # def post_aggs(self, params: dict) -> typing.OrderedDict[str, Column]:
    #     columns = OrderedDict()
    #     n_past_months_window = Window.partitionBy('customer_id').orderBy('month_offset').rangeBetween(-params['monthly_features_look_back_in_months'], -1)
    #     return enrich_with_z_score('cnt_trx_n_day', n_past_months_window, round_digits=2, output_column=self.identifier)
    #     return columns

    @property
    def output_fields(self) -> Set[Field]:
        return {Field(identifier='cnt_trx_n_day', 
                      display_name='Rapid Movement of Funds', 
                      data_type=DataType.LONG,
                      category="Transactional",
                      dynamic_description=
                      """
                      {% set md = metadata.cnt_trx_n_day %}
                      {% set percentage_difference = ((activity.cnt_trx_n_day - activity.pop_avg_cnt_trx_n_day) / activity.pop_avg_cnt_trx_n_day * 100) | round(0) %}
                      {% if percentage_difference > 5 %}
                      Customer **{{ activity.customer_id }}** conducted a total of **{{ activity.cnt_trx_n_day | prettify_number }} transactions** in a window of 3 days.

                      This number is **{{ percentage_difference }}%** higher than the average monthly transaction volume observed across the customer population, which stands at **{{ md.units | currency_symbol }}{{ activity.pop_avg_cnt_trx_n_day | prettify_number }}**.
                      
                      The comparison is based on a peer group of **{{ activity.pop_dstnct_cust_trx | prettify_number }} other customers** who also transacted during the same period.
                      {% else %}
                      Customer **{{ activity.customer_id }}** conducted a total of **{{ activity.cnt_trx_n_day | prettify_number }} transactions** in a window of 3 days.
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
                                        name="Rapid Amount",
                                        dynamic_value="cnt_trx_n_day",
                                        type=ExplainabilityValueType.TREND),
                                    ExplainabilityValueProperties(
                                        key='st',
                                        name="Pop Cash Amount",
                                        dynamic_value = "pop_avg_cnt_trx_n_day",
                                        type = ExplainabilityValueType.POPULATION)])])}
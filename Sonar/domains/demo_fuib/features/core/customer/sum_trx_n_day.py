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


class SumTrxNDay(AggFeature, FeatureDescriptor):

    @property
    def identifier(self) -> str:
        return 'sum_trx_n_day'

    @property
    def version(self) -> int:
        return 1

    @property
    def description(self) -> str:
        return 'Unusual incoming/outgoing volume of transactions in a short period of time'

    @property
    def required_columns(self) -> Set[str]:
        return {'customer_id', 'month_offset', 'day_offset','amount_usd'}

    @property
    def group_by_keys(self) -> List[str]:
        return ['customer_id', 'month_offset']

    def pre_aggs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = OrderedDict()
        nday_window = Window().partitionBy("customer_id").orderBy("day_offset").rangeBetween(-2, 0)
        columns["n_day_trx_value_in"] = f.sum(f.when(f.col('direction') == 'credit', f.col('amount_usd'))).over(nday_window)
        columns["n_day_trx_value_out"] = f.sum(f.when(f.col('direction') == 'debit', f.col('amount_usd'))).over(nday_window)
        columns['sum_trx_n_day_ratio'] = f.round(columns['n_day_trx_value_in'] / columns['n_day_trx_value_out'], 2)
        return columns

    def get_agg_exprs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = OrderedDict()
        # columns['sum_trx_n_day_in'] = f.round(f.max(f.col('n_day_trx_value_in')),2)
        # columns['sum_trx_n_day_out'] = f.round(f.max(f.col('n_day_trx_value_out')),2)
        # columns['sum_trx_n_day_ratio'] = f.round(columns['sum_in_trx_in'] / columns['sum_out_trx_out'], 2)
        columns['sum_trx_n_day'] = f.when((columns['sum_trx_n_day_ratio'] >= 0.9) & (columns['sum_trx_n_day_ratio'] <= 1.1), 
                                             f.greatest(columns['n_day_trx_value_in'], columns['n_day_trx_value_out'])).otherwise(0)
        return columns

    @property
    def output_fields(self) -> Set[Field]:
        return {Field(identifier='sum_trx_n_day', 
                      display_name='Rapid Movement of Funds', 
                      data_type=DataType.DOUBLE)}
       #                dynamic_description=
       #                """
       #                {% set md = metadata.total_rapid_movement_value %}
       #                {% set percentage_difference = ((activity.total_rapid_movement_value - activity.pop_avg_rapid_movement) / activity.pop_avg_rapid_movement * 100) | round(0) %}
       #                {% if percentage_difference > 5 %}
       #                Customer **{{ activity.cust }}** conducted transactions totaling **{{ md.units | currency_symbol }}{{ activity.total_rapid_movement_value | prettify_number }}** in a window of 5 days.
       #                This amount is **{{ percentage_difference }}%** higher than the average monthly transaction value observed across 
       # the customer population, which stands at **{{ md.units | currency_symbol }}{{ activity.pop_avg_rapid_movement | prettify_number }}**.               The comparison is based on a peer group of **{{ activity.pop_avg_total_value | prettify_number }} other customers** who also transacted during the same period.
       #                {% else %}
       #                Customer **{{ activity.cust }}** conducted transactions totaling **{{ md.units | currency_symbol }}{{ activity.total_rapid_movement_value | prettify_number }}** in a window of 5 days.
       #                {% endif %}
       #                """, 
       #               units="$",
       #               business_type = BusinessType.CURRENCY,
       #                explainabilities=[
       #                    Explainability(
       #                      identifier="hist_expl",
       #                      type=ExplainabilityType.HISTORICAL,
       #                      time_range_value=12,
       #                      time_range_unit=TimeRangeUnit.MONTH,
       #                      values=[ExplainabilityValueProperties(
       #                                  key="zval",
       #                                  name="Rapid Amount",
       #                                  dynamic_value="total_rapid_movement_value",
       #                                  type=ExplainabilityValueType.TREND),
       #                              ExplainabilityValueProperties(
       #                                  key='st',
       #                                  name="Pop Cash Amount",
       #                                  dynamic_value = "pop_avg_rapid_movement",
       #                                  type = ExplainabilityValueType.POPULATION)])])}
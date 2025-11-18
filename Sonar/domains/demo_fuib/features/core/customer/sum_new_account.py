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


class SumNewAccount(AggFeature, FeatureDescriptor):

    @property
    def identifier(self) -> str:
        return 'sum_new_account'

    @property
    def version(self) -> int:
        return 1

    @property
    def description(self) -> str:
        return 'Unusual value of incoming/outgoing Zelle transactions compared to the customer historical behavior in the last 12 months'

    @property
    def required_columns(self) -> Set[str]:
        return {'customer_id', 'month_offset', 'amount_usd', "is_new_account"}

    @property
    def group_by_keys(self) -> List[str]:
        return ['customer_id', 'month_offset']

    def pre_aggs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = OrderedDict()
        columns['new_account_val'] = f.when(f.col('is_new_account'), f.col("amount_usd")).otherwise(0)
        return columns

    def get_agg_exprs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = OrderedDict()
        columns['sum_new_account'] = f.round(f.sum(f.col('new_account_val')),2)
        return columns


    @property
    def output_fields(self) -> Set[Field]:
        return {Field(identifier='sum_new_account',
                      display_name='New Accounts Value',
                      data_type=DataType.DOUBLE, 
                      description='"Unusual value of incoming/outgoing transactions in the current period related to the customer new accounts"',
                      category="KYC",
                      dynamic_description=
                      """
                      {% set md = metadata.sum_new_account %}
                      {% set percentage_difference = ((activity.sum_new_account - activity.pop_avg_new_account) / activity.pop_avg_new_account * 100) | round(0) %}

                      {% if percentage_difference > 0 %}
                      Customer **{{ activity.customer_id }}**, who has new accounts, conducted transactions totaling **{{ md.units | currency_symbol }}{{ activity.sum_new_account | prettify_number }}** in the current month.
                      This amount is **{{ percentage_difference }}%** higher than the average monthly transaction value observed across the customer population, which stands at **{{ md.units | currency_symbol }}{{ activity.pop_avg_new_account | prettify_number }}**.
                      The comparison is based on a peer group of **{{ activity.pop_dstnct_cust_new_account| prettify_number }}** other customers with new accounts who also transacted during the same period.
                      {% else %}
                      Customer **{{ activity.customer_id }}**, who has new accounts, conducted transactions totaling **{{ md.units | currency_symbol }}{{ activity.sum_new_account | prettify_number }}** in the current month.
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
                                        name="New Account Amount Activity",
                                        dynamic_value="sum_new_account",
                                        type=ExplainabilityValueType.TREND),
                                    ExplainabilityValueProperties(
                                        key='st',
                                        name="Pop New Account Amount",
                                        dynamic_value = "pop_avg_new_account",
                                        type = ExplainabilityValueType.POPULATION)])])}
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


class CntNameMis(AggFeature, FeatureDescriptor):
    """
    required_params:
        "ratio_lower_bound" : lower bound for ratio of sum of in transactions to sum of out transactions
        "ratio_upper_bound" : upper bound for ratio of sum of in transactions to sum of out transactions
        "round_digits" : number of digits to round in feature result
    """
    @property
    def identifier(self) -> str:
        return 'cnt_trx_name_mis'

    @property
    def version(self) -> int:
        return 1

    @property
    def description(self) -> str:
        return 'High value turnover (i.e. pipe customer activity)'

    @property
    def required_columns(self) -> Set[str]:
        return {'customer_id', 'month_offset', 'direction', 'amount_usd'}

    @property
    def group_by_keys(self) -> List[str]:
        return ['customer_id', 'month_offset']

    def trace_query(self, params: dict) -> str:
        return "counterparty_name <> declared_counterparty_name"

    def pre_aggs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = OrderedDict()
        columns['name_mis_ind'] = f.when(
            (f.col('counterparty_name')!=f.col('declared_counterparty_name'))
            , f.lit(1)).otherwise(f.lit(0))
        return columns

    def get_agg_exprs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = OrderedDict()
        columns['cnt_trx_name_mis'] = f.sum(f.when(f.col('name_mis_ind') == 1, f.lit(1)))
        return columns

    @property
    def output_fields(self) -> Set[Field]:
        return {Field(identifier='cnt_trx_name_mis',
                      display_name='Name Mismatch Volume',
                      description='cnt_trx_name_mis',
                      category='KYC',
                      data_type=DataType.LONG,
                      dynamic_description=
                """
                Customer **{{ activity.customer_id }}** conducted **{{ activity.cnt_trx_name_mis | prettify_number }}** transactions with counterparties that have a mismatch between declared name and actual name.
                """,
                explainabilities=[
                    Explainability(
                        identifier="hist_expl",
                        type=ExplainabilityType.HISTORICAL,
                        time_range_value=12,
                        time_range_unit=TimeRangeUnit.MONTH,
                        values=[
                            ExplainabilityValueProperties(
                                key="zval",
                                name="Total Mis Count",
                                dynamic_value="cnt_trx_name_mis",
                                type=ExplainabilityValueType.TREND
                            )
                        ]
                    )
                ]
            )}
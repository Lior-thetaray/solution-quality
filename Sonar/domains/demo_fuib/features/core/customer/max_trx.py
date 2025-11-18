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


class MaxTrx(AggFeature, FeatureDescriptor):

    @property
    def identifier(self) -> str:
        return 'max_trx'

    @property
    def version(self) -> int:
        return 1

    @property
    def description(self) -> str:
        return 'A High value of a single transaction in the current period'

    @property
    def required_columns(self) -> Set[str]:
        return {'customer_id', 'month_offset', 'amount_usd'}

    @property
    def group_by_keys(self) -> List[str]:
        return ['customer_id', 'month_offset']

    def get_agg_exprs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = OrderedDict()
        columns['max_trx'] = f.max(f.col('amount_usd'))
        return columns

    # def post_aggs(self, params: dict) -> typing.OrderedDict[str, Column]:
    #     columns = OrderedDict()
    #     n_past_months_window = Window.partitionBy('customer_id').orderBy('month_offset').rangeBetween(-params['monthly_features_look_back_in_months'], -1)
    #     return enrich_with_z_score('sum_trx', n_past_months_window, round_digits=2, output_column=self.identifier)
    #     return columns

    @property
    def output_fields(self) -> Set[Field]:
        return {Field(identifier='max_trx',
                      display_name='Transaction Spike',
                      data_type=DataType.DOUBLE,
                      description= self.description,
                      category="Transactional",
                      dynamic_description=
                """
                Customer **{{ activity.customer_id }}** conducted a single transaction in the amount of **${{ activity.max_trx | prettify_number }}** in the current month.
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
                                name="Max Amount",
                                dynamic_value="max_trx",
                                type=ExplainabilityValueType.TREND
                            )
                        ]
                    )
                ]
            )}
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


class SumRatioPrev(AggFeature, FeatureDescriptor):

    @property
    def identifier(self) -> str:
        return 'sum_ratio_prev'

    @property
    def version(self) -> int:
        return 1

    @property
    def description(self) -> str:
        return 'Unusual difference in total transaction value in the current month as compared to the previous month'

    @property
    def required_columns(self) -> Set[str]:
        return {'customer_id', 'month_offset', 'trx_amount'}

    @property
    def required_params(self) -> Set[str]:
        return {'round_digits'}

    @property
    def group_by_keys(self) -> List[str]:
        return ['customer_id', 'month_offset']

    def get_agg_exprs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = OrderedDict()
        columns['sum_trx'] = f.sum("trx_amount")
        return columns

    def post_aggs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = OrderedDict()
        w = Window.partitionBy('customer_id').orderBy("month_offset")
        columns['sum_trx_prev'] = f.lag('sum_trx').over(w)
        columns[self.identifier] = f.round(f.col('sum_trx') / f.lag('sum_trx').over(w), params['round_digits'])
        return columns

    @property
    def output_fields(self) -> Set[Field]:
        return {Field(identifier='sum_ratio_prev', description=self.description, display_name='Unusual Value', data_type=DataType.DOUBLE, category='Transactional Activity'),
                           Field(
                data_type=DataType.DOUBLE,
                identifier="sum_trx_prev",
                category="Transactional Activity",
                display_name="Previous Month Value",
                is_explainability_column=True),
            Field(
                data_type=DataType.DOUBLE,
                identifier="sum_trx",
                category="Transactional Activity",
                display_name="Current Month Value",
                is_explainability_column=True)} 


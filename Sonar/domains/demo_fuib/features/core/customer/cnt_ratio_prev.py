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

class CountRatioPrev(AggFeature, FeatureDescriptor):

    @property
    def identifier(self) -> str:
        return 'cnt_ratio_prev'

    @property
    def version(self) -> int:
        return 1

    @property
    def description(self) -> str:
        return 'Unusual difference in total transaction volume in the current month as compared to the previous month'

    @property
    def required_columns(self) -> Set[str]:
        return {'customer_id', 'month_offset'}

    @property
    def required_params(self) -> Set[str]:
        return {'round_digits'}

    @property
    def group_by_keys(self) -> List[str]:
        return ['customer_id', 'month_offset']

    def get_agg_exprs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = OrderedDict()
        columns['cnt_trx'] = f.count(f.col('customer_id'))
        return columns

    def post_aggs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = OrderedDict()
        w = Window.partitionBy('customer_id').orderBy("month_offset")
        columns['cnt_trx_prev'] = f.lag('cnt_trx').over(w)
        columns[self.identifier] = f.round(f.col('cnt_trx') / f.lag('cnt_trx').over(w), params['round_digits'])

        
        return columns

    @property
    def output_fields(self) -> Set[Field]:
        return {Field(identifier='cnt_ratio_prev', description=self.description, display_name='Unusual Volume', data_type=DataType.DOUBLE, category='Transactional Activity'),
                            Field(
                data_type=DataType.LONG,
                identifier="cnt_trx_prev",
                category="Transactional Activity",
                display_name="Current Month Volume",
                is_explainability_column=True),
            Field(
                data_type=DataType.LONG,
                identifier="cnt_trx",
                category="Transactional Activity",
                display_name="Current Month Volume",
                is_explainability_column=True)}


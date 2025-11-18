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


class CustomerName(AggFeature, FeatureDescriptor):

    @property
    def identifier(self) -> str:
        return 'customer_name'

    @property
    def version(self) -> int:
        return 1

    @property
    def description(self) -> str:
        return 'A High value of a single transaction in the current period'

    @property
    def required_columns(self) -> Set[str]:
        return {'customer_id', 'month_offset', 'customer_name'}

    @property
    def group_by_keys(self) -> List[str]:
        return ['customer_id', 'month_offset']

    def get_agg_exprs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = OrderedDict()
        columns['customer_name'] = f.max(f.col('customer_name'))
        return columns

    @property
    def output_fields(self) -> Set[Field]:
        return {Field(identifier='customer_name',
                      display_name='Customer Name',
                      data_type=DataType.STRING,
                      description= self.description,
                      category="KYC")}
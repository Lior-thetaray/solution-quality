from typing import List, Set, Dict

from pyspark.sql import DataFrame, Window, functions as f, Column

from common.libs.feature_engineering import AggFeature, FeatureDescriptor
from common.libs.zscore import enrich_with_z_score

import typing
from collections import OrderedDict

from thetaray.api.solution import DataSet, Field, DataType, IngestionMode, BusinessType
from thetaray.api.solution.explainability import (
    Explainability,
    ExplainabilityType,
    ExplainabilityValueType,
    ExplainabilityValueProperties,
    TimeRangeUnit,
)

class CntTrx(AggFeature, FeatureDescriptor):

    @property
    def identifier(self) -> str:
        return 'cnt_trx'

    @property
    def version(self) -> int:
        return 1

    @property
    def description(self) -> str:
        return 'Unusual total number of transactions for the customer'

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

    @property
    def output_fields(self) -> Set[Field]:
        return {Field(identifier='cnt_trx', display_name='Total Volume', data_type=DataType.LONG, 
                      description=self.description)}

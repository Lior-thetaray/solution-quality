from typing import List, Set, Dict
from collections import OrderedDict

from pyspark.sql import DataFrame, Window, functions as f, Column

from common.libs.feature_engineering import AggFeature, FeatureDescriptor
from common.libs.zscore import enrich_with_z_score

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


class SumTrxCashIn(AggFeature, FeatureDescriptor):

    @property
    def identifier(self) -> str:
        return 'sum_trx_cash_in'

    @property
    def version(self) -> int:
        return 1

    @property
    def description(self) -> str:
        return 'Unusual value of incoming/outgoing cash activity compared to current period'

    @property
    def required_columns(self) -> Set[str]:
        return {'customer_id', 'month_offset', 'method', 'amount_usd'}

    @property
    def group_by_keys(self) -> List[str]:
        return ['customer_id', 'month_offset']

    def trace_query(self, params: dict) -> str:
        return "method = 'cash_deposit'"

    def get_agg_exprs(self, params: dict) -> OrderedDict[str, Column]:
        columns = OrderedDict()
        # count each cash transaction as 1
        columns['sum_trx_cash_in'] = f.sum(f.when( (f.col('method')=='cash_deposit'), f.col('amount_usd')))
        return columns

    @property
    def output_fields(self) -> Set[Field]:
        return {
            Field(
                identifier='sum_trx_cash_in',
                display_name='Total Cash Deposit Activity',
                data_type=DataType.DOUBLE,
                description=self.description,
                units="transactions",
                business_type = BusinessType.CURRENCY,
                category="Transactional",
                dynamic_description=
                      """
                      Customer **{{ activity.customer_id }}** conducted cash deposit transactions totaling **${{ activity.sum_trx_cash_in | round(2) }}** in the current month.
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
                                name="Total Mis Amount",
                                dynamic_value="sum_trx_cash_in",
                                type=ExplainabilityValueType.TREND
                            )
                        ]
                    )
                ]
            )
        }

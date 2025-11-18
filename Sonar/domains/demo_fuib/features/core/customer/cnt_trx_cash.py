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


class CntTrxCash(AggFeature, FeatureDescriptor):

    @property
    def identifier(self) -> str:
        return 'cnt_trx_cash'

    @property
    def version(self) -> int:
        return 1

    @property
    def description(self) -> str:
        return 'Unusual volume of incoming/outgoing cash activity compared to current period'

    @property
    def required_columns(self) -> Set[str]:
        return {'customer_id', 'month_offset', 'method'}

    @property
    def group_by_keys(self) -> List[str]:
        return ['customer_id', 'month_offset']

    def trace_query(self, params: dict) -> str:
        return "method = 'cash_deposit' OR method = 'cash_withdrawal'"

    def get_agg_exprs(self, params: dict) -> OrderedDict[str, Column]:
        columns = OrderedDict()
        # count each cash transaction as 1
        columns['cnt_trx_cash'] = f.sum(f.when( (f.col('method')=='cash_deposit') | (f.col('method')=='cash_withdrawal'), f.lit(1)))
        return columns

    @property
    def output_fields(self) -> Set[Field]:
        return {
            Field(
                identifier='cnt_trx_cash',
                display_name='Total Cash Count Activity',
                data_type=DataType.LONG,
                description=self.description,
                units="transactions",
                business_type = BusinessType.CURRENCY,
                category="Transactional",
                dynamic_description=
                """
                {% set md = metadata.cnt_trx_cash %}
                {% set percentage_difference = ((activity.cnt_trx_cash - activity.pop_avg_cnt_trx_cash) / activity.pop_avg_cnt_trx_cash * 100) | round(0) %}
                
                {% if percentage_difference > 5 %}
                Customer **{{ activity.customer_id }}** conducted **{{ activity.cnt_trx_cash | prettify_number }}** cash transactions in the current month.
                This count is **{{ percentage_difference }}%** higher than the average monthly cash volume observed across the customer population, which stands at **{{ activity.pop_avg_cnt_trx_cash | prettify_number }}**.
                The comparison is based on a peer group of **{{ activity.pop_dstnct_cust_trx_cash | prettify_number }}** other customers who also transacted via cash during the same period.
                {% else %}
                Customer **{{ activity.customer_id }}** conducted **{{ activity.cnt_trx_cash | prettify_number }}** cash transactions in the current month.
                {% endif %}
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
                                name="Total Cash Count",
                                dynamic_value="cnt_trx_cash",
                                type=ExplainabilityValueType.TREND
                            ),
                            ExplainabilityValueProperties(
                                key="st",
                                name="Pop Cash Count",
                                dynamic_value="pop_avg_cnt_trx_cash",
                                type=ExplainabilityValueType.POPULATION
                            )
                        ]
                    )
                ]
            )
        }

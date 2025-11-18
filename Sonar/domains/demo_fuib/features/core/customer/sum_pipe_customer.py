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


class SumPipeCustomer(AggFeature, FeatureDescriptor):
    """
    required_params:
        "ratio_lower_bound" : lower bound for ratio of sum of in transactions to sum of out transactions
        "ratio_upper_bound" : upper bound for ratio of sum of in transactions to sum of out transactions
        "round_digits" : number of digits to round in feature result
    """
    @property
    def identifier(self) -> str:
        return 'sum_pipe_customer'

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

    def get_agg_exprs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = OrderedDict()
        columns['sum_in_trx'] = f.sum(f.when(f.col('direction') == 'credit', f.col('amount_usd')))
        columns['sum_out_trx'] = f.sum(f.when(f.col('direction') == 'debit', f.col('amount_usd')))
        columns['sum_in_out_ratio'] = f.round(columns['sum_in_trx'] / columns['sum_out_trx'], 2)
        columns['sum_pipe_customer'] = f.when((columns['sum_in_out_ratio'] >= 0.9) & (columns['sum_in_out_ratio'] <= 1.1), 
                                             f.greatest(columns['sum_in_trx'], columns['sum_out_trx'])).otherwise(0)
        return columns

    @property
    def output_fields(self) -> Set[Field]:
        return {Field(identifier='sum_pipe_customer',
                      display_name='Pipe Customer',
                      description='High value turnover (i.e. pipe customer activity)',
                      category='Transactional Activity',
                      data_type=DataType.DOUBLE,
                      dynamic_description=
                      """
                      Customer **{{ activity.customer_id }}** received transactions totaling **${{ activity.sum_in_trx | round(2) }}** and sent transactions totaling **${{ activity.sum_out_trx | round(2) }}** in a short period of time.

                      This pattern might indicate pipe account behavior.

                      """,
                      units="$",
                      business_type = BusinessType.CURRENCY,
                      explainabilities=[
                          Explainability(
                            identifier="hist_expl",
                            type=ExplainabilityType.HISTORICAL,
                            time_range_value=10,
                            time_range_unit=TimeRangeUnit.MONTH,
                            values=[ExplainabilityValueProperties(
                                        key="zval",
                                        name="Pipe Customer",
                                        dynamic_value="sum_pipe_customer",
                                        type=ExplainabilityValueType.TREND)])]),
               Field(identifier='sum_in_trx',
                      display_name='Incoming Value',
                      description='High value turnover (i.e. pipe customer activity)',
                      category='Transactional Activity',
                      data_type=DataType.DOUBLE
                #       dynamic_description=
                # """
                # Customer **{{ activity.customer_id }}** received a total amount of **${{ activity.sum_in_trx | prettify_number }}** in the current month.
                # """,
                # explainabilities=[
                #     Explainability(
                #         identifier="hist_expl",
                #         type=ExplainabilityType.HISTORICAL,
                #         time_range_value=12,
                #         time_range_unit=TimeRangeUnit.MONTH,
                #         values=[
                #             ExplainabilityValueProperties(
                #                 key="zval",
                #                 name="Total In Amount",
                #                 dynamic_value="sum_in_trx",
                #                 type=ExplainabilityValueType.TREND
                #             )
                #         ]
                #     )
                # ]
            ),
               Field(identifier='sum_out_trx',
                      display_name='Outgoing Value',
                      description='High value turnover (i.e. pipe customer activity)',
                      category='Transactional Activity',
                      data_type=DataType.DOUBLE,
                      dynamic_description=
                """
                Customer **{{ activity.customer_id }}** conducted a total outgoing amount of **${{ activity.sum_out_trx | prettify_number }}** in the current month.
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
                                name="Total Out Amount",
                                dynamic_value="sum_out_trx",
                                type=ExplainabilityValueType.TREND
                            )
                        ]
                    )
                ]
            )
               }
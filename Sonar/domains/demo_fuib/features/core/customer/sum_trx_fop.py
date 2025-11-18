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


class SumFop(AggFeature, FeatureDescriptor):
    """
    required_params:
        "ratio_lower_bound" : lower bound for ratio of sum of in transactions to sum of out transactions
        "ratio_upper_bound" : upper bound for ratio of sum of in transactions to sum of out transactions
        "round_digits" : number of digits to round in feature result
    """
    @property
    def identifier(self) -> str:
        return 'sum_trx_fop'

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
        return "ip_hash = counterparty_ip AND customer_id <> cp_id"

    def pre_aggs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = OrderedDict()
        columns['fop_ind'] = f.when(
            ((f.col('ip_hash')==f.col('counterparty_ip')) & (f.col('customer_id')!=f.col('cp_id')))
            , f.lit(1)).otherwise(f.lit(0))
        return columns

    def get_agg_exprs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = OrderedDict()
        columns['sum_trx_fop'] = f.round(f.sum(f.when(f.col('fop_ind') == 1, f.col('amount_usd'))),2)
        columns['cnt_trx_fop'] = f.sum(f.when(f.col('fop_ind') == 1, f.lit(1)))
        columns['cnt_dstnct_fop'] = f.count_distinct(f.when(f.col('fop_ind') == 1, f.col('cp_id')))
        return columns

    @property
    def output_fields(self) -> Set[Field]:
        return {Field(identifier='sum_trx_fop',
                      display_name='FOP Value',
                      description='sum_trx_fop',
                      category='Transactional',
                      data_type=DataType.DOUBLE,
                      units="$",
                      business_type = BusinessType.CURRENCY,
                      dynamic_description=
                """
                Customer **{{ activity.customer_id }}** conducted a total amount of **${{ activity.sum_trx_fop | prettify_number }}** with counterparties that have the same IP address in the current month.
                """,
                explainabilities=[
                        Explainability(
                            identifier="categorical_expl",
                            type=ExplainabilityType.CATEGORICAL,
                            category_lbl="cn",
                            category_var="s",
                            json_column_reference="sum_trx_fop_explainability",
                            values=[
                                ExplainabilityValueProperties(
                                    key="cn",
                                    name="Counterparty Name",
                                ),
                                ExplainabilityValueProperties(
                                    key="s",
                                    name="Sum of Transactions",
                                    type=ExplainabilityValueType.SUM,
                                ),
                                ExplainabilityValueProperties(
                                    key="c",
                                    name="Transaction Count",
                                    type=ExplainabilityValueType.COUNT,
                                )
                            ]
                        )
                ]
            ),
               Field(identifier='cnt_trx_fop',
                      display_name='FOP Volume',
                      description='cnt_trx_fop',
                      category='Transactional',
                      units="$",
                      business_type = BusinessType.CURRENCY,
                      data_type=DataType.LONG,
                      dynamic_description=
                """
                Customer **{{ activity.customer_id }}** conducted **{{ activity.cnt_trx_fop | prettify_number }}** transactions with counterparties that have the same IP address in the current month.
                """,
                explainabilities=[
                        Explainability(
                            identifier="categorical_expl",
                            type=ExplainabilityType.CATEGORICAL,
                            category_lbl="cn",
                            category_var="c",
                            json_column_reference="sum_trx_fop_explainability",
                            values=[
                                ExplainabilityValueProperties(
                                    key="cn",
                                    name="Counterparty Name",
                                ),
                                ExplainabilityValueProperties(
                                    key="s",
                                    name="Sum of Transactions",
                                    type=ExplainabilityValueType.SUM,
                                ),
                                ExplainabilityValueProperties(
                                    key="c",
                                    name="Transaction Count",
                                    type=ExplainabilityValueType.COUNT,
                                )
                            ]
                        )
                ]
            ),
               Field(identifier='cnt_dstnct_fop',
                      display_name='Distinct FOP',
                      description='High value turnover (i.e. pipe customer activity)',
                      category='Transactional',
                      units="$",
                      business_type = BusinessType.CURRENCY,
                      data_type=DataType.LONG,
                #       dynamic_description=
                # """
                # Customer **{{ activity.customer_id }}** conducted transactions with **{{ activity.cnt_dstnct_fop | prettify_number }}** distinct counterparties that have same IP in the current month.
                # """,
                # explainabilities=[
                #         Explainability(
                #             identifier="categorical_expl",
                #             type=ExplainabilityType.CATEGORICAL,
                #             category_lbl="cn",
                #             category_var="c",
                #             json_column_reference="sum_trx_fop_explainability",
                #             values=[
                #                 ExplainabilityValueProperties(
                #                     key="cn",
                #                     name="Counterparty Name",
                #                 ),
                #                 ExplainabilityValueProperties(
                #                     key="s",
                #                     name="Sum of Transactions",
                #                     type=ExplainabilityValueType.SUM,
                #                 ),
                #                 ExplainabilityValueProperties(
                #                     key="c",
                #                     name="Transaction Count",
                #                     type=ExplainabilityValueType.COUNT,
                #                 )
                #             ]
                #         )
                # ]
            )}
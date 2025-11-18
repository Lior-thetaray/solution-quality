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


class ManyToOne(AggFeature, FeatureDescriptor):

    @property
    def identifier(self) -> str:
        return 'many_to_one'

    @property
    def version(self) -> int:
        return 1

    @property
    def description(self) -> str:
        return "Unusual number of distinct counterparties the customer is receiving funds from compared to his historical behavior in the last 12 months"

    @property
    def required_columns(self) -> Set[str]:
        return {'customer_id', 'month_offset', 'direction', 'cp_id'}

    def trace_query(self, params: dict) -> str:
        return "direction = 'credit'"

    @property
    def group_by_keys(self) -> List[str]:
        return ['customer_id', 'month_offset']

    def get_agg_exprs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = OrderedDict()
        columns['many_to_one'] = f.count_distinct(f.when(f.col('direction')=='credit', f.col('cp_id')))
        return columns

    # @property
    # def output_fields(self) -> Set[Field]:
    #     return {Field(identifier='many_to_one',
    #                   display_name='Many to One',
    #                   data_type=DataType.LONG, 
    #                   description="Unusual number of distinct counterparties the customer is receiving funds from in the current month",
    #                  category="Transactional"),
    #            Field(identifier=self.identifier,
    #                  display_name='Many to One Historical Activity',
    #                  data_type=DataType.DOUBLE,
    #                  description=self.description,
    #                  category="Transactional")}

    @property
    def output_fields(self) -> Set[Field]:
        return {Field(identifier='many_to_one',
                      display_name='Many to One',
                      data_type=DataType.LONG,
                      units="$",
                      business_type = BusinessType.CURRENCY,
                      description="Unusual number of distinct counterparties the customer is receiving funds from in the current month",
                      category="Transactional",
                      dynamic_description = """
                      Customer **{{ activity.customer_id }}** has received funds from **{{ activity.many_to_one }}** unique counterparties.
                      {% if activity.many_to_one > 5 %}
                      This pattern of **high fund distribution** may indicate potential layering or money laundering.
                      {% else %}
                      The number of counterparties is within an expected range.
                      {% endif %}
                      """,
                     explainabilities=[
                        Explainability(
                            identifier="categorical_expl",
                            type=ExplainabilityType.CATEGORICAL,
                            category_lbl="cn",
                            category_var="c",
                            json_column_reference="many_to_one_explainability",
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
                )}
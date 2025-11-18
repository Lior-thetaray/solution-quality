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


class OneToMany(AggFeature, FeatureDescriptor):

    @property
    def identifier(self) -> str:
        return 'one_to_many'

    @property
    def version(self) -> int:
        return 1

    @property
    def description(self) -> str:
        return 'Unusual number of distinct counterparties the customer is sending funds to compared to his historical behavior in the last 12 months'

    @property
    def required_columns(self) -> Set[str]:
        return {'customer_id', 'month_offset', 'direction', 'cp_id'}

    def trace_query(self, params: dict) -> str:
        return "direction = 'debit'"

    @property
    def group_by_keys(self) -> List[str]:
        return ['customer_id', 'month_offset']

    def get_agg_exprs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = OrderedDict()
        columns['one_to_many'] = f.count_distinct(f.when(f.col('direction')=='debit', f.col('cp_id')))
        return columns

    @property
    def output_fields(self) -> Set[Field]:
        return {Field(identifier='one_to_many',
                      display_name='One to Many',
                      data_type=DataType.LONG,
                      units="$",
                      business_type = BusinessType.CURRENCY,
                      description="Unusual number of distinct counterparties the customer is sending funds in the current month",
                      category="Transactional",
                      dynamic_description = """
                      Customer **{{ activity.customer_id }}** has sent funds to **{{ activity.one_to_many }}** unique counterparties.
                      {% if activity.one_to_many > 5 %}
                      This pattern of **high fund distribution** may indicate potential layering or money laundering.
                      {% else %}
                      The number of beneficiaries is within an expected range.
                      {% endif %}
                      """,
                     explainabilities=[
                        Explainability(
                            identifier="categorical_expl",
                            type=ExplainabilityType.CATEGORICAL,
                            category_lbl="cn",
                            category_var="c",
                            json_column_reference="one_to_many_explainability",
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

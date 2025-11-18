from typing import List
from thetaray.api.solution.evaluation import AlertConfiguration
from thetaray.api.solution import EvaluationFlow, AlgoEvaluationStep, TraceQuery
from thetaray.api.solution.evaluation import ModelReference, RelatedGraph, PropertyToFieldMapping
from thetaray.api.solution.summarization import AlertSummarizationType
from thetaray.common import Constants

from thetaray.api.solution import (EvaluationFlow, AlgoEvaluationStep, TraceQuery, ParquetIndex, CustomerInsights, InsightField, InsightFieldType, InsightPeriod, InsightType, InsightWidget)
from thetaray.api.solution.evaluation import (ModelReference, RelatedGraph, PropertyToFieldMapping, EvaluationFlowIdentifiers, EvaluationTimeWindowUnit)

from common.libs.config.loader import load_config
from common.libs.features_discovery import get_features, feature_ids_to_params
from common.libs.trace_query_collector import TraceQueryCollector
from typing import List

from thetaray.api.solution import DataSet, DataType, Field, IngestionMode, BusinessType


def customer_monthly_evaluation_flow():
    return EvaluationFlow(
        identifier="cust_month_ef",
        displayName="cust_month_ef",
        input_dataset="customer_monthly",
        data_permission="dpv:demo_fuib",
        alert_conf=AlertConfiguration(llm_summarization=True,
                                      summarization_types= [AlertSummarizationType(identifier = Constants.DEFAULT_ALERT_SUMMARIZATION_TYPE.identifier,
                                                                                                           name = Constants.DEFAULT_ALERT_SUMMARIZATION_TYPE.name,
                                                                                                           description = Constants.DEFAULT_ALERT_SUMMARIZATION_TYPE.description,
                                                                                                           llm_model = Constants.DEFAULT_ALERT_SUMMARIZATION_TYPE.llm_model,
                                                                                                           fallback_llm_model = Constants.DEFAULT_ALERT_SUMMARIZATION_TYPE.fallback_llm_model,
                                                                                                           prompt_template = """
{%- if risk.metadata.analysis_method == "AI" -%}
Anomalous behavior indicating money laundry activity has been identified for customer-{{ activity.customer_id }} by a machine learning
model with a probability of {{ algo.score }}.

The features with high rating, impacting the prediction are -
{{ algo.features[0].name }} with a rating of {{ algo.features[0].rating }}-{{ algo.features[0].description }}
{{ algo.features[1].name }} with a rating of {{ algo.features[1].rating }}-{{ algo.features[1].description }}
{{ algo.features[2].name }} with a rating of {{ algo.features[2].rating }}-{{ algo.features[2].description }}

All Feature values and descriptions -
{%- for feature in algo.features %}
{{ feature.identifier }}={{ feature.value }} | {{ feature.name }}
{%- endfor -%}
{%- endif %}
{%- if risk.metadata.analysis_method == "RULE" -%}
Anomalous behavior indicating money laundry activity has been identified for customer - {{ activity.customer_id }} by a rule based
model.
Rule Details:
    conditions_display: {{ risk.metadata.conditions_display }}
    description: {{ risk.metadata.description }}
    severity: {{ risk.metadata.severity }}
{%- endif %}

All enrichments values-
{%- if not risk.enrichments.values() -%}
No enrichments detected
{%- else -%}
{%- for enrichment in risk.enrichments.values() %}
    {{ enrichment.identifier }}-{{ enrichment.value }}
{%- endfor -%}
{%- endif %}

All variables values and descriptions-
{%- for variable in risk.variables.values() %}
    {{ variable.identifier }}-{{ variable.value }}-{{ variable.description }}
{%- endfor %}

Additional forensic information -
{%- for forensic in activity.forensic_fields.values() %}
    {{ forensic.identifier }}-{{ forensic.value }}-{{ forensic.description }}
{%- endfor %}

Please provide a summary in the following format
- a 2 row textual summary of the alert focusing on the customer details and reason for alerting
- the list of features with rating provided by the algorithm. The information should include feature name, description, value and rating. The information should be presented as bulleted rows
- additional information the is associated with suspicious activity within up to 5 rows. Don't repeat information that is included in the features with high rating
The output should be limited to 10 rows and be formatted using markdown
probability should be indicated in percentage

"""
                                                            
                                                                                                          )]),

        evaluation_steps=[
            AlgoEvaluationStep(
                identifier='algo',
                name='Algo',
                feature_extraction_model=ModelReference('customer_monthly_fe', tags = {"version": "release"}),
                detection_model=ModelReference('customer_monthly_ad', tags={"version": "release"}),
                pattern_length=3
            )
        ],
        global_trace_query=TraceQuery(identifier='global_trx_tq',
                                      dataset='trx_enriched',
                                      sql=base_query()),
        trace_queries=_trace_queries(),
        customer_insights=CustomerInsights(
            dataset="customer_insights_fuib",
            widgets=[
                InsightWidget(
                    identifier="kyc",
                    display_name="KYC Widget",
                    type=InsightType.KYC,
                    fields=[
                        InsightField(
                            field_ref="customer_risk",
                            display_name="Risk Class",
                            description="Customer Risk Class",
                            type=InsightFieldType.CLASSIFICATION,
                        ),
                        InsightField(
                            field_ref="customer_name",
                            display_name="Name",
                            description="Customer Name",
                            type=InsightFieldType.CUSTOMER_NAME
                        ),
                        InsightField(
                            field_ref="pep_indicator",
                            display_name="PEP",
                            description="Indicator if customer is PEP",
                            type=InsightFieldType.TAG
                        ),
                        InsightField(
                            field_ref="customer_type",
                            display_name="Customer Type"
                        ),
                        InsightField(
                            field_ref="incorporation_date",
                            display_name="Account Opening Date"
                        ),
                        InsightField(
                            field_ref="customer_country",
                            display_name="Country",
                            description="Customer country"
                        ),
                        InsightField(
                            field_ref="occupation",
                            display_name="Occupation",
                            description="Customer occupation"
                        ),
                        InsightField(
                            field_ref="customer_age",
                            display_name="Age",
                            description="Customer Age"
                        ),
                    ],
                ),
                InsightWidget(
                    identifier="ga",
                    display_name="Geographical Activity Widget",
                    type=InsightType.GEOGRAPHICAL_ACTIVITY,
                    fields=[
                        InsightField(
                            field_ref="hr_cc", type=InsightFieldType.HIGH_RISK_COUNTRIES
                        ),
                        InsightField(
                            field_ref="mr_cc",
                            type=InsightFieldType.MEDIUM_RISK_COUNTRIES,
                        ),
                        InsightField(
                            field_ref="lr_cc", type=InsightFieldType.LOW_RISK_COUNTRIES
                        )
                    ],
                ),
                InsightWidget(
                    identifier="tr",
                    display_name="Transactional Activity Widget",
                    type=InsightType.CUSTOMER_ACTIVITY,
                    fields=[
                        InsightField(
                            field_ref="tr_in", type=InsightFieldType.TRX_IN
                        ),
                        InsightField(
                            field_ref="tr_out",
                            type=InsightFieldType.TRX_OUT,
                        ),
                        InsightField(
                            field_ref="tr_in_count", 
                            type=InsightFieldType.TRX_IN_DETAIL
                        ),
                        InsightField(
                            field_ref="tr_out_count", type=InsightFieldType.TRX_OUT_DETAIL
                        )
                    ],
                period=InsightPeriod(
                    from_ref="trx_from_date",
                    to_ref="trx_to_date"
                )
                ),
                        ]),
        related_graph=RelatedGraph(
            identifier="fuib_graph",
            node_mappings={
                "AC": [PropertyToFieldMapping(field="customer_id", property="AN")]
            }
        )
    )


def _trace_queries() -> List[TraceQuery]:
    config = load_config('customer/monthly/wrangling.yaml', domain='demo_fuib')
    features = get_features(config)
    features_params = feature_ids_to_params(config, features)
    return TraceQueryCollector('trx_enriched', features, base_query(), features_params).trace_queries_fuib()


def base_query() -> str:
    return '''
    SELECT * FROM {dataset_table}
    WHERE customer_id = {activity.customer_id}
        AND txn_ts >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
        AND txn_ts < {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL
    '''


def entities():
    return [customer_monthly_evaluation_flow()]

from typing import List

from thetaray.api.solution import (AlgoEvaluationStep, EvaluationFlow, ParquetIndex, SuspiciousActivityReport, TraceQuery,
                                   CustomerInsights,
                                   InsightField,
                                   InsightFieldType,
                                   InsightPeriod,
                                   InsightType,
                                   InsightWidget,
                                   )
from thetaray.api.solution.evaluation import (
    EvaluationFlowIdentifiers,
    EvaluationTimeWindowUnit,
    ModelReference,
    PropertyToFieldMapping,
    RelatedGraph,
    AlertConfiguration
)

def evaluation_flow() -> EvaluationFlow:
    return EvaluationFlow(
        identifier="tr_analysis",
        displayName="tr_analysis",
        input_dataset="wrangling",
        data_permission="dpv:public",
        time_window_size=1,
        time_window_unit=EvaluationTimeWindowUnit.MONTH,
        identifiers=EvaluationFlowIdentifiers(
            grouping_identifier=["party_id"],
            primary_identifier=["account_id"],
            primary_entities_list="party_accounts",
        ),
        evaluation_steps=[
            AlgoEvaluationStep(
                identifier="tr_evaluation",
                name="Thetaray evaluation",
                features=[
                    "amount",
                    "duration",
                    "payments",
                    "birth_number",
                    "min1",
                    "max1",
                    "mean1",
                    "min2",
                    "max2",
                    "mean2",
                    "min3",
                    "max3",
                    "mean3",
                    "min4",
                    "max4",
                    "mean4",
                    "min5",
                    "max5",
                    "mean5",
                    "min6",
                    "max6",
                    "mean6",
                    "has_card",
                    "frequency",
                    "type_disp",
                    "type_card",
                    "high_risk_countries",
                    "keyword_matches",
                ],
                feature_extraction_model=ModelReference(
                    name="tr_feature_extraction_model",
                    tags={"version": "release"},
                ),
                detection_model=ModelReference(
                    name="tr_detection_model", tags={"version": "release"}
                ),
                pattern_length=3,
            ),
        ],
        max_workers=8,
        parquet_indexes=[
            ParquetIndex(
                identifier="pi_account_id",
                identifier_field="account_id",
                block_size=2 * 1024 * 1024,
                num_identifier_bins=10,
                identifiers_sample_size=1000,
            ),
        ],
        global_trace_query=TraceQuery(
            identifier="transactions_global_tq",
            identifier_column="trans_id",
            dataset="transaction",
            sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE account_id = {activity.account_id} AND tr_partition >= {activity.date_loan} -interval '1 month' - 
                ({occurred_before} || ' DAY')::INTERVAL AND tr_partition <= {activity.date_loan} + ({occurred_after} || 
                'DAY')::INTERVAL
            """,
        ),
        trace_queries=[
            TraceQuery(
                identifier="transactions_tq",
                identifier_column="trans_id",
                features=[
                    "amount",
                    "min1",
                    "max1",
                    "mean1",
                    "min2",
                    "max2",
                    "mean2",
                    "min3",
                    "max3",
                    "mean3",
                    "min4",
                    "max4",
                    "mean4",
                    "min5",
                    "max5",
                    "mean5",
                    "min6",
                    "max6",
                    "mean6",
                    "high_risk_countries",
                    "has_card",
                    "birth_number",
                    "keyword_matches",
                ],
                dataset="transaction",
                sql="""
                    SELECT * FROM {dataset_table}
                    WHERE account_id = {activity.account_id} 
                        AND tr_partition >= {activity.date_loan} - interval '1 month' - ({occurred_before} || ' DAY')::INTERVAL
                        AND tr_partition <= {activity.date_loan} + ({occurred_after} || ' DAY')::INTERVAL
                """,
            ),
            TraceQuery(
                identifier="loan_tq",
                identifier_column="loan_id",
                features=["payments", "amount", "duration"],
                dataset="loan",
                sql="""
                    SELECT * FROM {dataset_table}
                    WHERE account_id = {activity.account_id} 
                        AND tr_timestamp >= {activity.date_loan} - interval '1 month' - ({occurred_before} || ' DAY')::INTERVAL
                        AND tr_timestamp <= {activity.date_loan} + ({occurred_after} || ' DAY')::INTERVAL
                """,
            ),
        ],
        related_graph=RelatedGraph(
            identifier="public",
            node_mappings={
                "AC": [PropertyToFieldMapping(field="account_id", property="AN")]
            },
            grouping_node_mappings={
                "PR": [PropertyToFieldMapping(field="party_id", property="PI")]
            },
        ),
        customer_insights=CustomerInsights(
            dataset="customer_insights",
            widgets=[
                InsightWidget(
                    identifier="kyc",
                    display_name="KYC Widget",
                    type=InsightType.KYC,
                    fields=[
                        InsightField(
                            field_ref="kyc_classification",
                            type=InsightFieldType.CLASSIFICATION,
                        ),
                        InsightField(
                            field_ref="kyc_name", type=InsightFieldType.CUSTOMER_NAME
                        ),
                        InsightField(
                            field_ref="kyc_is_new", type=InsightFieldType.TAG
                        ),
                        InsightField(
                            field_ref="kyc_recently_updated",
                            type=InsightFieldType.TAG,
                        ),
                        InsightField(
                            field_ref="kyc_newly_incorporation",
                            type=InsightFieldType.TAG,
                        ),
                        InsightField(
                            field_ref="kyc_new_customer",
                            type=InsightFieldType.TAG,
                        ),
                        InsightField(
                            field_ref="kyc_occupation",
                        ),
                        InsightField(
                            field_ref="kyc_null_field",
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
                        ),
                        InsightField(
                            field_ref="director_ad", type=InsightFieldType.ADDRESS
                        ),
                        InsightField(
                            field_ref="company_ad", type=InsightFieldType.ADDRESS
                        ),
                    ],
                ),
                InsightWidget(
                    identifier="tr",
                    display_name="Transactional Activity Widget",
                    type=InsightType.CUSTOMER_ACTIVITY,
                    fields=[
                        InsightField(field_ref="tr_in", type=InsightFieldType.TRX_IN),
                        InsightField(field_ref="tr_out", type=InsightFieldType.TRX_OUT),
                        InsightField(
                            field_ref="tr_in_count", type=InsightFieldType.TRX_IN_DETAIL
                        ),
                        InsightField(
                            field_ref="tr_out_count",
                            type=InsightFieldType.TRX_OUT_DETAIL,
                        ),
                        InsightField(
                            field_ref="tr_in_seg",
                            type=InsightFieldType.TRX_POPULATION_IN,
                        ),
                        InsightField(
                            field_ref="tr_out_seg",
                            type=InsightFieldType.TRX_POPULATION_OUT,
                        ),
                        InsightField(
                            field_ref="tr_in_seg_count",
                            type=InsightFieldType.TRX_POPULATION_IN_DETAIL,
                        ),
                        InsightField(
                            field_ref="tr_out_seg_count",
                            type=InsightFieldType.TRX_POPULATION_OUT_DETAIL,
                        ),
                    ],
                    period=InsightPeriod(
                        from_ref="trx_from_date",
                        to_ref="trx_to_date"
                    )
                ),
                InsightWidget(
                    identifier="alerts",
                    display_name="Historical Alerts Widget",
                    type=InsightType.HISTORICAL_ALERTS,
                    fields=[
                        InsightField(field_ref="tm", type=InsightFieldType.CATEGORY),
                        InsightField(field_ref="scrn", type=InsightFieldType.CATEGORY),
                    ],
                    period=InsightPeriod(
                        from_ref="trx_from_date",
                        to_ref="trx_to_date"
                    )
                ),
            ],
        ),
        alert_conf=AlertConfiguration(llm_summarization=True),
        suspicious_activity_reports=[SuspiciousActivityReport(
            type="FINCEN",
            file_name="fincen.txt"
        )]
    )


def entities() -> List[EvaluationFlow]:
    return [evaluation_flow()]

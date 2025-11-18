from typing import List

from thetaray.api.solution import AlgoEvaluationStep, EvaluationFlow, TraceQuery
from thetaray.api.solution.evaluation import (
    EvaluationFlowIdentifiers,
    ModelReference,
    PropertyToFieldMapping,
    RelatedGraph,
)


def evaluation_flow() -> EvaluationFlow:
    return EvaluationFlow(
        identifier="party_tr_analysis",
        displayName="party_tr_analysis",
        input_dataset="party_wrangling",
        data_permission="dpv:public",
        identifiers=EvaluationFlowIdentifiers(
            grouping_identifier=["party_id"],
            primary_entities_list="party_accounts",
        ),
        evaluation_steps=[
            AlgoEvaluationStep(
                identifier="tr_evaluation",
                name="Thetaray evaluation",
                feature_extraction_model=ModelReference(
                    name="tr_feature_extraction_model",
                    tags={"version": "release"},
                ),
                detection_model=ModelReference(name="tr_detection_model", tags={"version": "release"}),
                pattern_length=3,
            ),
        ],
        max_workers=8,
        global_trace_query=TraceQuery(
            identifier="transactions_global_tq",
            identifier_column="trans_id",
            dataset="transaction",
            is_grouping_query=True,
            sql="""
                SELECT ds.* FROM {dataset_table} ds
                JOIN {primary_identifiers} AS pr_ids
                    ON ds.account_id = pr_ids.account_id
                WHERE ds.tr_partition >= {activity.date_loan} -interval '1 month' - ({occurred_before} || ' DAY')::INTERVAL
                AND ds.tr_partition <= {activity.date_loan} + ({occurred_after} || 'DAY')::INTERVAL
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
                ],
                dataset="transaction",
                is_grouping_query=True,
                sql="""
                    SELECT ds.* FROM {dataset_table} ds
                    JOIN {primary_identifiers} AS pr_ids
                        ON ds.account_id = pr_ids.account_id
                    WHERE ds.tr_timestamp >= {activity.date_loan} - interval '1 month' - ({occurred_before} || ' DAY')::INTERVAL 
                    AND ds.tr_timestamp <= {activity.date_loan} + ({occurred_after} || ' DAY')::INTERVAL
                """,
            ),
            TraceQuery(
                identifier="loan_tq",
                identifier_column="loan_id",
                features=["payments", "amount", "duration"],
                dataset="loan",
                is_grouping_query=True,
                sql="""
                    SELECT ds.* FROM {dataset_table} ds
                    JOIN {primary_identifiers} AS pr_ids
                        ON ds.account_id = pr_ids.account_id
                    AND ds.tr_timestamp >= {activity.date_loan} - interval '1 month' - ({occurred_before} || ' DAY')::INTERVAL 
                    AND ds.tr_timestamp <= {activity.date_loan} + ({occurred_after} || ' DAY')::INTERVAL
                """,
            ),
        ],
        related_graph=RelatedGraph(
            identifier="public",
            node_mappings={"PR": [PropertyToFieldMapping(field="party_id", property="PI")]},
        ),
    )


def entities() -> List[EvaluationFlow]:
    return [evaluation_flow()]

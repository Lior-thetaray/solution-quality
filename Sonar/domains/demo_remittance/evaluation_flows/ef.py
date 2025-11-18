from typing import List
from thetaray.api.solution import EvaluationFlow, AlgoEvaluationStep, TraceQuery
from thetaray.api.solution.evaluation import ModelReference, RelatedGraph, PropertyToFieldMapping, EvaluationTimeWindowUnit, EFRuleBuilderConfig
from domains.demo_remittance.utils.ai_summarization import config as ai_summary_config
from domains.demo_remittance.utils.customer_insights import config as insights_config


def evaluation_flow():
    return EvaluationFlow(
        identifier="demo_remittance_ef",
        displayName="Customer Monthly Evaluation",
        input_dataset="demo_remittance_customer_monthly",
        data_permission="dpv:demo_remittance",
        time_window_size=1,
        time_window_unit=EvaluationTimeWindowUnit.MONTH,
        rule_builder_config=EFRuleBuilderConfig(
                simulation_spark_config={"spark.executor.memory": "4g"},
                chunk_size=3,
                fetch_size=500),
        
        evaluation_steps=[
            AlgoEvaluationStep(
                identifier='algo',
                name='Algo',
                feature_extraction_model=ModelReference('demo_remmittance_fe', tags = {"version": "release"}),
                detection_model=ModelReference('demo_remmittance_ad', tags={"version": "release"}),
                pattern_length=2
            )
        ],
        alert_conf=ai_summary_config(),
        global_trace_query=TraceQuery(
            identifier="global_tq",
            identifier_column="transaction_id",
            dataset="demo_remittance_transactions",
            sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
            """,
        ),
        trace_queries=[
            TraceQuery(
                identifier="feat_tq_1",
                identifier_column="transaction_id",
                features=[
                    "multpl_tx_bl_lim",
                ],
                dataset="demo_remittance_transactions",
                sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND ((amount >= 10000.0 - 500.0) AND (amount < 10000.0))
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """,
            ),
            TraceQuery(
                identifier="feat_tq_2",
                identifier_column="transaction_id",
                features=[
                    "vel_spike",
                ],
                dataset="demo_remittance_transactions",
                sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """,
            ),
            TraceQuery(
                identifier="feat_tq_3",
                identifier_column="transaction_id",
                features=[
                    "multi_party_actv",
                ],
                dataset="demo_remittance_transactions",
                sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """,
            ),
            TraceQuery(
                identifier="feat_tq_4",
                identifier_column="transaction_id",
                features=[
                    "hr_jurid_vol",
                ],
                dataset="demo_remittance_transactions",
                sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND destination_country_code IN ('IR', 'KP', 'SY', 'SD', 'VE', 'SO', 'YE', 'CU', 'MM', 'CF')
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """,
            ),
    
            TraceQuery(
                identifier="feat_tq_4",
                identifier_column="transaction_id",
                features=[
                    "total_tx_amount",
                    "avg_tx_amount"
                ],
                dataset="demo_remittance_transactions",
                sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """,
            ),
        ],
        related_graph=RelatedGraph(
            identifier="demo_remittance_graph",
            node_mappings={
                "AC": [PropertyToFieldMapping(field="customer_id", property="AN")]
            }
        ),
        customer_insights=insights_config()
    )


def entities():
    return [evaluation_flow()]

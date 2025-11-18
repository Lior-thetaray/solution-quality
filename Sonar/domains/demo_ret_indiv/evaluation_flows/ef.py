from typing import List
from thetaray.api.solution import EvaluationFlow, AlgoEvaluationStep, TraceQuery
from thetaray.api.solution.evaluation import ModelReference, RelatedGraph, PropertyToFieldMapping, EvaluationTimeWindowUnit, EFRuleBuilderConfig
from domains.demo_ret_indiv.utils.ai_summarization import config as ai_summary_config
from domains.demo_ret_indiv.utils.customer_insights import config as insights_config


def evaluation_flow():
    return EvaluationFlow(
        identifier="demo_ret_indiv_ef",
        displayName="Customer Monthly Evaluation",
        input_dataset="demo_ret_indiv_customer_monthly",
        data_permission="dpv:demo_ret_indiv",
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
                feature_extraction_model=ModelReference('demo_ret_indiv_fe', tags = {"version": "release"}),
                detection_model=ModelReference('demo_ret_indiv_ad', tags={"version": "release"}),
                pattern_length=2
            )
        ],
        alert_conf=ai_summary_config(),
        global_trace_query=TraceQuery(
            identifier="global_tq",
            identifier_column="transaction_id",
            dataset="demo_ret_indiv_transactions",
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
                    "structuring",
                ],
                dataset="demo_ret_indiv_transactions",
                sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND transaction_type_description = 'Structuring'
                AND reference_trx_amount < 10000
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """,
            ),
            TraceQuery(
                identifier="feat_tq_2",
                identifier_column="transaction_id",
                features=[
                    "cnt_distinct_atm",
                ],
                dataset="demo_ret_indiv_transactions",
                sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND transaction_type_code = 'ATM'
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """,
            ),
            TraceQuery(
                identifier="feat_tq_3",
                identifier_column="transaction_id",
                features=[
                    "sum_trx_high_risk",
                ],
                dataset="demo_ret_indiv_transactions",
                sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND transaction_type_code = 'TRF'
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """,
            ),
            TraceQuery(
                identifier="feat_tq_4",
                identifier_column="transaction_id",
                features=[
                    "round_amounts",
                ],
                dataset="demo_ret_indiv_transactions",
                sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND transaction_type_code = 'ROUND_AMOUNT'
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """,
            ),
            TraceQuery(
                identifier="feat_tq_4",
                identifier_column="transaction_id",
                features=[
                    "deposit_withdrawal_pipe",
                    "overall_activity_spike",
                    "crypto_activity",
                    "check_deposit_value",

                ],
                dataset="demo_ret_indiv_transactions",
                sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """,
            ),
        ],
        related_graph=RelatedGraph(
            identifier="demo_ret_indiv_graph",
            node_mappings={
                "AC": [PropertyToFieldMapping(field="customer_id", property="AN")]
            }
        ),
        customer_insights=insights_config()
    )


def entities():
    return [evaluation_flow()]

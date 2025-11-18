from typing import List
from thetaray.api.solution import EvaluationFlow, AlgoEvaluationStep, TraceQuery
from thetaray.api.solution.evaluation import ModelReference, RelatedGraph, PropertyToFieldMapping, EvaluationTimeWindowUnit, EFRuleBuilderConfig
from domains.demo_ret_smb.utils.ai_summarization import config as ai_summary_config
from domains.demo_ret_smb.utils.customer_insights import config as insights_config


def evaluation_flow():
    return EvaluationFlow(
        identifier="demo_ret_smb_ef",
        displayName="Customer Monthly Evaluation",
        input_dataset="demo_ret_smb_customer_monthly",
        data_permission="dpv:demo_ret_smb",
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
                feature_extraction_model=ModelReference('demo_ret_smb_fe', tags={"version": "release"}),
                detection_model=ModelReference('demo_ret_smb_ad', tags={"version": "release"}),
                pattern_length=2
            )
        ],
        alert_conf=ai_summary_config(),
        global_trace_query=TraceQuery(
            identifier="global_tq",
            identifier_column="transaction_id",
            dataset="demo_ret_smb_transactions",
            sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
            """,
        ),
        trace_queries=[
            TraceQuery(
                identifier="pipe_accnt_behv_tq",
                identifier_column="transaction_id",
                features=["pipe_accnt_behv"],
                dataset="demo_ret_smb_transactions",
                sql="""
                SELECT * FROM {dataset_table}
                WHERE customer_id = {activity.customer_id}
                AND transaction_type_code = 'PIPE'
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """
            ),
            TraceQuery(
                identifier="tax_heaven_jurisd_tq",
                identifier_column="transaction_id",
                features=["tax_heaven_jurisd"],
                dataset="demo_ret_smb_transactions",
                sql="""
                SELECT * FROM {dataset_table}
                WHERE customer_id = {activity.customer_id}
                AND transaction_type_code = 'TAX_HEAVEN'
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """
            ),
            TraceQuery(
                identifier="spike_of_trx_tq",
                identifier_column="transaction_id",
                features=["spike_of_trx"],
                dataset="demo_ret_smb_transactions",
                sql="""
                SELECT * FROM {dataset_table}
                WHERE customer_id = {activity.customer_id}
                AND transaction_type_code = 'SPIKE'
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """
            ),
            TraceQuery(
                identifier="many_to_one_tq",
                identifier_column="transaction_id",
                features=["many_to_one"],
                dataset="demo_ret_smb_transactions",
                sql="""
                SELECT * FROM {dataset_table}
                WHERE customer_id = {activity.customer_id}
                AND in_out = 'IN'
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """
            ),
            TraceQuery(
                identifier="one_to_many_tq",
                identifier_column="transaction_id",
                features=["one_to_many"],
                dataset="demo_ret_smb_transactions",
                sql="""
                SELECT * FROM {dataset_table}
                WHERE customer_id = {activity.customer_id}
                AND in_out = 'OUT'
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """
            ),
            
            TraceQuery(
                identifier="features_tq",
                identifier_column="transaction_id",
                features=["avg_tx_amount_monthly","pct_domestic_transactions","atm_withdrawal_ratio"],
                dataset="demo_ret_smb_transactions",
                sql="""
                SELECT * FROM {dataset_table}
                WHERE customer_id = {activity.customer_id}
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """
            ),
        ],
        related_graph=RelatedGraph(
            identifier="demo_ret_smb_graph",
            node_mappings={
                "AC": [PropertyToFieldMapping(field="customer_id", property="AN")]
            }
        ),
        customer_insights=insights_config()
    )


def entities():
    return [evaluation_flow()]

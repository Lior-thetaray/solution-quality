from typing import List
from thetaray.api.solution import EvaluationFlow, AlgoEvaluationStep, TraceQuery
from thetaray.api.solution.evaluation import (
    ModelReference,
    RelatedGraph,
    PropertyToFieldMapping,
    EvaluationTimeWindowUnit,
    EFRuleBuilderConfig,
)
from domains.demo_pay_proc.utils.ai_summarization import config as ai_summary_config
from domains.demo_pay_proc.utils.customer_insights import config as insights_config


def evaluation_flow():
    return EvaluationFlow(
        identifier="demo_pay_proc_ef",
        displayName="Customer Monthly Evaluation",
        input_dataset="demo_pay_proc_customer_monthly",
        data_permission="dpv:demo_pay_proc",
        time_window_size=1,
        time_window_unit=EvaluationTimeWindowUnit.MONTH,
        rule_builder_config=EFRuleBuilderConfig(
            simulation_spark_config={"spark.executor.memory": "4g"},
            chunk_size=3,
            fetch_size=500
        ),
        evaluation_steps=[
            AlgoEvaluationStep(
                identifier='algo',
                name='Algo',
                feature_extraction_model=ModelReference('demo_pay_proc_fe', tags={"version": "release"}),
                detection_model=ModelReference('demo_pay_proc_ad', tags={"version": "release"}),
                pattern_length=2
            )
        ],
        alert_conf=ai_summary_config(),
        global_trace_query=TraceQuery(
            identifier="global_tq",
            identifier_column="transaction_id",
            dataset="demo_pay_proc_transactions",
            sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
            """,
        ),
        trace_queries=[
            # 1. Transaction Count Ratio
            TraceQuery(
                identifier="txn_count_tq",
                identifier_column="transaction_id",
                features=["txn_count_ratio"],
                dataset="demo_pay_proc_transactions",
                sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """
            ),
            # 2. Reversal Ratio
            TraceQuery(
                identifier="reversal_tq",
                identifier_column="transaction_id",
                features=["reversal_ratio"],
                dataset="demo_pay_proc_transactions",
                sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND is_reversal = TRUE
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """
            ),
            # 3. Rare Currency Percentage
            TraceQuery(
                identifier="rare_currency_tq",
                identifier_column="transaction_id",
                features=["rare_currency_pct"],
                dataset="demo_pay_proc_transactions",
                sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND is_rare_currency = TRUE
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """
            ),
            # 4. New Terminal Ratio
            TraceQuery(
                identifier="terminal_ratio_tq",
                identifier_column="transaction_id",
                features=["new_terminal_ratio"],
                dataset="demo_pay_proc_transactions",
                sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """
            ),
            # 5. Average Transaction Amount Ratio
            TraceQuery(
                identifier="avg_txn_amt_tq",
                identifier_column="transaction_id",
                features=["avg_txn_amt_ratio"],
                dataset="demo_pay_proc_transactions",
                sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """
            ),
            # 6. Foreign vs Domestic Ratio Change
            TraceQuery(
                identifier="foreign_domestic_tq",
                identifier_column="transaction_id",
                features=["domestic_ratio_change"],
                dataset="demo_pay_proc_transactions",
                sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """
            ),
            # 7. Pipe Account Behavior Score
            TraceQuery(
                identifier="pipe_behavior_tq",
                identifier_column="transaction_id",
                features=["pipe_account_behaviour_score"],
                dataset="demo_pay_proc_transactions",
                sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """
            ),
        ],
        related_graph=RelatedGraph(
            identifier="demo_pay_proc_graph",
            node_mappings={
                "AC": [PropertyToFieldMapping(field="customer_id", property="AN")]
            }
        ),
        customer_insights=insights_config()
    )


def entities():
    return [evaluation_flow()]

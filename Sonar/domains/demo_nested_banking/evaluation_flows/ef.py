from typing import List
from thetaray.api.solution import EvaluationFlow, AlgoEvaluationStep, TraceQuery
from thetaray.api.solution.evaluation import (
    ModelReference,
    RelatedGraph,
    PropertyToFieldMapping,
    EvaluationTimeWindowUnit,
    EFRuleBuilderConfig,
)
from domains.demo_nested_banking.utils.ai_summarization import config as ai_summary_config
from domains.demo_nested_banking.utils.customer_insights import config as insights_config


def evaluation_flow():
    return EvaluationFlow(
        identifier="demo_nested_banking_ef",
        displayName="Customer Monthly Evaluation (Nested Banking)",
        input_dataset="demo_nested_banking_customer_monthly",
        data_permission="dpv:demo_nested_banking",
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
                feature_extraction_model=ModelReference('demo_nested_banking_fe', tags={"version": "release"}),
                detection_model=ModelReference('demo_nested_banking_ad', tags={"version": "release"}),
                pattern_length=2
            )
        ],
        alert_conf=ai_summary_config(),
        global_trace_query=TraceQuery(
            identifier="global_tq",
            identifier_column="transaction_id",
            dataset="demo_nested_banking_transactions",
            sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition <  {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL
            """,
        ),
        trace_queries=[
            # 1) Spike de actividad: txn_count
            TraceQuery(
                identifier="txn_count_tq",
                identifier_column="transaction_id",
                features=["txn_count"],
                dataset="demo_nested_banking_transactions",
                sql="""
                    SELECT ds.* FROM {dataset_table} ds
                    WHERE customer_id = {activity.customer_id}
                    AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                    AND tr_partition <  {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL
                """
            ),
            # 2) Moneda no vista (evidencia aproximada): is_new_currency
            TraceQuery(
                identifier="new_currency_tq",
                identifier_column="transaction_id",
                features=["new_currency_count"],
                dataset="demo_nested_banking_transactions",
                sql="""
                    SELECT ds.* FROM {dataset_table} ds
                    WHERE customer_id = {activity.customer_id}
                    AND is_new_currency = TRUE
                    AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                    AND tr_partition <  {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL
                """
            ),
            # 3) Nuevo BIC (intermediario) único: primeras apariciones
            TraceQuery(
                identifier="new_intr_bic_unique_tq",
                identifier_column="transaction_id",
                features=["new_intr_bic_unique_count"],
                dataset="demo_nested_banking_transactions",
                sql="""
                    SELECT ds.* FROM {dataset_table} ds
                    WHERE customer_id = {activity.customer_id}
                    AND first_new_intr_bic8 IS NOT NULL
                    AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                    AND tr_partition <  {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL
                """
            ),
            # 4) Jurisdicciones de alto riesgo
            TraceQuery(
                identifier="high_risk_tq",
                identifier_column="transaction_id",
                features=["high_risk_count"],
                dataset="demo_nested_banking_transactions",
                sql="""
                    SELECT ds.* FROM {dataset_table} ds
                    WHERE customer_id = {activity.customer_id}
                    AND touches_high_risk_jurisdiction = TRUE
                    AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                    AND tr_partition <  {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL
                """
            ),
            # 5) Ratio de montos redondos (corporates)
            TraceQuery(
                identifier="round_amount_ratio_tq",
                identifier_column="transaction_id",
                features=["round_amount_ratio"],
                dataset="demo_nested_banking_transactions",
                sql="""
                    SELECT ds.* FROM {dataset_table} ds
                    WHERE customer_id = {activity.customer_id}
                    AND originator_is_corporate = TRUE
                    AND is_round_amount = TRUE
                    AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                    AND tr_partition <  {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL
                """
            ),
            # 6) Pipe (no trigger): alternancia IN/OUT
            TraceQuery(
                identifier="pipe_behavior_tq",
                identifier_column="transaction_id",
                features=["pipe_account_behaviour_score"],
                dataset="demo_nested_banking_transactions",
                sql="""
                    SELECT ds.* FROM {dataset_table} ds
                    WHERE customer_id = {activity.customer_id}
                    AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                    AND tr_partition <  {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL
                """
            ),
            # 7) Many-to-one (no trigger)
            TraceQuery(
                identifier="many_to_one_tq",
                identifier_column="transaction_id",
                features=["many_to_one_count"],
                dataset="demo_nested_banking_transactions",
                sql="""
                    SELECT ds.* FROM {dataset_table} ds
                    WHERE customer_id = {activity.customer_id}
                    AND direction = 'IN'
                    AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                    AND tr_partition <  {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL
                """
            ),
        ],
        related_graph=RelatedGraph(
            identifier="demo_nested_banking_graph",
            node_mappings={
                "AC": [PropertyToFieldMapping(field="customer_id", property="AN")]
            }
        ),
        customer_insights=insights_config()
    )


def entities():
    return [evaluation_flow()]

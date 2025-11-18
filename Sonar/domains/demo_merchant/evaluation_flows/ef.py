from typing import List
from thetaray.api.solution import EvaluationFlow, AlgoEvaluationStep, TraceQuery
from thetaray.api.solution.evaluation import (
    ModelReference, RelatedGraph, PropertyToFieldMapping,
    EvaluationTimeWindowUnit, EFRuleBuilderConfig
)
from domains.demo_merchant.utils.ai_summarization import config as ai_summary_config
from domains.demo_merchant.utils.customer_insights import config as insights_config


def evaluation_flow():
    return EvaluationFlow(
        identifier="demo_merchant_ef",
        displayName="Customer Monthly Evaluation",
        input_dataset="demo_merchant_customer_monthly",
        data_permission="dpv:demo_merchant",
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
                # Adjust identifiers if your registered models differ:
                feature_extraction_model=ModelReference('demo_merchant_fe', tags={"version": "release"}),
                detection_model=ModelReference('demo_merchant_ad', tags={"version": "release"}),
                pattern_length=2
            )
        ],
        alert_conf=ai_summary_config(),

        # ==================== GLOBAL TRACE ====================
                
        global_trace_query=TraceQuery(
            identifier="global_tq",
            identifier_column="transaction_id",
            dataset="demo_merchant_transactions",
            sql="""
                SELECT ds.*
                FROM {dataset_table} ds
                WHERE merchant_id = {activity.merchant_id}
                  AND transaction_datetime >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                  AND transaction_datetime <  {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL
            """,
        ),

        # ==================== FEATURE-SPECIFIC TRACES ====================
        trace_queries=[
            # Low-value transactions (to compute ratio) — excluye refunds/chargebacks
            TraceQuery(
                identifier="tq_low_value_trx",
                identifier_column="transaction_id",
                features=["low_value_trx_ratio"],
                dataset="demo_merchant_transactions",
                sql="""
                    SELECT ds.*
                    FROM {dataset_table} ds
                    WHERE merchant_id = {activity.merchant_id}
                      AND amount > 0
                      AND amount < 50.0                               -- low-value threshold (ajustable)
                      AND COALESCE(is_refund, FALSE) = FALSE
                      AND COALESCE(is_chargeback, FALSE) = FALSE
                      AND transaction_datetime >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                      AND transaction_datetime <  {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL
                """,
            ),

            # Dormant account (trae toda la actividad para verificar inactividad)
            TraceQuery(
                identifier="tq_dormant_account",
                identifier_column="transaction_id",
                features=["is_dormant_account"],
                dataset="demo_merchant_transactions",
                sql="""
                    SELECT ds.*
                    FROM {dataset_table} ds
                    WHERE merchant_id = {activity.merchant_id}
                      AND transaction_datetime >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                      AND transaction_datetime <  {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL
                """,
            ),

            # Transaction spike (conteo/monto) — opcionalmente excluye reversas para evitar ruido
            TraceQuery(
                identifier="tq_spike_of_trx",
                identifier_column="transaction_id",
                features=["spike_of_trx"],
                dataset="demo_merchant_transactions",
                sql="""
                    SELECT ds.*
                    FROM {dataset_table} ds
                    WHERE merchant_id = {activity.merchant_id}
                      AND COALESCE(is_refund, FALSE) = FALSE
                      AND COALESCE(is_chargeback, FALSE) = FALSE
                      AND transaction_datetime >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                      AND transaction_datetime <  {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL
                """,
            ),

            # Refund / chargeback ratio
            TraceQuery(
                identifier="tq_refund_ratio",
                identifier_column="transaction_id",
                features=["refund_count_ratio"],
                dataset="demo_merchant_transactions",
                sql="""
                    SELECT ds.*
                    FROM {dataset_table} ds
                    WHERE merchant_id = {activity.merchant_id}
                      AND (
                           COALESCE(is_refund, FALSE) = TRUE
                        OR COALESCE(is_chargeback, FALSE) = TRUE
                      )
                      AND transaction_datetime >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                      AND transaction_datetime <  {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL
                """,
            ),

            # Revenue mismatch — sin campos de settlement en este dataset, trae todo para reconciliar externamente
            TraceQuery(
                identifier="tq_revenue_mismatch",
                identifier_column="transaction_id",
                features=["revenue_mismatch"],
                dataset="demo_merchant_transactions",
                sql="""
                    SELECT ds.*
                    FROM {dataset_table} ds
                    WHERE merchant_id = {activity.merchant_id}
                      AND transaction_datetime >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                      AND transaction_datetime <  {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL
                """,
            ),

            # Avg txn amount ratio — promedio sobre ventas netas (excluye refunds/chargebacks)
            TraceQuery(
                identifier="tq_avg_txn_amt_ratio",
                identifier_column="transaction_id",
                features=["avg_txn_amt_ratio"],
                dataset="demo_merchant_transactions",
                sql="""
                    SELECT ds.*
                    FROM {dataset_table} ds
                    WHERE merchant_id = {activity.merchant_id}
                      AND amount > 0
                      AND COALESCE(is_refund, FALSE) = FALSE
                      AND COALESCE(is_chargeback, FALSE) = FALSE
                      AND transaction_datetime >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                      AND transaction_datetime <  {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL
                """,
            ),

            # Rapid load -> transfer — este schema no distingue outflows; traemos todo para que la lógica lo derive externamente
            TraceQuery(
                identifier="tq_rapid_load_transfer",
                identifier_column="transaction_id",
                features=["rapid_load_transfer"],
                dataset="demo_merchant_transactions",
                sql="""
                    SELECT ds.*
                    FROM {dataset_table} ds
                    WHERE merchant_id = {activity.merchant_id}
                      AND transaction_datetime >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                      AND transaction_datetime <  {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL
                """,
            ),
        ],

        # If you want to enable related graph, uncomment and adjust:
        related_graph=RelatedGraph(
            identifier="demo_merchant_graph",
            node_mappings={
                # Example mapping:
                "AC": [PropertyToFieldMapping(field="merchant_id", property="AN")]
            }
        ),

        #If you want customer insights in alerts:
        customer_insights=insights_config(),
    )


def entities():
    return [evaluation_flow()]

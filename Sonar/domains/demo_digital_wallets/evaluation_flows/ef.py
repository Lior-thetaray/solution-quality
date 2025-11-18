from typing import List
from thetaray.api.solution import EvaluationFlow, AlgoEvaluationStep, TraceQuery
from thetaray.api.solution.evaluation import (
    ModelReference, RelatedGraph, PropertyToFieldMapping,
    EvaluationTimeWindowUnit, EFRuleBuilderConfig
)
from domains.demo_digital_wallets.utils.ai_summarization import config as ai_summary_config
from domains.demo_digital_wallets.utils.customer_insights import config as insights_config


def evaluation_flow():
    return EvaluationFlow(
        identifier="demo_digital_wallets_ef",
        displayName="Customer Monthly Evaluation",
        input_dataset="demo_digital_wallets_customer_monthly",
        data_permission="dpv:demo_digital_wallets",
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
                
                feature_extraction_model=ModelReference('demo_dwallets_fe', tags={"version": "release"}),
                detection_model=ModelReference('demo_dwallets_ad', tags={"version": "release"}),
                pattern_length=2
            )
        ],
        alert_conf=ai_summary_config(),

      
        global_trace_query=TraceQuery(
            identifier="global_tq",
            identifier_column="transaction_id",
            dataset="demo_digital_wallets_transactions",
            sql="""
                SELECT ds.*
                FROM {dataset_table} ds
                WHERE client_id = {activity.client_id}
                  AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                  AND tr_partition <  {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL""",
        ),

        
        trace_queries=[
            # Structuring
            TraceQuery(
                identifier="tq_struct",
                identifier_column="transaction_id",
                features=["struct_score"],
                dataset="demo_digital_wallets_transactions",
                sql="""
                    SELECT ds.*
                    FROM {dataset_table} ds
                    WHERE client_id = {activity.client_id}
                      AND direction = 'inflow'
                      AND amount >= 1.0
                      AND amount < 1000.0
                      AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                      AND tr_partition <  {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL""",
            ),

            # Rapid Load & Spend
            TraceQuery(
                identifier="tq_rapid_spend",
                identifier_column="transaction_id",
                features=["rapid_spend"],
                dataset="demo_digital_wallets_transactions",
                sql="""
                    SELECT ds.*
                    FROM {dataset_table} ds
                    WHERE client_id = {activity.client_id}
                      AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                      AND tr_partition <  {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL""",
            ),

            # Many-to-One
            TraceQuery(
                identifier="tq_mto",
                identifier_column="transaction_id",
                features=["mto_score"],
                dataset="demo_digital_wallets_transactions",
                sql="""
                    SELECT ds.*
                    FROM {dataset_table} ds
                    WHERE client_id = {activity.client_id}
                      AND direction = 'outflow'
                      AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                      AND tr_partition <  {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL""",
            ),

            # Crypto usage 
            TraceQuery(
                identifier="tq_crypto",
                identifier_column="transaction_id",
                features=["crypto_score"],
                dataset="demo_digital_wallets_transactions",
                sql="""
                    SELECT ds.*
                    FROM {dataset_table} ds
                    WHERE client_id = {activity.client_id}
                      AND (
                            transaction_type IN ('crypto_purchase','crypto_sale')
                         OR LOWER(COALESCE(merchant_category,'')) = 'crypto exchange'
                      )
                      AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                      AND tr_partition <  {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL""",
            ),

            # Pct Domestic
            TraceQuery(
                identifier="tq_pct_domestic",
                identifier_column="transaction_id",
                features=["pct_domestic"],
                dataset="demo_digital_wallets_transactions",
                sql="""
                    SELECT ds.*
                    FROM {dataset_table} ds
                    WHERE client_id = {activity.client_id}
                      AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                      AND tr_partition <  {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL""",
            ),

            # High-risk jurisdictions (null-safe)
            TraceQuery(
                identifier="tq_high_risk_countries",
                identifier_column="transaction_id",
                features=["pct_domestic"],  # misma tarjeta de geografía
                dataset="demo_digital_wallets_transactions",
                sql="""
                    SELECT ds.*
                    FROM {dataset_table} ds
                    WHERE client_id = {activity.client_id}
                      AND UPPER(COALESCE(country_destination,'')) IN ('CU','IR','SY','RU')
                      AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                      AND tr_partition <  {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL""",
            ),

            # Reversals
            TraceQuery(
                identifier="tq_reversals",
                identifier_column="transaction_id",
                features=["rev_ratio"],
                dataset="demo_digital_wallets_transactions",
                sql="""
                    SELECT ds.*
                    FROM {dataset_table} ds
                    WHERE client_id = {activity.client_id}
                      AND is_reversal = TRUE
                      AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                      AND tr_partition <  {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL""",
            ),

            # Activity Spike 
            TraceQuery(
                identifier="tq_act_spike",
                identifier_column="transaction_id",
                features=["act_spike"],
                dataset="demo_digital_wallets_transactions",
                sql="""
                    SELECT ds.*
                    FROM {dataset_table} ds
                    WHERE client_id = {activity.client_id}
                      AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                      AND tr_partition <  {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL""",
            ),

            
            TraceQuery(
                identifier="tq_amounts",
                identifier_column="transaction_id",
                features=["total_tx_amount", "avg_tx_amount"],
                dataset="demo_digital_wallets_transactions",
                sql="""
                    SELECT ds.*
                    FROM {dataset_table} ds
                    WHERE client_id = {activity.client_id}
                      AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                      AND tr_partition <  {activity.year_month} + interval '1 month' + ({occurred_after} || ' DAY')::INTERVAL""",
            ),
        ],

        related_graph=RelatedGraph(
            identifier="demo_dwallets_graph",
            node_mappings={
                "AC": [PropertyToFieldMapping(field="client_id", property="AN")]
            }
        ),
        customer_insights=insights_config()
    )


def entities():
    return [evaluation_flow()]

from typing import List
from thetaray.api.solution import EvaluationFlow, AlgoEvaluationStep, TraceQuery
from thetaray.api.solution.evaluation import ModelReference, RelatedGraph, PropertyToFieldMapping, EvaluationTimeWindowUnit, EFRuleBuilderConfig
from domains.demo_human_trafficking.utils.ai_summarization import config as ai_summary_config
from domains.demo_human_trafficking.utils.customer_insights import config as insights_config


def evaluation_flow():
    return EvaluationFlow(
        identifier="demo_human_trafficking_ef",
        displayName="Customer Monthly Evaluation",
        input_dataset="demo_human_trafficking_customer_monthly",
        data_permission="dpv:demo_human_trafficking",
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
                feature_extraction_model=ModelReference('demo_human_trafficking_fe', tags = {"version": "release"}),
                detection_model=ModelReference('demo_human_trafficking_ad', tags={"version": "release"}),
                pattern_length=2
            )
        ],
        alert_conf=ai_summary_config(),
        global_trace_query=TraceQuery(
            identifier="global_tq",
            identifier_column="transaction_id",
            dataset="demo_human_trafficking_transactions",
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
                    "income_websites_amt",
                ],
                dataset="demo_human_trafficking_transactions",
                sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND transaction_type_code = 'WEB_IN'
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """,
            ),
            TraceQuery(
                identifier="feat_tq_2",
                identifier_column="transaction_id",
                features=[
                    "income_websites_cnt",
                ],
                dataset="demo_human_trafficking_transactions",
                sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND transaction_type_code = 'WEB_IN'
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """,
            ),
            TraceQuery(
                identifier="feat_tq_3",
                identifier_column="transaction_id",
                features=[
                    "ad_agency_out_cnt",
                ],
                dataset="demo_human_trafficking_transactions",
                sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND merchant_category_code IN  ('7311', '7333')
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """,
            ),

            TraceQuery(
                identifier="feat_tq_4",
                identifier_column="transaction_id",
                features=[
                    "ad_agency_out_amt",
                ],
                dataset="demo_human_trafficking_transactions",
                sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND merchant_category_code IN  ('7311', '7333')
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """,
            ),


            TraceQuery(
                identifier="feat_tq_5",
                identifier_column="transaction_id",
                features=[
                    "risky_expenses_cnt",
                ],
                dataset="demo_human_trafficking_transactions",
                sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND merchant_category_code IN ('5814', '7011', '5912')
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """,
            ),

            TraceQuery(
                identifier="feat_tq_6",
                identifier_column="transaction_id",
                features=[
                    "round_amounts",
                ],
                dataset="demo_human_trafficking_transactions",
                sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND transaction_type_code = 'ROUND_AMOUNT'
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """,
            ),
            TraceQuery(
                identifier="feat_tq_7",
                identifier_column="transaction_id",
                features=[
                    "cnt_distinct_atm",

                ],
                dataset="demo_human_trafficking_transactions",
                sql="""
                SELECT ds.* FROM {dataset_table} ds
                WHERE customer_id = {activity.customer_id}
                AND transaction_type_code = 'ATM'
                AND tr_partition >= {activity.year_month} - ({occurred_before} || ' DAY')::INTERVAL
                AND tr_partition < {activity.year_month} + interval '1 month' + ({occurred_after} || 'DAY')::INTERVAL
                """,
            ),
        ],
        related_graph=RelatedGraph(
            identifier="demo_human_traf_graph",
            node_mappings={
                "AC": [PropertyToFieldMapping(field="customer_id", property="AN")]
            }
        ),
        customer_insights=insights_config()
    )


def entities():
    return [evaluation_flow()]

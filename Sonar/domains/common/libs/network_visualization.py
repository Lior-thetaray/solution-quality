from pyspark.sql import DataFrame, functions as f
from typing import Tuple


def create_alert_graph_entities(alerted_activities_df: DataFrame,
                                evaluated_activities_df: DataFrame,
                                entity_id_column_name: str,
                                date_column_name: str) -> Tuple[DataFrame, DataFrame]:
    """
    Create entities for alert graph - nodes and edges

    Parameters
    ----------
    alerted_activities_df: DataFrame
        data frame of the alerted activities, should be fetched using read_alerted_activities() API of platform
    evaluated_activities_df: DataFrame
        date frame of the evaluated activities, should be fetched using load_evaluated_activities() API of platform
    entity_id_column_name: str
        name of the column that contains the entity id, e.g. creditor_account_number / sender_id
    date_column_name: str
        name of the column that contains the effective/occurred_on date
    """

    joined_alerted_activities_df = evaluated_activities_df.join(alerted_activities_df, 'tr_id')
    selected_activity_fields = joined_alerted_activities_df.select('tr_id', 'risk_id', date_column_name, 'is_suppressed', entity_id_column_name)
    selected_activity_fields.cache()
    alert_nodes_df = selected_activity_fields.withColumn('id', f.concat(f.col('tr_id'),f.lit('_'), f.col('risk_id'))) \
        .withColumnRenamed(date_column_name, 'effective_date') \
        .withColumnRenamed('is_suppressed', 'suppressed') \
        .withColumnRenamed('tr_id', 'activity_id') \
        .drop(entity_id_column_name)
    alert_edges_df = selected_activity_fields.withColumn('id', f.concat(f.col('tr_id'),f.lit('_'), f.col('risk_id'))) \
        .withColumnRenamed(date_column_name, 'effective_date') \
        .withColumn('source_node', f.col('id')) \
        .withColumnRenamed(entity_id_column_name, 'target_node') \
        .drop('is_suppressed', 'tr_id', 'risk_id')
    return alert_nodes_df, alert_edges_df

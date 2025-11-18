from datetime import datetime, timedelta

from airflow.models import DAG

from thetaray.api.airflow import RunNotebookOperator

default_args = {
    "owner": "Airflow",
    "depends_on_past": False,
    "start_date": datetime(2020, 2, 20),
    # "schedule_interval": "@daily",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    dag_id="default_end_to_end",
    catchup=False,
    default_args=default_args,
    schedule_interval=None,
)

copy_data_to_s3 = RunNotebookOperator(
    task_id="copy_data_to_s3",
    domain="default",
    notebook_name="copy_data_to_s3",
    dag=dag,
)

upload_data = RunNotebookOperator(
    task_id="upload_data",
    domain="default",
    notebook_name="upload_data",
    dag=dag,
)

entity_resolution = RunNotebookOperator(
    task_id="entity_resolution",
    domain="default",
    notebook_name="tr_entity_resolution",
    dag=dag,
)

wrangling = RunNotebookOperator(
    task_id="wrangling",
    domain="default",
    notebook_name="wrangling",
    dag=dag,
)

training = RunNotebookOperator(
    task_id="training",
    domain="default",
    notebook_name="tr-algo-train",
    dag=dag,
)

detecting = RunNotebookOperator(
    task_id="detecting",
    domain="default",
    notebook_name="tr-algo-detect",
    dag=dag,
)

publishing_activities = RunNotebookOperator(
    task_id="publishing_activities",
    domain="default",
    notebook_name="publish-activities",
    dag=dag,
)

publishing_dataset = RunNotebookOperator(
    task_id="publishing_dataset",
    domain="default",
    notebook_name="publish",
    dag=dag,
)

decisioning = RunNotebookOperator(
    task_id="decisioning",
    domain="default",
    notebook_name="decisioning",
    dag=dag,
)

distributing = RunNotebookOperator(
    task_id="distributing",
    domain="default",
    notebook_name="distribution",
    dag=dag,
)

graph_netviz = RunNotebookOperator(
    task_id="graph_netviz",
    domain="default",
    notebook_name="graphing-network-viz",
    dag=dag,
)

(
    copy_data_to_s3
    >> upload_data
    >> entity_resolution
    >> wrangling
    >> training
    >> detecting
    >> publishing_activities
    >> publishing_dataset
    >> decisioning
    >> distributing
    >> graph_netviz
)


if __name__ == "__main__":
    dag.cli()

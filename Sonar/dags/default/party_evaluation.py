from datetime import datetime, timedelta

from airflow.models import DAG

from thetaray.api.airflow import RunNotebookOperator

default_args = {
    "owner": "Airflow",
    "depends_on_past": False,
    "start_date": datetime(2020, 2, 20),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    dag_id="default_party_evaluation",
    catchup=False,
    default_args=default_args,
    schedule_interval=None,
)

party_wrangling = RunNotebookOperator(
    task_id="party_wrangling",
    domain="default",
    notebook_name="wrangling_party",
    dag=dag,
)

party_detecting = RunNotebookOperator(
    task_id="party_detecting",
    domain="default",
    notebook_name="tr-algo-party-detect",
    dag=dag,
)

publishing_activities = RunNotebookOperator(
    task_id="publishing_activities",
    domain="default",
    notebook_name="publish-activities-party",
    dag=dag,
)
party_decisioning = RunNotebookOperator(
    task_id="party_decisioning",
    domain="default",
    notebook_name="decisioning-party",
    dag=dag,
)

party_distributing = RunNotebookOperator(
    task_id="party_distributing",
    domain="default",
    notebook_name="distribution-party",
    dag=dag,
)

party_wrangling >> party_detecting >> publishing_activities >> party_decisioning >> party_distributing

if __name__ == "__main__":
    dag.cli()

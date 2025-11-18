from datetime import timedelta

from airflow.models import DAG

from thetaray.api.airflow import RunNotebookOperator


default_args = {
    "owner": "Airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    dag_id="default_generate_customer_insights_data",
    catchup=False,
    default_args=default_args,
    schedule_interval=None,
)

generate_customer_insights_data = RunNotebookOperator(
    task_id="generate_customer_insights_data",
    domain="default",
    notebook_name="generate_customer_insights_data",
    dag=dag,
)


if __name__ == "__main__":
    dag.cli()

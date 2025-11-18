import datetime
import yaml
from airflow.models import DAG
from thetaray.api.airflow import RunNotebookOperator, ExecutionDateMode

default_args = {
    'owner': 'Airflow',
    'depends_on_past': False,
    'start_date': datetime.datetime(1970, 1, 1),
    'end_date': datetime.datetime(1970, 1, 31),
    'retries': 0,
    'retry_delay': datetime.timedelta(seconds=5),
    'execution_date_mode': ExecutionDateMode.PERIOD_END,
}

domain = 'demo_digital_wallets'

with open(f'/thetaray/git/solutions/domains/{domain}/config/spark_config.yaml') as spark_config_file:
    spark_config = yaml.load(spark_config_file, yaml.FullLoader)['spark_config_a']

dag = DAG(
    dag_id=f'{domain}_setup',
    catchup=False,  # evita ejecuciones atrasadas
    schedule_interval='0 0 1 * *',
    default_args=default_args,
    params={},
)

clear_data = RunNotebookOperator(
    task_id="clear_data",
    domain=domain,
    notebook_name="clear_everything",
    container_cpu="500m",
    container_memory="4Gi",               
    dag=dag,
    spark_conf=spark_config
)

dataprep = RunNotebookOperator(
    task_id="1_data_generation",
    domain=domain,
    notebook_name="1_data_generation",
    container_cpu="1000m",
    container_memory="6Gi",
    dag=dag,
    spark_conf=spark_config
)

train = RunNotebookOperator(
    task_id="2_train",
    domain=domain,
    notebook_name="2_train",
    container_cpu="1000m",
    container_memory="6Gi",
    dag=dag,
    spark_conf=spark_config
)

detection = RunNotebookOperator(
    task_id="3_detection",
    domain=domain,
    notebook_name="3_detection",
    container_cpu="4000m",
    container_memory="16Gi",
    dag=dag,
    spark_conf=spark_config
)

identify = RunNotebookOperator(
    task_id="4_identify",
    domain=domain,
    notebook_name="4_identify",
    container_cpu="1000m",
    container_memory="8Gi",
    dag=dag,
    spark_conf=spark_config
)

distribute = RunNotebookOperator(
    task_id="5_distribute",
    domain=domain,
    notebook_name="5_distribute",
    container_cpu="1000m",
    container_memory="8Gi",
    dag=dag,
    spark_conf=spark_config
)

graph = RunNotebookOperator(
    task_id="7_graph",
    domain=domain,
    notebook_name="network_viz",
    container_cpu="1000m",
    container_memory="4Gi",
    dag=dag,
    spark_conf=spark_config
)

insights = RunNotebookOperator(
    task_id="6_insights",
    domain=domain,
    notebook_name="customer_insights",
    container_cpu="1000m",
    container_memory="4Gi",
    dag=dag,
    spark_conf=spark_config
)

# Orden de ejecución
clear_data >> dataprep >> train >> detection >> identify >> distribute >> insights >> graph

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

domain = 'demo_ret_smb'

with open(f'/thetaray/git/solutions/domains/{domain}/config/spark_config.yaml') as spark_config_file:
    spark_config = yaml.load(spark_config_file, yaml.FullLoader)['spark_config_a']

dag = DAG(
    dag_id=f'{domain}_setup',
    catchup=True,
    schedule='0 0 1 * *',
    default_args=default_args,
    params={},
)

clear_data = \
    RunNotebookOperator(task_id="clear_data",
                        domain=domain,
                        notebook_name="clear_everything",
                        dag=dag,
                        spark_conf=spark_config)

data_gen = \
    RunNotebookOperator(task_id="data_gen",
                        domain=domain,
                        notebook_name="data_generation",
                        dag=dag,
                        spark_conf=spark_config)

train_model = \
    RunNotebookOperator(task_id="train_model",
                        domain=domain,
                        notebook_name="train",
                        dag=dag,
                        spark_conf=spark_config)

detect = \
    RunNotebookOperator(task_id="detect",
                        domain=domain,
                        notebook_name="detection",
                        dag=dag,
                        spark_conf=spark_config)

identify = \
    RunNotebookOperator(task_id="identify",
                        domain=domain,
                        notebook_name="identify",
                        dag=dag,
                        spark_conf=spark_config)

distribute = \
    RunNotebookOperator(task_id="distribute",
                        domain=domain,
                        notebook_name="distribute",
                        dag=dag,
                        spark_conf=spark_config)

network_viz = \
    RunNotebookOperator(task_id="network_viz",
                        domain=domain,
                        notebook_name="network_viz",
                        dag=dag,
                        spark_conf=spark_config)

customer_insights = \
    RunNotebookOperator(task_id="customer_insights",
                        domain=domain,
                        notebook_name="customer_insights",
                        dag=dag,
                        spark_conf=spark_config)

clear_data >> data_gen >> train_model >> detect >> identify >> distribute >> network_viz >> customer_insights

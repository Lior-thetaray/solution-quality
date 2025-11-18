import datetime
import os
from common.libs.config.loader import load_config
import flatdict


def load_dag_config(path, domain) -> dict:
    default_config = load_config('dags/default.yaml', domain=domain)['dag']
    effective_config = flatdict.FlatDict(default_config)
    try:
        dag_config = load_config(f'dags/{path}', domain=domain)
        effective_config.update(flatdict.FlatDict(dag_config.get('dag', {})))
    except FileNotFoundError:
        print(f'Default dag config is used for dag {path}')
    effective_config['default_args']['start_date'] = datetime.datetime.strptime(effective_config['default_args']['start_date'], '%Y-%m-%d')
    effective_config['default_args']['retry_delay'] = datetime.timedelta(minutes=effective_config['default_args']['retry_delay'])
    return effective_config.as_dict()


def load_task_config(path, domain, task_id) -> dict:
    default_config = load_config('dags/default.yaml', domain=domain)['task']
    effective_config = flatdict.FlatDict(default_config)
    try:
        dag_config = load_config(f'dags/{path}', domain=domain)
        task_config = dag_config.get('tasks', {}).get(task_id, {})
        effective_config.update(flatdict.FlatDict(task_config))
        if not task_config:
            print(f'Default task config is used for task {task_id}')
    except FileNotFoundError:
        print(f'Default task config is used for task {task_id}')
    effective_config['execution_timeout'] = datetime.timedelta(minutes=effective_config['execution_timeout'])
    return effective_config.as_dict()

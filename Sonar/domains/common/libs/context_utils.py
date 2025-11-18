import inspect

from thetaray.api.solution import DataSet
from thetaray.api.connector.connector import Connector
from thetaray.api.context import JobExecutionContext


def get_connector(context: JobExecutionContext, identifier: str) -> Connector:
    """Given the context and the connector identifier, if available,
    returns the connector object, raise a ValueError otherwise.

    Parameters
    ----------
    context: JobExecutionContext
        The context of the relevant domain
    identifier: str
        The identifier of the connector
    
    Returns
    ----------
    Connector
        The corresponding connector object
    """
    connector = next((connector for connector in context.solution.connectors if connector.identifier == identifier), None)
    if connector is None:
        raise ValueError(f'Not found connector with identifier {identifier}')
    return connector


def get_dataset(context: JobExecutionContext, identifier: str) -> DataSet:
    """Given the context and the dataset identifier, if available,
    returns the dataset object, raise a ValueError otherwise.

    Parameters
    ----------
    context: JobExecutionContext
        The context of the relevant domain
    identifier: str
        The identifier of the DataSet
    
    Returns
    ----------
    DataSet
        The corresponding Dataset object
    """
    ds = next((ds for ds in context.solution.datasets if ds.identifier == identifier), None)
    if ds is None:
        raise ValueError(f'Not found dataset with identifier {identifier}')
    return ds


def is_run_triggered_from_airflow() -> bool:
    """Used to determine whether run is triggered by Airflow or not

    Returns
    ----------
    bool
        True if run is triggered from airflow, else False (notebook is triggered manually by the user)
    """
    parent_globals = inspect.stack()[1][0].f_globals
    return "serialized_context" in parent_globals


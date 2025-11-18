from typing import Tuple

from pyspark.sql import DataFrame, functions as f, WindowSpec, Column

from enum import Enum, auto

from common.libs.config.loader import load_config

import typing
from collections import OrderedDict

class Z_Score_Method(Enum):
    MEAN = auto()
    MEDIAN = auto()


zscore_conf = load_config('libs/zscore.yaml', domain='common')


def enrich_with_z_score(col: str,
                        window: WindowSpec,
                        round_digits: int = None,
                        truncate_min_max: Tuple[int, int] = None,
                        output_column: str = None,
                        z_score_method: Z_Score_Method = None) -> typing.OrderedDict[str, Column]:
    """Enrich data frame with z-score based on given column

    Parameters
    ----------
    df: DataFrame
        Dataframe with a column to calculate z-score for
    col: str
        The column to calculate z-score for
    window: WindowSpec
        The z-score is calculated based on a given window
    round_digits: int
        Use round function so the z-score will be truncated
    truncate_min_max: tuple
        A tuple of integers to truncate the z-score column to, default to None
    output_column: str
        The name of the output column with the z-score can be configured, default to the name of the column to calculate z-score for with a 'z_score_' prefix
    z_score_method: Z_Score_Method
        Z-score can be calculated using mean/median

    Returns
    ----------
    dict
        A dict contains the z-score column and its implementation
    """
    round_digits = round_digits if round_digits is not None else zscore_conf['round_digits']
    truncate_min_max = truncate_min_max if truncate_min_max is not None else zscore_conf['truncate_min_max']
    z_score_method = z_score_method if z_score_method is not None else Z_Score_Method[zscore_conf['z_score_method'].upper()]
    z_score_column_name = output_column or f'z_score_{col}'

    columns = OrderedDict()
    columns[f'stddev_{col}'] = f.round(f.stddev(col).over(window), round_digits)
    if z_score_method == Z_Score_Method.MEAN:
        columns[f'avg_{col}'] = f.round(f.avg(col).over(window), round_digits)
        columns[z_score_column_name] = f.round((f.col(col) - columns[f'avg_{col}']) / columns[f'stddev_{col}'], round_digits)
    elif z_score_method == Z_Score_Method.MEDIAN:
        columns[f'median_{col}'] = f.round(f.percentile_approx(col, 0.5).over(window), round_digits)
        columns[z_score_column_name] = f.round((f.col(col) - columns[f'median_{col}']) / columns[f'stddev_{col}'], round_digits)
    else:
        raise ValueError(f"z_score_method {z_score_method} is not supported")

    for k in {f'avg_{col}', f'median_{col}', f'stddev_{col}'}:
        columns.pop(k, None)
    if truncate_min_max is not None:
        columns[z_score_column_name] = f.when(columns[z_score_column_name] < truncate_min_max[0], truncate_min_max[0])\
                                        .when(columns[z_score_column_name] > truncate_min_max[1], truncate_min_max[1])\
                                        .otherwise(columns[z_score_column_name])
    return columns

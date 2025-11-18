import datetime
from typing import Tuple

from abc import abstractmethod
from pyspark.sql import DataFrame

from common.libs import dates as dates_lib
from common.libs.feature_engineering import max_look_back_monthly_features
from common.notebook_utils.wrangling.wrangling_execution_strategy import WranglingExecutionStrategy


class MonthlyWranglingExecution(WranglingExecutionStrategy):

    def __init__(self, config: dict, trx_date_column_name: str, features: list):
        self.trx_date_column_name = trx_date_column_name
        self.monthly_data_horizon = config['monthly_data_horizon']
        self.max_look_back = max_look_back_monthly_features(features, config)
        if self.max_look_back > self.monthly_data_horizon:
            raise Exception(f'Monthly data horizon is configured to be {self.monthly_data_horizon} but there is at least 1 active feature'
                            f' that requires a longer window size - {self.max_look_back} months.\n'
                            f'Either increase the monthly data horizon, deactivate the feature or decrease the required window size of the feature')

    def enrich_df_pre_feature_engineering(self, df: DataFrame) -> DataFrame:
        df = dates_lib.add_day_offset_column(df, self.trx_date_column_name, 'day_offset')
        df = dates_lib.add_month_offset_column(df, self.trx_date_column_name, 'month_offset')
        return df

    def enrich_df_post_feature_engineering(self, df: DataFrame) -> DataFrame:
        return dates_lib.month_offset_to_year_month_columns(df, 'month_offset', 'year_month')

    @abstractmethod
    def get_read_date_range(self) -> Tuple[datetime.datetime, datetime.datetime]:
        pass

    @abstractmethod
    def get_write_date_range(self) -> Tuple[datetime.datetime, datetime.datetime]:
        pass

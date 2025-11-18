from typing import Tuple
from abc import abstractmethod
from pyspark.sql import DataFrame
import datetime
import dateutil.relativedelta
from common.libs import dates as dates_lib
from common.libs.feature_engineering import max_look_back_daily_weekly_features
from common.notebook_utils.wrangling.wrangling_execution_strategy import WranglingExecutionStrategy


class WeeklyWranglingExecution(WranglingExecutionStrategy):

    def __init__(self, config: dict, trx_date_column_name: str, features: list):
        self.config = config
        self.trx_date_column_name = trx_date_column_name
        self.features = features
        self.max_look_back = max_look_back_daily_weekly_features(self.features, self.config)

    def enrich_df_pre_feature_engineering(self, df: DataFrame) -> DataFrame:
        return dates_lib.add_week_offset_column(df, self.trx_date_column_name, 'week_offset')

    def enrich_df_post_feature_engineering(self, df: DataFrame) -> DataFrame:
        return dates_lib.week_offset_to_first_monday_columns(df, 'week_offset', 'first_monday_week')

    @abstractmethod
    def get_read_date_range(self) -> Tuple[datetime.datetime, datetime.datetime]:
        pass

    @abstractmethod
    def get_write_date_range(self) -> Tuple[datetime.datetime, datetime.datetime]:
        pass

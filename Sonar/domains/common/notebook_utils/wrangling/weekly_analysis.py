from typing import Tuple
from pyspark.sql import DataFrame
import datetime
import dateutil.relativedelta
from common.libs import dates as dates_lib
from common.libs.feature_engineering import max_look_back_daily_weekly_features
from common.notebook_utils.wrangling.wrangling_execution_strategy import WranglingExecutionStrategy
from common.notebook_utils.wrangling.weekly import WeeklyWranglingExecution


class WeeklyAnalysisWranglingExecution(WeeklyWranglingExecution):

    def __init__(self, config: dict, trx_date_column_name: str, features: list):
        WeeklyWranglingExecution.__init__(self, config, trx_date_column_name, features)
        self.batch_date = datetime.datetime.strptime(config['first_monday_week_execution'], "%Y-%m-%d")

        if self.batch_date.weekday() != 0:
            raise ValueError("You must use Monday day for weekly analysis")

    def get_read_date_range(self) -> Tuple[datetime.datetime, datetime.datetime]:
        start_date = self.batch_date + dateutil.relativedelta.relativedelta(days=-self.max_look_back)
        end_date = self.batch_date + dateutil.relativedelta.relativedelta(weeks=1)
        return start_date, end_date

    def get_write_date_range(self) -> Tuple[datetime.datetime, datetime.datetime]:
        return self.batch_date, self.batch_date + dateutil.relativedelta.relativedelta(weeks=1)

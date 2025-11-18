from typing import Tuple
import datetime
import dateutil.relativedelta
from common.notebook_utils.wrangling.daily import DailyWranglingExecution


class DailyAnalysisWranglingExecution(DailyWranglingExecution):

    def __init__(self, config: dict, trx_date_column_name: str, features: list):
        DailyWranglingExecution.__init__(self, config, trx_date_column_name, features)
        self.batch_date = datetime.datetime.strptime(config['date_execution'], "%Y-%m-%d")

    def get_read_date_range(self) -> Tuple[datetime.datetime, datetime.datetime]:
        start_date = self.batch_date + dateutil.relativedelta.relativedelta(days=-self.max_look_back)
        end_date = self.batch_date + dateutil.relativedelta.relativedelta(days=1)
        return start_date, end_date

    def get_write_date_range(self) -> Tuple[datetime.datetime, datetime.datetime]:
        return self.batch_date, self.batch_date + dateutil.relativedelta.relativedelta(days=1)

import datetime
from typing import Tuple

import dateutil.relativedelta

from common.notebook_utils.wrangling.monthly import MonthlyWranglingExecution


class MonthlyTrainWranglingExecution(MonthlyWranglingExecution):

    def __init__(self, config: dict, trx_date_column_name: str, features: list):
        MonthlyWranglingExecution.__init__(self, config, trx_date_column_name, features)
        self.train_start_date = datetime.datetime.strptime(config['start_date'], "%Y-%m-%d")
        self.train_end_date = datetime.datetime.strptime(config['end_date'], "%Y-%m-%d")

    def get_read_date_range(self) -> Tuple[datetime.datetime, datetime.datetime]:
        start_date = self.train_start_date + dateutil.relativedelta.relativedelta(months=-self.max_look_back)
        return start_date, self.train_end_date

    def get_write_date_range(self) -> Tuple[datetime.datetime, datetime.datetime]:
        return self.train_start_date, self.train_end_date

from abc import ABC, abstractmethod
from typing import Tuple
from pyspark.sql import DataFrame
import datetime


class WranglingExecutionStrategy(ABC):

    @abstractmethod
    def get_read_date_range(self) -> Tuple[datetime.datetime, datetime.datetime]:
        pass

    @abstractmethod
    def enrich_df_pre_feature_engineering(self, df: DataFrame) -> DataFrame:
        return df

    @abstractmethod
    def enrich_df_post_feature_engineering(self, df: DataFrame) -> DataFrame:
        return df

    @abstractmethod
    def get_write_date_range(self) -> Tuple[datetime.datetime, datetime.datetime]:
        pass

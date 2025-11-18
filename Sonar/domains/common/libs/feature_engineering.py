from thetaray.api.solution import Field
import typing
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import List, Set
from pyspark.sql import DataFrame, Column

from pyspark.sql import functions as f
from common.libs.config.loader import load_config
from common.libs.features_discovery import feature_ids_to_params

class FeatureDescriptor(ABC):

    @property
    @abstractmethod
    def identifier(self) -> str:
        pass

    @property
    @abstractmethod
    def version(self) -> int:
        pass

    @property
    def fqfn(self) -> str:
        return f'{self.identifier}_v{self.version}'

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def required_columns(self) -> Set[str]:
        pass

    @property
    def required_params(self) -> Set[str]:
        return set()

    @property
    def output_columns(self) -> Set[str]:
        return {field.identifier for field in self.output_fields}

    @property
    @abstractmethod
    def output_fields(self) -> Set[Field]:
        pass

    def __repr__(self):
        return self.fqfn


class BaseFeature(ABC):

    def trace_query(self, params: dict) -> str:
        return ""

    def get_invalid_output_columns(self, df: DataFrame) -> Set[str]:
        # invalid_cols = set()
        # for col in self.output_columns:
        #     if _col_has_zero_variance(df, col):
        #         invalid_cols.add(col)
        return False


class AggFeature(BaseFeature, ABC):

    @property
    @abstractmethod
    def group_by_keys(self) -> List[str]:
        pass

    def pre_aggs(self, params: dict) -> typing.OrderedDict[str, Column]:
        return OrderedDict()

    @abstractmethod
    def get_agg_exprs(self, params: dict) -> typing.OrderedDict[str, Column]:
        return OrderedDict()

    def post_aggs(self, params: dict) -> typing.OrderedDict[str, Column]:
        return OrderedDict()

    def apply_feature(self, df: DataFrame, params: dict) -> DataFrame:
        """Apply a single feature, used primarily for testing. For performance boost, apply multiple features together
        """
        for col_name, col in self.pre_aggs(params).items():
            df = df.withColumn(col_name, col)

        agg_exprs = [col.alias(col_name) for col_name, col in self.get_agg_exprs(params).items()]
        agg_df = df.groupBy(*self.group_by_keys).agg(*agg_exprs)

        for col_name, col in self.post_aggs(params).items():
            agg_df = agg_df.withColumn(col_name, col)

        agg_df = agg_df.orderBy(*self.group_by_keys)
        return agg_df


def _col_has_zero_variance(df: DataFrame, col: str):
    return df.select(col).distinct().limit(2).count() == 1


def max_look_back_monthly_features(features: list, config: dict = None) -> int:
    return _max_look_back_of_features('monthly_features_look_back_in_months', features, config)


def max_look_back_daily_weekly_features(features: list, config: dict = None) -> int:
    return _max_look_back_of_features('daily_weekly_features_look_back_in_days', features, config)


def _max_look_back_of_features(look_back_property_name, features: list, config: dict = None):
    max_look_back = max(0, config.get(look_back_property_name, 0))
    features_params = feature_ids_to_params(config, features).values()
    for feature_params in features_params:
        max_look_back = max(max_look_back, feature_params.get(look_back_property_name, 0))
    return max_look_back


def filter_feature_by_min_trx_amount(feature_ind_col_name):
    """
    Indicator column should ignore transactions with amount lower than the configured threshold

    param: feature_ind_col_name - column of feature indicator, must be numeric (0/1)
    """
    def decorator(function):
        def wrapper(*args, **kwargs):
            global_config = load_config('feature_engineering.yaml', domain='common')
            min_trx_amount_thr = global_config.get('min_trx_amount_thr')
            columns = function(*args, **kwargs)
            columns[feature_ind_col_name] = f.when(f.col('trx_amount') > min_trx_amount_thr, columns[feature_ind_col_name]).otherwise(0)
            return columns
        return wrapper
    return decorator

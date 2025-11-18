from pyspark.sql import DataFrame, Column
from dataclasses import dataclass

from common.libs.config.loader import load_config
from common.libs.features_loader import format_feature_version

import json

from thetaray.common.logging import logger


@dataclass
class FeatureColumn:
    feature_identifier: str
    col_name: str
    col: Column


features_executor_conf = load_config('libs/features_executor.yaml', domain='common')


class FeaturesExecutor:
    """The FeaturesExecutor is used to apply all the requested features on the given DataFrame.

    The FeatureExecutor is also responsibile for various validations related to the features.
    Every column required by any of the requested features must be part of the given DataFrame columns.
    Every param required by any of the requested features must be part of the given config argument.
    The requested features must be grouped by the same key.
    Every column that is created based on the feature implementation in the pre_aggs() or in the get_agg_exprs() 
    must have only 1 universal implementation (this is to avoid a logical error where 1 feature overrides other 
    feature  implementation for the same column or to avoid a case where same implementation for a column is done 
    for 2 different column names)

    The FeatureExecutor is optimized to compute the same column once whether when it's a column created in the 
    pre_aggs() or in the get_agg_exprs(). For example, monthly sum is an aggregation that is needed for multiple 
    features and can be computed once.

    Parameters
    ----------
    df : DataFrame
        The DataFrame to apply the features on
    features: list
        The list of requested features
    config : dict
        A configuration for the params required by the features, default to None
    """

    def __init__(self, df: DataFrame, features: list, config: dict = None, fail_on_features_validation: bool = None) -> None:
        self.df = df
        self.features = features
        self.fail_on_features_validation = fail_on_features_validation if fail_on_features_validation is not None else features_executor_conf['fail_on_features_validation']
        self.params_map = self._build_params_map(config)
        self.group_by_keys = {tuple(feature.group_by_keys) for feature in self.features}
        self.features_cols_by_stages = {"pre_aggs": {"rank": 1,
                                                     "feature_columns": [FeatureColumn(feature.identifier, col_name, col)
                                                                         for feature in self.features
                                                                         for col_name, col in feature.pre_aggs(self.params_map[feature.identifier]).items()]},
                                        "aggs": {"rank": 2,
                                                 "feature_columns": [FeatureColumn(feature.identifier, col_name, col)
                                                                     for feature in self.features
                                                                     for col_name, col in feature.get_agg_exprs(self.params_map[feature.identifier]).items()]},
                                        "post_aggs": {"rank": 3,
                                                      "feature_columns": [FeatureColumn(feature.identifier, col_name, col)
                                                                          for feature in self.features
                                                                          for col_name, col in feature.post_aggs(self.params_map[feature.identifier]).items()]}}
        self._validate_required_params_exist()
        self._validate_features()

    def execute(self) -> DataFrame:
        """
        Apply the features on the given dataframe

        Returns
        -------
        DataFrame
            The aggregated dataframe after features were applied
        """
        logger.debug(f'executing features with params: {self.params_map}')
        pre_aggs_columns = {feature_column.col_name: feature_column.col for feature_column in self.features_cols_by_stages["pre_aggs"]["feature_columns"]}
        for col_name, col in pre_aggs_columns.items():
            self.df = self.df.withColumn(col_name, col)

        agg_exprs = {feature_column.col_name: feature_column.col.alias(feature_column.col_name) for feature_column in self.features_cols_by_stages["aggs"]["feature_columns"]}.values()
        agg_df = self.df.groupBy(*next(iter(self.group_by_keys))).agg(*agg_exprs)

        features_with_invalid_output_columns = {}
        for feature in self.features:
            post_aggs_columns = {feature_column.col_name: feature_column.col for feature_column in self.features_cols_by_stages["post_aggs"]["feature_columns"]}
            for col_name, col in post_aggs_columns.items():
                agg_df = agg_df.withColumn(col_name, col)
            invalid_output_cols = feature.get_invalid_output_columns(agg_df)
            if invalid_output_cols:
                features_with_invalid_output_columns[feature.fqfn] = list(invalid_output_cols)
        if features_with_invalid_output_columns:
            error_msg = f"Following features have invalid output columns. \n You can check for each feature his implementation for get_invalid_output_columns(). \n {json.dumps(features_with_invalid_output_columns, indent=4)}"
            if self.fail_on_features_validation:
                raise RuntimeError(error_msg)
            else:
                print(f"WARNING: {error_msg}")

        return agg_df

    def _build_params_map(self, config):
        params_map = dict()
        global_feature_params = config.get('global_features_params') or {}
        global_feature_params['monthly_features_look_back_in_months'] = config.get('monthly_features_look_back_in_months')
        global_feature_params['daily_weekly_features_look_back_in_days'] = config.get('daily_weekly_features_look_back_in_days')
        for feature in self.features:
            feature_params = global_feature_params.copy()
            features_loading_config = config.get('requested_features')
            feature_config = features_loading_config[feature.identifier][format_feature_version(feature.version)]
            config_feature_params = feature_config.get('params', {})
            feature_params.update(config_feature_params)
            params_map[feature.identifier] = feature_params
        return params_map

    def _validate_required_params_exist(self):
        features_missing_params = {}
        for feature in self.features:
            missing_params = feature.required_params - set(self.params_map[feature.identifier].keys())
            if missing_params:
                features_missing_params[feature.fqfn] = list(missing_params)
        if features_missing_params:
            raise ValueError(f"Following features have missing required params. \n {json.dumps(features_missing_params, indent=4)}")

    def _validate_features(self):
        if len(self.group_by_keys) > 1:
            raise ValueError(f"Currently only 1 set of group by keys is supported, {len(self.group_by_keys)} were defined: {self.group_by_keys}")
        self._validate_columns_for_features_exist()
        # self._validate_input_df_columns_are_not_overwritten()
        for stage in self.features_cols_by_stages:
            self._validate_no_different_impl_for_same_col_name(self.features_cols_by_stages[stage]["feature_columns"])
            self._validate_no_different_col_name_for_same_impl(self.features_cols_by_stages[stage]["feature_columns"])

    def _validate_columns_for_features_exist(self):
        missing_columns = dict()
        for feature in self.features:
            missing_columns[feature] = feature.required_columns.difference(set(self.df.columns))
        missing_columns = {feature.identifier: columns for feature, columns in missing_columns.items() if columns}
        if missing_columns:
            raise ValueError(
                f'following requested features have required columns that are missing from the df, {missing_columns}')

    def _validate_input_df_columns_are_not_overwritten(self):
        for feature_column in self.features_cols_by_stages["pre_aggs"]["feature_columns"]:
            if feature_column.col_name in self.df.columns:
                raise ValueError(
                    f"Overwriting input data frame columns is disallowed. feature '{feature_column.feature_identifier}' is overwriting column '{feature_column.col_name}'")

    @staticmethod
    def _validate_no_different_impl_for_same_col_name(features_columns):
        existing_columns = dict()
        for current_feature_column in features_columns:
            if current_feature_column.col_name not in existing_columns:
                existing_columns[current_feature_column.col_name] = current_feature_column
            else:
                existing_col = existing_columns[current_feature_column.col_name]
                if str(current_feature_column.col) != str(existing_col.col):
                    raise ValueError(
                        f'2 features ({[existing_col.feature_identifier, current_feature_column.feature_identifier]}) '
                        f'have different implementation for same column {existing_col.col_name}.'
                        f'The implementations are {[existing_col.col, current_feature_column.col]}')

    @staticmethod
    def _validate_no_different_col_name_for_same_impl(features_columns):
        existing_columns = dict()
        for current_feature_column in features_columns:
            col_expr_str = str(current_feature_column.col)
            if col_expr_str not in existing_columns:
                existing_columns[col_expr_str] = current_feature_column
            else:
                existing_col = existing_columns[col_expr_str]
                if current_feature_column.col_name != str(existing_col.col_name):
                    raise ValueError(
                        f'2 features ({[existing_col.feature_identifier, current_feature_column.feature_identifier]}) '
                        f'have same implementation for different columns {[existing_col.col_name, current_feature_column.col_name]}.'
                        f'The implementation is {existing_col.col}.')

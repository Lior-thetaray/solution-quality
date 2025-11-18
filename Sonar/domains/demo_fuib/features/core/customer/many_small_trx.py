from typing import List, Set, Dict
from pyspark.sql import DataFrame, Window, functions as f, Column

from common.libs.feature_engineering import AggFeature, FeatureDescriptor
from common.libs.zscore import enrich_with_z_score

import typing
from collections import OrderedDict

from thetaray.api.solution import DataSet, DataType, Field, IngestionMode, BusinessType
from thetaray.api.solution.explainability import (
    Explainability,
    ExplainabilityType,
    ExplainabilityValueType,
    ExplainabilityValueProperties,
    ExplainabilityValuesFilter,
    ExplainabilityValuesFilterType,
    TimeRangeUnit,
)

class ManySmallTrx(AggFeature, FeatureDescriptor):
    """
    params required:
        "min_trx_amount" : minimal single transaction amount to be considered as structuring
        "max_trx_amount" : maximum single transaction amount to be considered as structuring
        "ndays": number of days to compute the similar amounts
        "similar_amounts_thr": % of maximum possible deviations in trx amounts to be considered similar
        ""
    """
    @property
    def identifier(self) -> str:
        return 'many_small_trx'

    @property
    def version(self) -> int:
        return 1

    @property
    def description(self) -> str:
        return 'Unusual maximum number of transactions in similar amounts within a short period of time'

    @property
    def required_columns(self) -> typing.Set[str]:
        return {'customer_id', 'delivery_timestamp', 'month_offset', 'trx_amount'}

    @property
    def required_params(self) -> typing.Set[str]:
        return {'min_trx_amount', 'max_trx_amount', 'ndays', 'similar_amounts_thr'}

    @property
    def group_by_keys(self) -> typing.List[str]:
        return ['customer_id', 'month_offset']

    def pre_aggs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = collections.OrderedDict()
        columns['day_offset'] = f.datediff(f.col('delivery_timestamp'), f.lit(Constants.BEGINNING_OF_TIME))
        # define a window for calculating the percentage difference in amounts
        amount_window_spec = Window.partitionBy('customer_id').orderBy('trx_amount')
        # find similar amounts
        difference_between_amounts = f.abs(f.col('trx_amount') - f.lag(f.col('trx_amount')).over(amount_window_spec))/\
                                ((f.lag(f.col('trx_amount')).over(amount_window_spec)+f.col('trx_amount'))/2)*100
        columns['amount_difference'] = f.when(f.abs(f.col('day_offset')-f.lag(f.col('day_offset')).over(amount_window_spec))<=params['ndays'], difference_between_amounts)
        columns['small_amount_difference'] = f.when((f.col('trx_amount')>=params['min_trx_amount'])&\
                                                    (f.col('trx_amount')<=params['max_trx_amount'])&\
                                                    (f.col('amount_difference')<=params['similar_amounts_thr']),
                                                     f.col('amount_difference'))
        # add amount difference for the first trx in a chain
        columns['small_amount_difference_all'] = f.when((f.col('small_amount_difference').isNull())&\
                                                    (f.lead(f.col('small_amount_difference')).over(amount_window_spec)<=params['similar_amounts_thr']),
                                                     f.lead(f.col('small_amount_difference')).over(amount_window_spec)).otherwise(f.col('small_amount_difference'))
        time_window_spec = Window.partitionBy('customer_id', 'month_offset')
        # if we get n_small_trxs_ndays = 1, the others were longer than n days before
        cnt_small_trxs = f.count('small_amount_difference_all').over(time_window_spec).cast('float')
        columns['n_small_trxs_ndays'] = f.when(cnt_small_trxs==1., f.lit(0.)).otherwise(cnt_small_trxs.cast('float'))
        return columns

    def get_agg_exprs(self, params: dict) -> typing.OrderedDict[str, Column]:
        columns = collections.OrderedDict()
        columns[self.identifier] = f.max(f.col('n_small_trxs_ndays')).cast('double')
        return columns

    @property
    def output_fields(self) -> typing.Set[Field]:
        return {Field(identifier=self.identifier, display_name='Structuring', description=self.description, data_type=DataType.DOUBLE, category='Transactional Activity')}
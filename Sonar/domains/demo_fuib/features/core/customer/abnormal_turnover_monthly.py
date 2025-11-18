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


class Turnover(AggFeature, FeatureDescriptor):

    @property
    def identifier(self) -> str:
        return "abnormal_turnover_monthly"

    @property
    def version(self) -> int:
        return 1

    @property
    def description(self) -> str:
        return 'Unusual value of incoming/outgoing Zelle transactions compared to the customer historical behavior in the last 12 months'

    @property
    def required_columns(self) -> Set[str]:
        return {'customer_id', 'month_offset', 'amount_usd', 'method', 'direction'}

    @property
    def group_by_keys(self) -> List[str]:
        return ['customer_id', 'month_offset']

    def pre_aggs(self, params: dict) -> typing.OrderedDict[str, Column]:
        cols = OrderedDict()
        cols["amount_abs_usd"] = f.abs(f.col("amount_usd"))
        cols["amount_withdrawal_usd"] = f.when(f.col("method") == "cash_withdrawal", f.col("amount_usd")).otherwise(f.lit(0.0))
        cols["amount_revenue_usd"] = f.when(f.col("method") == "wire_in", f.col("amount_usd")).otherwise(f.lit(0.0))
        return cols

    def get_agg_exprs(self, params: dict) -> typing.OrderedDict[str, Column]:
        cols = OrderedDict()
        cols["turnover_usd"] = f.round(f.sum(f.col("amount_abs_usd")), 2)
        cols["cashwd_usd"]   = f.round(f.sum(f.col("amount_withdrawal_usd")), 2)
        cols["revenue_usd"]  = f.round(f.sum(f.col("amount_revenue_usd")), 2)
        cols["txn_count"]    = f.count(f.lit(1))  # optional diagnostic
        return cols

    # ---------- Post-aggregation: build the single anomaly score ----------
    def post_aggs(self, params: dict) -> typing.OrderedDict[str, Column]:
        cols = OrderedDict()

        # trailing look-back in months (EXCLUDING current month)
        # your framework used 'monthly_features_look_back_in_months' with rangeBetween
        # lookback = int(params.get("monthly_features_look_back_in_months", 6))
        # Order by month_offset; use rangeBetween to reference *values* not row counts
        w_hist = Window.partitionBy("customer_id").orderBy("month_offset").rangeBetween(-6, -1)   # past N months only)

        EPS = f.lit(1e-6)

        # --- Components this month ---
        turnover_cur = f.col("turnover_usd")
        ratio_wr_cur = f.col("cashwd_usd") / (f.col("revenue_usd") + EPS)  # withdrawals-to-revenue

        # --- Historical means/stddevs over trailing window (same definitions) ---
        mean_turnover = f.avg(f.col("turnover_usd")).over(w_hist)
        std_turnover  = f.stddev_samp(f.col("turnover_usd")).over(w_hist)

        mean_ratio_wr = f.avg((f.col("cashwd_usd") / (f.col("revenue_usd") + EPS))).over(w_hist)
        std_ratio_wr  = f.stddev_samp((f.col("cashwd_usd") / (f.col("revenue_usd") + EPS))).over(w_hist)

        # --- Z-scores (coalesce std to EPS; missing history → 0) ---
        z_turnover = f.when(
            mean_turnover.isNotNull(),
            (turnover_cur - mean_turnover) / (f.coalesce(std_turnover, EPS) + EPS)
        ).otherwise(f.lit(0.0))

        z_ratio_wr = f.when(
            mean_ratio_wr.isNotNull(),
            (ratio_wr_cur - mean_ratio_wr) / (f.coalesce(std_ratio_wr, EPS) + EPS)
        ).otherwise(f.lit(0.0))

        # --- Single composite score (weights are tunable) ---
        cols[self.identifier] = f.round(0.6 * z_turnover + 0.4 * z_ratio_wr, 4)

        return cols

    @property
    def output_fields(self) -> Set[Field]:
        return {Field(identifier=self.identifier,
                      display_name='Turnover',
                      data_type=DataType.DOUBLE, 
                      description="Turnover",
                      category="Transactional")}
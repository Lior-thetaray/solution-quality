# -*- coding: utf-8 -*-
"""
Proportional injector: adds strong anomalies in the LAST month only,
scaled per-customer relative to their own recent baseline.

Patterns covered:
1) high monthly transactional value
2) high monthly transactional value to high risk jurisdictions
3) high monthly transactional volume (txn count)
4) high single transactional value in the month
5) high transactional value in a 3-day window
6) high number of counterparties
7) high transactional concentration to a single counterparty
8) similar high credit and debit values in a 3-day window (fast in/out)

Assumptions: input df has the schema produced by your generator.
"""

from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime, timedelta
import random, string
import numpy as np

from pyspark.sql import DataFrame, Row, SparkSession
from pyspark.sql import functions as F
from pyspark.sql import Window as W

HIGH_RISK_DEST = {"TR", "CY", "AE"}
FX_RATES_TO_USD = {"UAH": 0.027, "USD": 1.00, "EUR": 1.10}
CURRENCIES = ["UAH", "USD", "EUR"]

def _rand_id(prefix: str, n: int = 10) -> str:
    s = "".join(random.choices(string.ascii_uppercase + string.digits, k=n))
    return f"{prefix}_{s}"

def _to_py(x):
    import numpy as _np
    return x.item() if isinstance(x, _np.generic) else x

def _month_bounds(end_date_iso: str) -> Tuple[datetime, datetime]:
    end = datetime.fromisoformat(end_date_iso)
    last_start = end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_eod = end.replace(hour=23, minute=59, second=59, microsecond=0)
    return last_start, end_eod

def _pick_currency_for_usd_target(usd_target: float) -> Tuple[str, float]:
    currency = random.choices(CURRENCIES, weights=[0.2, 0.7, 0.1], k=1)[0]
    if currency == "USD":
        return "USD", float(round(usd_target, 2))
    rate = FX_RATES_TO_USD.get(currency, 1.0)
    return currency, float(round(usd_target / rate, 2))

def _usd(amount: float, currency: str) -> float:
    return float(round(amount * FX_RATES_TO_USD.get(currency, 1.0), 2))

def _sample_times(start_dt: datetime, end_dt: datetime, n: int) -> List[datetime]:
    span = int((end_dt - start_dt).total_seconds())
    offs = sorted(np.random.randint(0, max(1, span + 1), size=n).tolist())
    return [start_dt + timedelta(seconds=int(o)) for o in offs]

def _pick_3day_window(last_start: datetime, last_end: datetime) -> Tuple[datetime, datetime]:
    latest_start = last_end - timedelta(days=3)
    if latest_start <= last_start:
        s = last_start
    else:
        span = int((latest_start - last_start).total_seconds())
        off = int(np.random.randint(0, span + 1))
        s = last_start + timedelta(seconds=off)
    return s, s + timedelta(days=3)

def _build_row(c: Dict[str, Any], ts: datetime, *, method: str, direction: str,
               usd_amount: float, purpose: str = "services",
               cp_id: Optional[str] = None, cp_name: Optional[str] = None,
               cp_addr: Optional[str] = None, cp_ip: Optional[str] = None,
               cp_jur: Optional[str] = None, cross_border: bool = False,
               known_shell: bool = False, same_cp: bool = False) -> Row:
    currency, amount = _pick_currency_for_usd_target(usd_amount)
    return Row(**{
        "txn_id": _rand_id("T", 12),
        "txn_ts": ts,
        "customer_id": c["customer_id"],
        "account_id": c["account_id"],
        # KYC snapshot
        "customer_type": c.get("customer_type"),
        "customer_name": c.get("customer_name"),
        "date_of_birth": c.get("date_of_birth"),
        "address_full": c.get("address_full"),
        "occupation": c.get("occupation"),
        "pep_indicator": bool(c.get("pep_indicator", False)),
        "industry_code": c.get("industry_code"),
        "account_open_months": None,
        "whitelist_flag": bool(c.get("whitelist_flag", False)),
        # Txn
        "direction": direction,
        "method": method,
        "amount": float(amount),
        "currency": currency,
        "amount_usd": float(_usd(amount, currency)),
        "purpose_code": purpose,
        "cross_border_flag": bool(cross_border),
        "declared_counterparty_name": cp_name,
        "balance_after_txn": 0.0,
        "is_split_component": False,
        # Counterparty
        "cp_id": cp_id or (_rand_id("CP", 8) if not same_cp else "CP_ANCHOR"),
        "cp_type": "external_legal_entity",
        "cp_jurisdiction": cp_jur,
        "cp_known_shell_flag": bool(known_shell),
        "cp_is_bank_customer": False,
        "counterparty_name": cp_name,
        "counterparty_address": cp_addr,
        "counterparty_ip": cp_ip,
        # Endpoint
        "endpoint_type": "online_banking",
        "ip_hash": f"IP_{_rand_id('', 6)[1:]}",
        "device_id_hash": f"DEV_{_rand_id('', 6)[1:]}",
        "geo_lat": None, "geo_lon": None, "atm_id": None,
        "withdrawal_channel": None, "pos_terminal_id": None,
        # Linkage
        "rep_id_hash": c.get("rep_id_hash"),
        "address_hash": c.get("address_hash"),
        "website_hash": c.get("website_hash"),
        # Annotations
        "scenario_type": "injected_last_month_prop",
        "scenario_role": "injector",
        "anomaly_flag": True,
    })

def inject_last_month_anomalies_proportional(
    spark: SparkSession,
    df: DataFrame,
    end_date: str,
    *,
    frac_customers: Dict[str, float],
    multipliers: Dict[str, float],
    seed: Optional[int] = 1234
) -> DataFrame:

    if seed is not None:
        random.seed(seed); np.random.seed(seed)

    schema = df.schema
    last_start, last_end = _month_bounds(end_date)

    # Active customers in last month (candidate pool)
    last_month_df = df.where((F.col("txn_ts") >= F.lit(last_start)) & (F.col("txn_ts") <= F.lit(last_end)))
    active_last = (
        last_month_df
        .select("customer_id","account_id","customer_type","customer_name",
                "date_of_birth","address_full","occupation","pep_indicator",
                "industry_code","whitelist_flag","rep_id_hash","address_hash","website_hash")
        .dropDuplicates(["customer_id","account_id"])
    )
    n_active = active_last.count()

    # Baseline window = previous 3 months
    prev3_start = (last_start - F.expr("INTERVAL 3 MONTH")).cast("timestamp")
    # Compute baseline stats per customer over prev3 months
    prev3 = df.where((F.col("txn_ts") >= prev3_start) & (F.col("txn_ts") < F.lit(last_start)))
    prev3_agg = (
        prev3.groupBy("customer_id")
             .agg(
                 F.sum(F.abs(F.col("amount_usd"))).alias("base_turnover_usd"),
                 F.count("*").alias("base_txn_count"),
                 F.max(F.abs(F.col("amount_usd"))).alias("base_max_single_usd"),
                 F.countDistinct(F.col("cp_id")).alias("base_distinct_cp"),
                 F.sum(F.when(F.col("cp_jurisdiction").isin(list(HIGH_RISK_DEST)), F.abs(F.col("amount_usd"))).otherwise(0.0)).alias("base_turnover_hr_usd")
             )
    )

    # Current last-month stats per customer
    last_agg = (
        last_month_df.groupBy("customer_id")
        .agg(
            F.sum(F.abs(F.col("amount_usd"))).alias("cur_turnover_usd"),
            F.count("*").alias("cur_txn_count"),
            F.max(F.abs(F.col("amount_usd"))).alias("cur_max_single_usd"),
            F.countDistinct(F.col("cp_id")).alias("cur_distinct_cp"),
            F.sum(F.when(F.col("cp_jurisdiction").isin(list(HIGH_RISK_DEST)), F.abs(F.col("amount_usd"))).otherwise(0.0)).alias("cur_turnover_hr_usd")
        )
    )

    stats = (
        active_last.join(last_agg, "customer_id", "left")
                   .join(prev3_agg, "customer_id", "left")
                   .fillna({"cur_turnover_usd":0.0,"cur_txn_count":0,"cur_max_single_usd":0.0,"cur_distinct_cp":0,
                            "base_turnover_usd":0.0,"base_txn_count":0,"base_max_single_usd":0.0,"base_distinct_cp":0,
                            "cur_turnover_hr_usd":0.0,"base_turnover_hr_usd":0.0})
    )

    # Collect candidate dicts (keep reasonable size by sampling)
    candidates = stats.collect()
    random.shuffle(candidates)

    def pick_fraction(tag: str) -> List[Dict[str, Any]]:
        k = max(1, int(frac_customers.get(tag, 0.0) * n_active))
        pool = random.sample(candidates, k=min(k, len(candidates)))
        return [r.asDict(recursive=True) for r in pool]

    new_rows: List[Row] = []

    # 1) High monthly transactional value: make cur_turnover reach multiplier*baseline
    for c in pick_fraction("high_monthly_value"):
        base = float(c.get("base_turnover_usd", 0.0))/max(1, 3)  # average per month
        target = max(30_000.0, multipliers.get("turnover",3.0) * base)
        delta = max(0.0, target - float(c.get("cur_turnover_usd",0.0)))
        if delta <= 0: continue
        n = int(np.random.randint(5, 9))
        parts = (np.random.dirichlet(np.ones(n)) * delta).tolist()
        times = _sample_times(last_start, last_end, n)
        for a, t in zip(parts, times):
            new_rows.append(_build_row(c, t, method="wire_out", direction="debit", usd_amount=float(a), purpose="invoice"))

    # 2) High monthly value to high-risk jurisdictions
    for c in pick_fraction("high_monthly_value_hr"):
        base = float(c.get("base_turnover_hr_usd", 0.0))/max(1, 3)
        target = max(20_000.0, multipliers.get("turnover_hr",2.5) * base)
        delta = max(0.0, target - float(c.get("cur_turnover_hr_usd",0.0)))
        if delta <= 0: continue
        n = int(np.random.randint(4, 8))
        parts = (np.random.dirichlet(np.ones(n)) * delta).tolist()
        times = _sample_times(last_start, last_end, n)
        for a, t in zip(parts, times):
            new_rows.append(_build_row(c, t, method="wire_out", direction="debit", usd_amount=float(a),
                                       purpose="services", cp_jur=random.choice(list(HIGH_RISK_DEST)),
                                       cross_border=True, known_shell=(random.random()<0.3)))

    # 3) High monthly volume (txn count): add small e-com debits to reach 3× baseline count
    for c in pick_fraction("high_monthly_volume"):
        base_cnt = float(c.get("base_txn_count", 0.0))/max(1, 3)
        target_cnt = int(max(30, multipliers.get("volume",3.0) * base_cnt))
        cur_cnt = int(c.get("cur_txn_count", 0))
        need = max(0, target_cnt - cur_cnt)
        if need <= 0: continue
        times = _sample_times(last_start, last_end, need)
        for t in times:
            amt = float(np.random.lognormal(mean=3.0, sigma=0.4))  # tens of USD
            new_rows.append(_build_row(c, t, method="card_ecom", direction="debit", usd_amount=amt, purpose="small_purchase"))

    # 4) High single transaction value: ensure one txn ≥ multiplier × baseline max
    for c in pick_fraction("high_single_txn"):
        base_max = float(c.get("base_max_single_usd", 0.0))
        target = max(20_000.0, multipliers.get("single_txn",3.0) * base_max)
        cur_max = float(c.get("cur_max_single_usd", 0.0))
        if cur_max >= target: continue
        t = random.choice(_sample_times(last_start, last_end, 1))
        new_rows.append(_build_row(c, t, method="wire_out", direction="debit", usd_amount=target, purpose="one_off_capital"))

    # 5) High value in a 3-day window: create cluster to reach multiplier × (baseline monthly avg)
    for c in pick_fraction("high_value_3d"):
        base = float(c.get("base_turnover_usd", 0.0))/max(1, 3)
        target_cluster = max(25_000.0, multipliers.get("value_3d",2.5) * base)
        s, e = _pick_3day_window(last_start, last_end)
        n = int(np.random.randint(5, 9))
        parts = (np.random.dirichlet(np.ones(n)) * target_cluster).tolist()
        times = _sample_times(s, e, n)
        for a, t in zip(parts, times):
            new_rows.append(_build_row(c, t, method="wire_out", direction="debit", usd_amount=float(a), purpose="clustered_payouts"))

    # 6) Many counterparties: reach 3× baseline distinct_cp by sending to fresh cps
    for c in pick_fraction("many_counterparties"):
        base_k = float(c.get("base_distinct_cp", 0.0))/max(1, 3)
        target_k = int(max(10, multipliers.get("distinct_cp",3.0) * base_k))
        cur_k = int(c.get("cur_distinct_cp", 0))
        need_k = max(0, target_k - cur_k)
        if need_k <= 0: continue
        # one txn per new cp
        times = _sample_times(last_start, last_end, need_k)
        for t in times:
            amt = float(np.random.lognormal(9.5, 0.4)/1000)  # few hundreds–thousands
            new_rows.append(_build_row(c, t, method="wire_out", direction="debit", usd_amount=amt,
                                       purpose="supplier", cp_id=_rand_id("CP", 8)))

    # 7) Concentration to a single counterparty: make top_cp_share ≈ target
    for c in pick_fraction("concentration_one_cp"):
        target_share = float(multipliers.get("concentration_share", 0.85))
        base = float(c.get("base_turnover_usd", 0.0))/max(1, 3)
        # Put a chunk to one CP so that share is dominated
        anchor = _rand_id("CP", 8)
        chunk = max(20_000.0, 0.8 * target_share * base)
        n = int(np.random.randint(25, 45))
        times = _sample_times(last_start, last_end, n)
        for i, t in enumerate(times):
            usd_amt = (chunk / n) * float(np.random.uniform(0.8, 1.2))
            new_rows.append(_build_row(c, t, method="wire_out", direction="debit",
                                       usd_amount=usd_amt, purpose="services",
                                       cp_id=anchor, same_cp=True))

    # 8) Fast in / fast out in 3-day window: credit in, then debits within ±5%
    for c in pick_fraction("fast_in_fast_out"):
        base = float(c.get("base_turnover_usd", 0.0))/max(1, 3)
        s, e = _pick_3day_window(last_start, last_end)
        t_in = random.choice(_sample_times(s, e - timedelta(hours=24), 1))
        base_in = max(25_000.0, 0.6 * base)
        # credit in
        new_rows.append(_build_row(c, t_in, method="wire_in", direction="credit",
                                   usd_amount=base_in, purpose="unexpected_inflow",
                                   cp_id=_rand_id("CP", 8)))
        # one or two debits out within 6–48 hours totaling ≈ base_in (±5%)
        k = int(np.random.randint(1, 3))
        out_total = base_in * float(np.random.uniform(0.95, 1.05))
        weights = np.random.dirichlet(np.ones(k))
        for j in range(k):
            t_out = t_in + timedelta(hours=int(np.random.randint(6, 48)))
            new_rows.append(_build_row(c, t_out, method="wire_out", direction="debit",
                                       usd_amount=float(out_total * weights[j]), purpose="rapid_outflow",
                                       cp_id=_rand_id("CP", 8)))

    if not new_rows:
        return df

    injected_df = spark.createDataFrame(
        [Row(**{k: _to_py(v) for k, v in r.asDict().items()}) for r in new_rows],
        schema=schema
    )
    return df.unionByName(injected_df)

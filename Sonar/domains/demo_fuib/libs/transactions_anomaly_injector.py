# -*- coding: utf-8 -*-
"""
Injector of strong anomalous behaviors in the *last month* of a generated period.

It adds rows to an existing transactions DataFrame (same schema as your generator):
- high monthly transactional value
- high monthly value to high-risk jurisdictions
- high monthly transaction volume
- high single transaction value in the month
- high value in a 3-day window
- high number of counterparties
- high concentration to a single counterparty
- similar high credit and debit values in a 3-day window (“money-in, money-out”)

Safe for Spark pickling: uses pure Python scalars.
"""

from datetime import datetime, timedelta
import random
import string
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
from pyspark.sql import Row, DataFrame, SparkSession
from pyspark.sql import functions as F

# ---- If you have these constants in your generator, keep them in sync ----
HIGH_RISK_DEST = {"TR", "CY", "AE"}
FX_RATES_TO_USD = {"UAH": 0.027, "USD": 1.00, "EUR": 1.10}
CURRENCIES = ["UAH", "USD", "EUR"]

# ----------------- Utilities (copied from generator style) -----------------
def _rand_id(prefix: str, n: int = 10) -> str:
    s = "".join(random.choices(string.ascii_uppercase + string.digits, k=n))
    return f"{prefix}_{s}"

def _to_py(x):
    if isinstance(x, np.generic):
        return x.item()
    return x

def _month_bounds(end_date_iso: str) -> Tuple[datetime, datetime]:
    """Return (start_of_last_month, end_of_period) given an inclusive end_date (YYYY-MM-DD)."""
    end = datetime.fromisoformat(end_date_iso)
    last_month_start = end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return last_month_start, end.replace(hour=23, minute=59, second=59, microsecond=0)

def _usd(amount: float, currency: str) -> float:
    return float(round(amount * FX_RATES_TO_USD.get(currency, 1.0), 2))

def _pick_currency_for_usd_target(usd_target: float) -> Tuple[str, float]:
    """Return (currency, amount_in_currency) such that amount_usd ~= usd_target."""
    # Bias to USD to avoid FX noise for “exact” targets
    currency = random.choices(CURRENCIES, weights=[0.2, 0.7, 0.1], k=1)[0]
    if currency == "USD":
        return "USD", float(round(usd_target, 2))
    rate = FX_RATES_TO_USD.get(currency, 1.0)
    return currency, float(round(usd_target / rate, 2))

def _sample_times_in_window(start_dt: datetime, end_dt: datetime, n: int) -> List[datetime]:
    span = int((end_dt - start_dt).total_seconds())
    offs = sorted(np.random.randint(0, max(1, span + 1), size=n).tolist())
    return [start_dt + timedelta(seconds=int(o)) for o in offs]

# ----------------- Core injector -----------------
def inject_last_month_anomalies(
    spark: SparkSession,
    df: DataFrame,
    end_date: str,
    *,
    per_pattern_n_customers: int = 20,
    usd_scale: float = 1.0,
    high_value_month_usd: float = 150_000.0,
    high_value_month_hr_juris_usd: float = 100_000.0,
    high_single_txn_usd: float = 85_000.0,
    three_day_window_usd: float = 120_000.0,
    many_txn_count: int = 120,
    many_counterparties_count: int = 60,
    concentration_txn_count: int = 40,
    seed: Optional[int] = 1234,
) -> DataFrame:
    """
    Adds anomalous rows restricted to the *last month* in [.., end_date].
    Returns: df union injected_rows_df (same schema).
    """

    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    # Infer schema from existing df (assumes the generator's schema)
    schema = df.schema

    # Determine last-month bounds
    last_start, last_end = _month_bounds(end_date)

    # choose candidate customers that are active in last month (or just any)
    cids = (
        df.where((F.col("txn_ts") >= F.lit(last_start)) & (F.col("txn_ts") <= F.lit(last_end)))
          .select("customer_id", "account_id", "customer_type", "customer_name",
                  "date_of_birth", "address_full", "occupation", "pep_indicator",
                  "industry_code", "whitelist_flag", "rep_id_hash", "address_hash", "website_hash")
          .dropDuplicates(["customer_id", "account_id"])
          .limit(per_pattern_n_customers * 10)  # buffer pool
          .collect()
    )
    if not cids:
        # fallback: sample from full df if last month has no rows
        cids = (
            df.select("customer_id", "account_id", "customer_type", "customer_name",
                      "date_of_birth", "address_full", "occupation", "pep_indicator",
                      "industry_code", "whitelist_flag", "rep_id_hash", "address_hash", "website_hash")
              .dropDuplicates(["customer_id", "account_id"])
              .limit(per_pattern_n_customers * 10)
              .collect()
        )

    # helper to get a random customer snapshot Row-like dict
    base_customers = [r.asDict(recursive=True) for r in cids]
    random.shuffle(base_customers)

    def take(n: int) -> List[Dict[str, Any]]:
        out = base_customers[:n] if len(base_customers) >= n else random.sample(base_customers, k=n)
        # rotate pool
        del base_customers[:min(n, len(base_customers))]
        return out

    new_rows: List[Row] = []

    # ------------- Pattern builders (each returns list of Row) -------------
    def build_row(c: Dict[str, Any], ts: datetime, *, method: str, direction: str,
                  usd_amount: float, purpose: str = "services", cp_id: Optional[str] = None,
                  cp_name: Optional[str] = None, cp_addr: Optional[str] = None,
                  cp_ip: Optional[str] = None, cp_jur: Optional[str] = None,
                  cross_border: bool = False, known_shell: bool = False,
                  same_cp: bool = False) -> Row:
        currency, amount = _pick_currency_for_usd_target(usd_scale * usd_amount)
        balance_after = 0.0  # leave as 0; or omit if not used downstream
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
            "account_open_months": None,  # optional; compute upstream if needed
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
            "balance_after_txn": float(balance_after),
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
            "scenario_type": "injected_last_month",
            "scenario_role": "injector",
            "anomaly_flag": True,
        })

    # ---- Windows for 3-day clusters inside last month
    def pick_3day_window() -> Tuple[datetime, datetime]:
        # choose a start between last_start and last_end - 3 days
        latest_start = last_end - timedelta(days=3)
        if latest_start <= last_start:
            s = last_start
        else:
            span = int((latest_start - last_start).total_seconds())
            off = int(np.random.randint(0, span + 1))
            s = last_start + timedelta(seconds=off)
        return s, s + timedelta(days=3)

    # 1) High monthly transactional value (big total in month)
    for c in take(per_pattern_n_customers):
        # break the target into ~6–10 large wires
        n = int(np.random.randint(6, 10))
        amounts = np.random.dirichlet(np.ones(n)) * high_value_month_usd
        times = _sample_times_in_window(last_start, last_end, n)
        for a, t in zip(amounts, times):
            new_rows.append(build_row(c, t, method="wire_out", direction="debit",
                                      usd_amount=float(a), purpose="invoice"))

    # 2) High monthly value to high-risk jurisdictions
    for c in take(per_pattern_n_customers):
        n = int(np.random.randint(4, 8))
        amounts = np.random.dirichlet(np.ones(n)) * high_value_month_hr_juris_usd
        times = _sample_times_in_window(last_start, last_end, n)
        for a, t in zip(amounts, times):
            new_rows.append(build_row(c, t, method="wire_out", direction="debit",
                                      usd_amount=float(a), purpose="services",
                                      cp_jur=random.choice(list(HIGH_RISK_DEST)),
                                      cross_border=True, known_shell=random.random()<0.3))

    # 3) High monthly transactional volume (many small txns)
    for c in take(per_pattern_n_customers):
        n = int(many_txn_count)
        times = _sample_times_in_window(last_start, last_end, n)
        for t in times:
            usd_amt = float(np.random.lognormal(mean=3.0, sigma=0.4))  # ~ $20–$100 typical
            new_rows.append(build_row(c, t, method="card_ecom", direction="debit",
                                      usd_amount=usd_amt, purpose="small_purchase"))

    # 4) High single transactional value in the month
    for c in take(per_pattern_n_customers):
        t = random.choice(_sample_times_in_window(last_start, last_end, 1))
        new_rows.append(build_row(c, t, method="wire_out", direction="debit",
                                  usd_amount=float(high_single_txn_usd), purpose="one_off_capital"))

    # 5) High transactional value in a 3-day window
    for c in take(per_pattern_n_customers):
        s, e = pick_3day_window()
        n = int(np.random.randint(5, 9))
        amounts = np.random.dirichlet(np.ones(n)) * three_day_window_usd
        times = _sample_times_in_window(s, e, n)
        for a, t in zip(amounts, times):
            new_rows.append(build_row(c, t, method="wire_out", direction="debit",
                                      usd_amount=float(a), purpose="clustered_payouts"))

    # 6) High number of counterparties (unique cp_id’s)
    for c in take(per_pattern_n_customers):
        n = int(many_counterparties_count)
        times = _sample_times_in_window(last_start, last_end, n)
        for t in times:
            new_rows.append(build_row(c, t, method="wire_out", direction="debit",
                                      usd_amount=float(np.random.lognormal(9.5, 0.4)/1000),  # ~ few hundreds–thousands
                                      purpose="supplier", cp_id=_rand_id("CP", 8)))

    # 7) High concentration to a single counterparty
    for c in take(per_pattern_n_customers):
        anchor_cp = _rand_id("CP", 8)
        n = int(concentration_txn_count)
        times = _sample_times_in_window(last_start, last_end, n)
        for t in times:
            usd_amt = float(np.random.lognormal(10.0, 0.3)/500)  # mid-size wires
            new_rows.append(build_row(c, t, method="wire_out", direction="debit",
                                      usd_amount=usd_amt, purpose="services",
                                      cp_id=anchor_cp, same_cp=True))

    # 8) Similar high credit and debit in a 3-day window (in-fast-out)
    for c in take(per_pattern_n_customers):
        s, e = pick_3day_window()
        t_in = random.choice(_sample_times_in_window(s, e - timedelta(hours=24), 1))
        base = float(np.random.uniform(60_000, 120_000))
        # credit in
        new_rows.append(build_row(c, t_in, method="wire_in", direction="credit",
                                  usd_amount=base, purpose="unexpected_inflow",
                                  cp_id=_rand_id("CP", 8)))
        # debit out within 24–48h, within ±5%
        k = int(np.random.randint(1, 3))  # 1–2 outflows
        outs = [base * float(np.random.uniform(0.95, 1.05)) for _ in range(k)]
        for i in range(k):
            t_out = t_in + timedelta(hours=int(np.random.randint(6, 48)))
            new_rows.append(build_row(c, t_out, method="wire_out", direction="debit",
                                      usd_amount=float(outs[i]), purpose="rapid_outflow",
                                      cp_id=_rand_id("CP", 8)))

    # ----------------- Create DF and union -----------------
    if not new_rows:
        return df

    injected_df = spark.createDataFrame([Row(**{k: _to_py(v) for k, v in r.asDict().items()}) for r in new_rows], schema=schema)
    return df.unionByName(injected_df)

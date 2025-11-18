# -*- coding: utf-8 -*-
"""
PySpark single-table synthetic transactional data generator with KYC, amount_usd,
and identity-overlap fields (customer_name, counterparty_name, counterparty_address, counterparty_ip).

Safe for older NumPy and Spark pickling:
- uses np.random.randint (not integers)
- uses random.choices (not np.random.choice)
- sanitizes values to native Python types
"""

from __future__ import annotations
import random
import string
from dataclasses import dataclass
from datetime import datetime, timedelta, date
from typing import List, Optional, Tuple, Dict, Any

import numpy as np

from pyspark.sql import Row, SparkSession
from pyspark.sql.types import (
    StructType, StructField,
    StringType, BooleanType, IntegerType, DoubleType, TimestampType, DateType
)

# -----------------------------
# Constants / palettes
# -----------------------------
CURRENCIES = ["UAH", "USD", "EUR"]
COUNTRIES = ["UA", "PL", "TR", "CY", "AE", "GB", "DE", "US", "LT"]
HIGH_RISK_DEST = {"TR", "CY", "AE"}
INDUSTRIES = ["it_services", "marketing", "consulting", "retail", "wholesale", "logistics", "construction"]
OCCUPATIONS = ["accountant", "developer", "designer", "marketer", "consultant", "shop_owner", "driver"]
METHODS = ["p2p", "wire_in", "wire_out", "card_pos", "card_ecom", "cash_withdrawal", "cash_deposit", "internal_transfer"]
ENDPOINTS = ["online_banking", "mobile_app", "pos", "atm", "branch"]
CP_TYPES = ["customer", "external_individual", "external_legal_entity", "merchant", "atm_owner", "foreign_bank"]

STRUCTURING_AMOUNTS = [19990, 199900, 499900, 99990, 149900]
SERVICE_PURPOSES = ["marketing services", "IT services", "consulting services", "contractor payment"]
RETAIL_PURPOSES = ["goods purchase", "inventory", "supplier payment"]
GEN_PURPOSES   = ["salary", "rent", "utilities", "refund", "invoice", "services"]

# FX to USD
FX_RATES_TO_USD = {"UAH": 0.027, "USD": 1.00, "EUR": 1.10}

FIRST_NAMES = ["Andrii","Olena","Ihor","Yulia","Maksym","Anna","Dmytro","Oksana","Taras","Nadia"]
LAST_NAMES  = ["Shevchenko","Koval","Boyko","Tkachenko","Bondarenko","Kravchenko","Melnyk","Polishchuk","Savchenko","Lysenko"]

COMPANY_WORDS = ["Global","Prime","Vertex","Blue","Delta","Apex","Nova","Terra","Quantum","Metro"]
COMPANY_SUFFIX = ["LLC","Ltd","GmbH","Sp.z o.o.","SIA","s.r.o.","Inc."]

# -----------------------------
# Helpers (SAFE for Spark)
# -----------------------------
def rand_id(prefix: str, n: int = 10) -> str:
    s = "".join(random.choices(string.ascii_uppercase + string.digits, k=n))
    return f"{prefix}_{s}"

def rand_bool(p_true: float) -> bool:
    return bool(np.random.random() < p_true)

def pick_weighted(items, probs):
    return random.choices(items, weights=probs, k=1)[0]

def month_floor(dt: datetime) -> datetime:
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

def months_between(a: datetime, b: datetime) -> int:
    return (b.year - a.year) * 12 + (b.month - a.month)

def to_py(x: Any) -> Any:
    if isinstance(x, (np.generic,)):
        return x.item()
    return x

def make_customer_name(customer_type: str) -> str:
    if customer_type == "individual":
        return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    # FOP / legal_entity -> business-like name
    return f"{random.choice(COMPANY_WORDS)} {random.choice(COMPANY_WORDS)} {random.choice(COMPANY_SUFFIX)}"

# -----------------------------
# Customer model
# -----------------------------
@dataclass
class Customer:
    customer_id: str
    account_id: str
    customer_type: str            # individual | fop | legal_entity
    dob: Optional[date]
    address_full: str
    occupation: Optional[str]
    pep_indicator: bool
    industry_code: Optional[str]  # for fop/legal_entity
    whitelist_flag: bool
    open_date: date
    rep_id_hash: Optional[str]
    address_hash: Optional[str]
    website_hash: Optional[str]
    customer_name: str            # NEW: stable display name

def make_customers(
    n_customers: int,
    pct_fop: float = 0.25,
    pct_legal: float = 0.15,
    pep_rate: float = 0.01,
    whitelist_rate: float = 0.02,
    seed: Optional[int] = None,
) -> List[Customer]:
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    out: List[Customer] = []
    today = date.today()
    for _ in range(n_customers):
        cid = rand_id("C")
        aid = rand_id("A")
        r = np.random.random()

        if r < pct_legal:
            ctype = "legal_entity"
            dob = None
            occupation = None
            industry = random.choice(INDUSTRIES)
        elif r < pct_legal + pct_fop:
            ctype = "fop"
            age_years = int(np.clip(np.random.normal(38, 9), 20, 70))
            dob = today.replace(year=today.year - age_years)
            occupation = random.choice(OCCUPATIONS)
            industry = random.choice(INDUSTRIES)
        else:
            ctype = "individual"
            age_years = int(np.clip(np.random.normal(38, 12), 18, 85))
            dob = today.replace(year=today.year - age_years)
            occupation = random.choice(OCCUPATIONS)
            industry = None

        addr = f"{random.randint(1, 200)} Example St, City_{random.randint(1,50)}"
        pep = rand_bool(pep_rate)
        wl = rand_bool(whitelist_rate)
        open_date = today - timedelta(days=int(np.random.randint(365, 8*365)))
        rep_hash = (rand_id("REP", 6) if ctype in ("fop","legal_entity") and rand_bool(0.15) else None)
        addr_hash = (f"ADDR_{hash(addr) % 10_000}" if rand_bool(0.25) else None)
        website_hash = (f"WEB_{np.random.randint(1000,9999)}" if ctype in ("fop","legal_entity") and rand_bool(0.10) else None)
        cname = make_customer_name(ctype)

        out.append(Customer(
            customer_id=cid,
            account_id=aid,
            customer_type=ctype,
            dob=dob,
            address_full=addr,
            occupation=occupation,
            pep_indicator=pep,
            industry_code=industry,
            whitelist_flag=wl,
            open_date=open_date,
            rep_id_hash=rep_hash,
            address_hash=addr_hash,
            website_hash=website_hash,
            customer_name=cname
        ))
    return out

# -----------------------------
# Transaction synthesis
# -----------------------------
def _normal_txn_mix(customer: Customer):
    if customer.customer_type == "individual":
        methods = ["card_pos","card_ecom","p2p","cash_withdrawal","wire_out","wire_in","cash_deposit","internal_transfer"]
        probs   = [0.35,        0.20,       0.20,  0.10,            0.05,      0.04,      0.03,          0.03]
    elif customer.customer_type == "fop":
        methods = ["wire_in","wire_out","card_pos","card_ecom","cash_withdrawal","p2p","internal_transfer","cash_deposit"]
        probs   = [0.25,     0.25,      0.15,      0.10,        0.10,            0.07, 0.05,               0.03]
    else:  # legal_entity
        methods = ["wire_in","wire_out","card_pos","card_ecom","cash_withdrawal","internal_transfer","p2p","cash_deposit"]
        probs   = [0.35,     0.30,      0.08,      0.05,        0.05,            0.10,                0.04, 0.03]
    return methods, probs

def _amount_sampler(method: str, customer: Customer, anomalous: bool=False) -> float:
    if anomalous and method in ("wire_out","cash_withdrawal","p2p"):
        if rand_bool(0.35):
            base = random.choice(STRUCTURING_AMOUNTS)
            jitter = np.random.normal(0, base*0.01)
            return max(10.0, float(base + jitter))
    if method in ("card_pos","card_ecom","p2p"):
        return float(max(5, np.random.lognormal(mean=3.2, sigma=0.5)))
    if method in ("wire_in","wire_out"):
        scale = 2.5 if customer.customer_type=="individual" else 3.2
        return float(max(100, np.random.lognormal(mean=scale, sigma=0.7)))
    if method in ("cash_withdrawal","cash_deposit"):
        return float(max(50, np.random.lognormal(mean=3.3, sigma=0.6)))
    return float(max(10, np.random.lognormal(mean=3.0, sigma=0.6)))

def _purpose_sampler(customer: Customer, method: str, anomalous: bool=False) -> str:
    if anomalous and method in ("wire_out","p2p") and customer.customer_type in ("fop","legal_entity"):
        return random.choice(SERVICE_PURPOSES)
    if method in ("card_pos","card_ecom"):
        return random.choice(RETAIL_PURPOSES)
    return random.choice(GEN_PURPOSES)

def _counterparty_sampler(anomalous: bool=False) -> Dict[str, object]:
    cp_id = rand_id("CP", 8) if rand_bool(0.8) else None
    cp_type = pick_weighted(CP_TYPES, [0.20,0.30,0.25,0.15,0.03,0.07])
    cp_j = random.choice(COUNTRIES) if rand_bool(0.5) else None
    cp_shell = anomalous and rand_bool(0.25)
    cp_is_bank_customer = rand_bool(0.2)
    # default CP name/address/ip (can be overridden by overlap logic)
    cp_name = f"CP_{int(np.random.randint(10000,99999))}" if rand_bool(0.6) else None
    cp_addr = (f"{random.randint(1, 200)} Market Rd, City_{random.randint(1,50)}" if rand_bool(0.5) else None)
    cp_ip   = (f"IP_{rand_id('',6)[1:]}" if rand_bool(0.4) else None)
    return dict(cp_id=cp_id, cp_type=cp_type, cp_jurisdiction=cp_j,
                cp_known_shell_flag=cp_shell, cp_is_bank_customer=cp_is_bank_customer,
                declared_counterparty_name=cp_name,
                counterparty_address=cp_addr,
                counterparty_ip=cp_ip)

def _endpoint_sampler(method: str, anomalous: bool=False) -> Dict[str, object]:
    if method in ("card_pos","card_ecom"):
        endpoint_type = "pos" if method=="card_pos" else "mobile_app"
    elif method == "cash_withdrawal":
        endpoint_type = "atm"
    elif method == "cash_deposit":
        endpoint_type = "branch"
    else:
        endpoint_type = pick_weighted(ENDPOINTS, [0.35,0.35,0.05,0.10,0.15])
    ip_hash = rand_id("IP", 6) if endpoint_type in ("online_banking","mobile_app") and rand_bool(0.7) else None
    device_id_hash = rand_id("DEV", 6) if endpoint_type in ("online_banking","mobile_app") and rand_bool(0.6) else None
    geo_lat = float(50 + np.random.normal(0, 0.3)) if endpoint_type in ("atm","branch","pos") and rand_bool(0.5) else None
    geo_lon = float(30 + np.random.normal(0, 0.3)) if geo_lat is not None else None
    atm_id = rand_id("ATM", 5) if endpoint_type=="atm" else None
    withdrawal_channel = (pick_weighted(["onus","offus"], [0.8,0.2]) if endpoint_type=="atm" else None)
    pos_terminal_id = rand_id("POS", 6) if endpoint_type=="pos" and rand_bool(0.6) else None
    return dict(endpoint_type=endpoint_type, ip_hash=ip_hash, device_id_hash=device_id_hash,
                geo_lat=geo_lat, geo_lon=geo_lon, atm_id=atm_id,
                withdrawal_channel=withdrawal_channel, pos_terminal_id=pos_terminal_id)

def _advance_balance(balance: float, direction: str, amount: float) -> float:
    return balance + amount if direction == "credit" else balance - amount

# -----------------------------
# Schema (explicit)  — NEW columns included
# -----------------------------
SCHEMA = StructType([
    StructField("txn_id", StringType(), False),
    StructField("txn_ts", TimestampType(), False),
    StructField("customer_id", StringType(), False),
    StructField("account_id", StringType(), False),
    # KYC snapshot
    StructField("customer_type", StringType(), True),
    StructField("customer_name", StringType(), True),            # NEW
    StructField("date_of_birth", DateType(), True),
    StructField("address_full", StringType(), True),
    StructField("occupation", StringType(), True),
    StructField("pep_indicator", BooleanType(), True),
    StructField("industry_code", StringType(), True),
    StructField("account_open_months", IntegerType(), True),
    StructField("whitelist_flag", BooleanType(), True),
    # Txn
    StructField("direction", StringType(), True),
    StructField("method", StringType(), True),
    StructField("amount", DoubleType(), True),
    StructField("currency", StringType(), True),
    StructField("amount_usd", DoubleType(), True),
    StructField("purpose_code", StringType(), True),
    StructField("cross_border_flag", BooleanType(), True),
    StructField("declared_counterparty_name", StringType(), True),
    StructField("balance_after_txn", DoubleType(), True),
    StructField("is_split_component", BooleanType(), True),
    # Counterparty
    StructField("cp_id", StringType(), True),
    StructField("cp_type", StringType(), True),
    StructField("cp_jurisdiction", StringType(), True),
    StructField("cp_known_shell_flag", BooleanType(), True),
    StructField("cp_is_bank_customer", BooleanType(), True),
    StructField("counterparty_name", StringType(), True),        # NEW
    StructField("counterparty_address", StringType(), True),     # NEW
    StructField("counterparty_ip", StringType(), True),          # NEW
    # Endpoint
    StructField("endpoint_type", StringType(), True),
    StructField("ip_hash", StringType(), True),
    StructField("device_id_hash", StringType(), True),
    StructField("geo_lat", DoubleType(), True),
    StructField("geo_lon", DoubleType(), True),
    StructField("atm_id", StringType(), True),
    StructField("withdrawal_channel", StringType(), True),
    StructField("pos_terminal_id", StringType(), True),
    # Linkage breadcrumbs
    StructField("rep_id_hash", StringType(), True),
    StructField("address_hash", StringType(), True),
    StructField("website_hash", StringType(), True),
    # Generator-only annotations
    StructField("scenario_type", StringType(), True),
    StructField("scenario_role", StringType(), True),
    StructField("anomaly_flag", BooleanType(), True),
])

# -----------------------------
# Main generator
# -----------------------------
def generate_transactions_spark(
    spark: SparkSession,
    start_date: str,
    end_date: str,
    n_customers: int = 1000,
    pct_anomalous_monthly: float = 0.03,
    avg_txn_per_customer_per_month: Tuple[int,int] = (12, 40),
    identity_overlap_rate: float = 0.02,  # NEW: fraction of eligible txns to force overlaps
    seed: Optional[int] = 42,
):
    """
    Returns a PySpark DataFrame with the single-table schema.
    identity_overlap_rate: share of transactions where cp fields (name/address/ip) are
    set equal to the customer's fields while customer_id != cp_id, using a random subset
    of {name, address, ip} (at least one).
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    start = datetime.fromisoformat(start_date)
    end   = datetime.fromisoformat(end_date)
    if not (end > start):
        raise ValueError("end_date must be after start_date")

    customers = make_customers(n_customers, seed=seed)

    # Select anomalous customers + windows
    def pick_anomaly_window(start: datetime, end: datetime, seed: Optional[int]) -> Tuple[datetime, datetime]:
        rng = random.Random(seed)
        months = []
        cur = month_floor(start)
        while cur <= end.replace(day=1):
            months.append(cur)
            year = cur.year + (1 if cur.month == 12 else 0)
            month = 1 if cur.month == 12 else cur.month + 1
            cur = cur.replace(year=year, month=month)
        m0 = rng.choice(months)
        year = m0.year + (1 if m0.month == 12 else 0)
        month = 1 if m0.month == 12 else m0.month + 1
        m1 = m0.replace(year=year, month=month) - timedelta(seconds=1)
        return max(start, m0), min(end, m1)

    def anomaly_style_for(customer: Customer) -> str:
        if customer.customer_type == "legal_entity":
            return random.choice(["structuring","biz_split","rapid_drain"])
        if customer.customer_type == "fop":
            return random.choice(["structuring","rapid_drain"])
        return random.choice(["rapid_drain","structuring"])

    anomalous_cids = set(random.sample([c.customer_id for c in customers],
                                       k=max(1, int(len(customers) * pct_anomalous_monthly))))
    anomaly_windows: Dict[str, Tuple[datetime, datetime]] = {}
    anomaly_styles: Dict[str, str] = {}
    for c in customers:
        if c.customer_id in anomalous_cids:
            anomaly_windows[c.customer_id] = pick_anomaly_window(start, end, seed + hash(c.customer_id) % 10000)
            anomaly_styles[c.customer_id] = anomaly_style_for(c)

    rows: List[Row] = []
    balances = {c.account_id: float(max(0, np.random.normal(10_000, 5_000))) for c in customers}

    cur_month = month_floor(start)
    while cur_month <= end:
        next_month = (cur_month.replace(day=28) + timedelta(days=4)).replace(day=1)
        window_start = max(start, cur_month)
        window_end   = min(end, next_month - timedelta(seconds=1))

        for c in customers:
            mmin, mmax = avg_txn_per_customer_per_month
            monthly_n = int(np.random.randint(mmin, mmax + 1))

            is_abnormal_month = False
            style = None
            if c.customer_id in anomalous_cids:
                aw_start, aw_end = anomaly_windows[c.customer_id]
                if (window_start <= aw_end) and (window_end >= aw_start):
                    is_abnormal_month = True
                    style = anomaly_styles[c.customer_id]
                    monthly_n = int(monthly_n * np.random.uniform(1.5, 2.5))

            if monthly_n <= 0:
                continue

            span_seconds = int((window_end - window_start).total_seconds())
            ts_offsets = np.sort(np.random.randint(0, span_seconds + 1, size=monthly_n))
            txn_times = [window_start + timedelta(seconds=int(s)) for s in ts_offsets]

            shared_cp = rand_id("CPGRP", 6) if is_abnormal_month and style == "biz_split" else None
            shared_site = c.website_hash or (rand_id("WEB", 6) if (is_abnormal_month and style == "biz_split" and rand_bool(0.7)) else None)
            shared_rep  = c.rep_id_hash  or (rand_id("REP", 6) if (is_abnormal_month and rand_bool(0.4)) else None)

            for t in txn_times:
                acc_age_m = max(0, months_between(datetime.combine(c.open_date, datetime.min.time()), t))
                methods, probs = _normal_txn_mix(c)
                method = pick_weighted(methods, probs)

                if is_abnormal_month:
                    if style == "rapid_drain" and rand_bool(0.4):
                        method = random.choice(["wire_in","cash_withdrawal","wire_out"])
                    if style == "structuring" and rand_bool(0.4):
                        method = random.choice(["wire_out","p2p"])
                    if style == "biz_split" and rand_bool(0.5):
                        method = "wire_out"

                direction = "debit" if method in ("card_pos","card_ecom","cash_withdrawal","wire_out","p2p") else "credit"

                amt = _amount_sampler(method, c, anomalous=is_abnormal_month)
                purpose = _purpose_sampler(c, method, anomalous=is_abnormal_month)
                ep = _endpoint_sampler(method, anomalous=is_abnormal_month)
                cp = _counterparty_sampler(anomalous=is_abnormal_month)

                if is_abnormal_month and style == "biz_split":
                    cp["cp_id"] = shared_cp or cp["cp_id"]
                    purpose = random.choice(SERVICE_PURPOSES)

                cross_border_flag = False
                if is_abnormal_month and style == "rapid_drain":
                    if direction == "credit" and method in ("wire_in",):
                        cross_border_flag = rand_bool(0.5)
                        if cross_border_flag:
                            cp["cp_jurisdiction"] = random.choice(list(HIGH_RISK_DEST))
                    if direction == "debit" and method in ("cash_withdrawal","wire_out"):
                        cross_border_flag = rand_bool(0.2)

                is_split_component = False
                if is_abnormal_month and style == "structuring" and method in ("wire_out","p2p","cash_withdrawal"):
                    if any(abs(amt - s) / s < 0.03 for s in STRUCTURING_AMOUNTS):
                        is_split_component = True

                # Currency + USD normalization
                currency = pick_weighted(CURRENCIES, [0.85, 0.10, 0.05])
                amount_usd = round(float(amt) * float(FX_RATES_TO_USD.get(currency, 1.0)), 2)

                # ----- Identity overlap logic (customer_id != cp_id) -----
                # Decide if this txn should have any overlap (only if cp_id exists and differs)
                do_overlap = False
                if cp["cp_id"] is not None and cp["cp_id"] != c.customer_id and rand_bool(identity_overlap_rate):
                    do_overlap = True
                    # choose which fields to overlap (at least one)
                    fields = ["name", "address", "ip"]
                    k = random.choice([1, 2, 3])
                    chosen = set(random.sample(fields, k=k))
                else:
                    chosen = set()

                # Counterparty name/address/ip defaults
                cp_name = cp["declared_counterparty_name"]
                cp_addr = cp["counterparty_address"]
                cp_ip   = cp["counterparty_ip"]

                # Overwrite with customer's fields for chosen overlaps
                if "name" in chosen:
                    cp_name = c.customer_name
                if "address" in chosen:
                    cp_addr = c.address_full
                if "ip" in chosen:
                    # use customer's ip_hash if present; otherwise synthesize one
                    cp_ip = ep["ip_hash"] or f"IP_{rand_id('',6)[1:]}"

                bal = balances[c.account_id]
                new_bal = _advance_balance(bal, direction, amt)
                balances[c.account_id] = new_bal

                raw = dict(
                    txn_id=rand_id("T", 12),
                    txn_ts=t,
                    customer_id=c.customer_id,
                    account_id=c.account_id,
                    # KYC snapshot
                    customer_type=str(c.customer_type),
                    customer_name=str(c.customer_name),          # NEW
                    date_of_birth=c.dob,
                    address_full=str(c.address_full),
                    occupation=(str(c.occupation) if c.occupation is not None else None),
                    pep_indicator=bool(c.pep_indicator),
                    industry_code=(str(c.industry_code) if c.industry_code is not None else None),
                    account_open_months=int(acc_age_m),
                    whitelist_flag=bool(c.whitelist_flag),
                    # Txn
                    direction=str(direction),
                    method=str(method),
                    amount=float(round(float(amt), 2)),
                    currency=str(currency),
                    amount_usd=float(amount_usd),
                    purpose_code=str(purpose),
                    cross_border_flag=bool(cross_border_flag),
                    declared_counterparty_name=(str(cp_name) if cp_name is not None else None),
                    balance_after_txn=float(round(new_bal, 2)),
                    is_split_component=bool(is_split_component),
                    # Counterparty
                    cp_id=(str(cp["cp_id"]) if cp["cp_id"] is not None else None),
                    cp_type=str(cp["cp_type"]),
                    cp_jurisdiction=(str(cp["cp_jurisdiction"]) if cp["cp_jurisdiction"] is not None else None),
                    cp_known_shell_flag=bool(cp["cp_known_shell_flag"]),
                    cp_is_bank_customer=bool(cp["cp_is_bank_customer"]),
                    counterparty_name=(str(cp_name) if cp_name is not None else None),          # NEW
                    counterparty_address=(str(cp_addr) if cp_addr is not None else None),       # NEW
                    counterparty_ip=(str(cp_ip) if cp_ip is not None else None),                # NEW
                    # Endpoint
                    endpoint_type=str(ep["endpoint_type"]),
                    ip_hash=(str(ep["ip_hash"]) if ep["ip_hash"] is not None else None),
                    device_id_hash=(str(ep["device_id_hash"]) if ep["device_id_hash"] is not None else None),
                    geo_lat=(float(ep["geo_lat"]) if ep["geo_lat"] is not None else None),
                    geo_lon=(float(ep["geo_lon"]) if ep["geo_lon"] is not None else None),
                    atm_id=(str(ep["atm_id"]) if ep["atm_id"] is not None else None),
                    withdrawal_channel=(str(ep["withdrawal_channel"]) if ep["withdrawal_channel"] is not None else None),
                    pos_terminal_id=(str(ep["pos_terminal_id"]) if ep["pos_terminal_id"] is not None else None),
                    # Linkage breadcrumbs
                    rep_id_hash=(str(shared_rep) if (is_abnormal_month and rand_bool(0.2)) else (str(c.rep_id_hash) if c.rep_id_hash is not None else None)),
                    address_hash=(str(c.address_hash) if c.address_hash is not None else None),
                    website_hash=(str(shared_site) if (is_abnormal_month and style=="biz_split") else (str(c.website_hash) if c.website_hash is not None else None)),
                    # Generator-only annotations
                    scenario_type=("normal" if not is_abnormal_month else
                                   ("rapid_drain" if style=="rapid_drain" else
                                    "structuring" if style=="structuring" else
                                    "business_splitting")),
                    scenario_role=("none" if not is_abnormal_month else
                                   ("anchor" if style=="business_splitting" and c.customer_type=="legal_entity" else
                                    "group_member" if style=="business_splitting" else
                                    "mule" if style=="rapid_drain" and c.customer_type!="legal_entity" else
                                    "feeder")),
                    anomaly_flag=bool(is_abnormal_month),
                )

                rows.append(Row(**{k: to_py(v) for k, v in raw.items()}))

        cur_month = next_month

    df = spark.createDataFrame(rows, schema=SCHEMA)
    return df

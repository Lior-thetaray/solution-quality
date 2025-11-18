#!/usr/bin/env python3
"""
SEPA Synthetic Transactions Generator
-------------------------------------

Generates realistic-looking SEPA transactions (SCT & SDD) with
reasonable distributions, plus built‑in "cases" (scenarios) useful
for analytics, QA and model training.

Includes:
- Debtor & Creditor postal addresses (synthetic).
- IP addresses for online/mobile transactions (IPv4).

Key features
- Distributions for amounts (mixture of lognormal/normal), timestamps
  with weekday/hour-of-day patterns, counterparties and countries.
- Valid IBAN check digits for several SEPA countries (DE, FR, ES, IT, NL, BE, AT, PT, IE, FI, GR).
- Simple BIC catalog per country.
- Purpose codes (ISO 20022) and merchant categories.
- Scenarios: salary runs, card/POS burst to merchant, structuring (smurfing) deposits,
  SDD CORE + return (R-transaction), and mule-ish in→out fan-out. Each row is labeled with
  a case_label for supervised tasks.
- Deterministic with --seed.

Output
- CSV with one row per transaction.

Usage
------
$ python sepa_data_generator.py --n 50000 --start 2024-01-01 --end 2024-12-31 \
    --out sepa_synth.csv --seed 42 --cases salary,merchant_burst,structuring,returns,mule

Notes
- All data is synthetic. No real persons, banks or accounts.
- "Cases" are for testing detection systems and analytics pipelines.
"""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import math
import random
import string
import uuid
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Callable

# ----------------------------- Utilities ---------------------------------

def _letters_to_digits(s: str) -> str:
    # A=10 ... Z=35
    return ''.join(str(ord(ch) - 55) if ch.isalpha() else ch for ch in s)

def iban_check_digits(country: str, bban: str) -> str:
    # Compute ISO 13616 mod-97 check digits
    rearranged = bban + country + '00'
    numeric = int(_letters_to_digits(rearranged))
    cd = 98 - (numeric % 97)
    return f"{cd:02d}"

def make_iban(country: str, bank_code: str, branch: str, acct: str) -> str:
    bban = (bank_code + branch + acct)
    cd = iban_check_digits(country, bban)
    return f"{country}{cd}{bban}"

def random_ipv4(r: random.Random) -> str:
    # Avoid 0 and 255 for first octet to look less special-case
    first = r.randint(1, 254)
    rest = [r.randint(0, 255) for _ in range(3)]
    return ".".join([str(first)] + [str(x) for x in rest])

# ----------------------- Light synthetic catalogs ------------------------

@dataclass
class CountrySpec:
    country: str
    bank_len: int
    branch_len: int
    acct_len: int
    iban_len: int

# Minimal patterns for a set of common SEPA countries
COUNTRY_SPECS: Dict[str, CountrySpec] = {
    # country, bank, branch, acct, iban total
    'DE': CountrySpec('DE', 8, 0, 10, 22),
    'FR': CountrySpec('FR', 5, 5, 11, 27),
    'ES': CountrySpec('ES', 4, 4, 12, 24),
    'IT': CountrySpec('IT', 5, 5, 12, 27),
    'NL': CountrySpec('NL', 4, 0, 10, 18),
    'BE': CountrySpec('BE', 3, 0, 11, 16),
    'AT': CountrySpec('AT', 5, 0, 11, 20),
    'PT': CountrySpec('PT', 4, 4, 11, 25),
    'IE': CountrySpec('IE', 4, 0, 14, 22),
    'FI': CountrySpec('FI', 6, 0, 8, 18),
    'GR': CountrySpec('GR', 3, 4, 16, 27),
}

# A small BIC catalog (dummy realistic-looking codes)
BICS_BY_COUNTRY: Dict[str, List[str]] = {
    'DE': ['DEUTDEFF', 'COBADEFF', 'BYLADEM1MUN'],
    'FR': ['BNPAFRPP', 'SOGEFRPP', 'CRLYFRPP'],
    'ES': ['BBVAESMM', 'CAIXESBB', 'BSABESBB'],
    'IT': ['BCITITMM', 'UNCRITMM', 'BCITITRR'],
    'NL': ['ABNANL2A', 'INGBNL2A', 'RABONL2U'],
    'BE': ['KREDBEBB', 'GEBABEBB', 'BBRUBEBB'],
    'AT': ['OBKLAT2L', 'SPADATW1', 'RZOOAT2L'],
    'PT': ['TOTAPTPL', 'BESCPTPL', 'CGDIPTPL'],
    'IE': ['AIBKIE2D', 'BOFIIE2D', 'IRCEIE2D'],
    'FI': ['NDEAFIHH', 'DABAFIHH', 'OKOYFIHH'],
    'GR': ['ETHNGRAA', 'PIRBGRAA', 'ALPHGRAA'],
}

FIRST_NAMES = [
    'Liam','Noah','Oliver','Elijah','Emma','Olivia','Ava','Mia','Sofia','Amelia',
    'Luca','Sophie','Lucas','Lea','Hugo','Louis','Leon','Noe','Sara','Giulia',
]
LAST_NAMES = [
    'Martin','Bernard','Dubois','Muller','Schmidt','Weber','Fischer','Bauer',
    'Garcia','Fernandez','Rossi','Russo','Vermeulen','Jansen','Murphy','Nieminen'
]
MERCHANTS = [
    'AMZ EU Sarl','Zalando SE','IKEA Stores','ALDI','LIDL','Carrefour','MediaMarkt',
    'Uber BV','Bolt Operations','Spotify','Netflix','Steam Games EU','Ryanair DAC','Wizz Air',
]
BILLERS = ['City Utilities','GreenEnergy SA','Vodafone','Orange Telecom','Suez Water','Rent LLC']

ADDRESSES = [
    '123 Main St, Berlin, Germany',
    '45 Rue de Lyon, Paris, France',
    '12 Via Roma, Milan, Italy',
    'Calle Mayor 22, Madrid, Spain',
    'Stationsstraat 5, Amsterdam, Netherlands',
    'Rue Royale 100, Brussels, Belgium',
    'Mariahilfer Str. 77, Vienna, Austria',
    'Rua Augusta 15, Lisbon, Portugal',
    'O’Connell St 200, Dublin, Ireland',
    'Mannerheimintie 10, Helsinki, Finland',
    'Ermou 50, Athens, Greece',
]

PURPOSE_CODES = [
    'SALA','SUPP','GOVT','TAXS','PENS','RENT','OTHR','TELI','ELEC','WTER','TRAD','CASH','LOAN','INTE'
]

MCC_SAMPLE = ['5311','5411','5812','5814','5732','5691','4111','4511','4812','4121','7995']
CHANNELS = ['ONLINE','MOBILE','BRANCH','POS']

# -------------------------- Random helpers -------------------------------

class RNG:
    def __init__(self, seed: Optional[int]=None):
        self.r = random.Random(seed)

    def choice(self, seq):
        return self.r.choice(seq)

    def weighted(self, items_with_w):
        items, weights = zip(*items_with_w)
        total = sum(weights)
        x = self.r.random() * total
        acc = 0
        for item, w in zip(items, weights):
            acc += w
            if x <= acc:
                return item
        return items[-1]

    def lognormal(self, mean: float, sigma: float) -> float:
        return self.r.lognormvariate(mean, sigma)

    def normal(self, mu: float, sigma: float) -> float:
        return self.r.normalvariate(mu, sigma)

    def expovariate(self, lambd: float) -> float:
        return self.r.expovariate(lambd)

    def randint(self, a: int, b: int) -> int:
        return self.r.randint(a, b)

# ------------------------ Generative primitives --------------------------

@dataclass
class Identity:
    name: str
    country: str
    iban: str
    bic: str
    address: str

class IdentityFactory:
    def __init__(self, rng: RNG):
        self.rng = rng

    def random_country(self) -> str:
        choices = [('DE', 20), ('FR', 16), ('IT', 15), ('ES', 12), ('NL', 7), ('BE', 4),
                   ('AT', 4), ('PT', 3), ('IE', 3), ('FI', 3), ('GR', 3)]
        return self.rng.weighted(choices)

    def make_iban_for_country(self, country: str) -> str:
        spec = COUNTRY_SPECS[country]
        def digits(n: int) -> str:
            return ''.join(self.rng.choice(string.digits) for _ in range(n))
        def letters(n: int) -> str:
            return ''.join(self.rng.choice(string.ascii_uppercase) for _ in range(n))
        bank = letters(min(4, spec.bank_len)) + digits(max(0, spec.bank_len - 4)) if spec.bank_len else ''
        branch = digits(spec.branch_len) if spec.branch_len else ''
        acct = digits(spec.acct_len)
        iban = make_iban(country, bank, branch, acct)
        if len(iban) != spec.iban_len:
            pad = spec.iban_len - len(iban)
            if pad > 0:
                acct2 = acct + '0'*pad
            else:
                acct2 = acct[:pad]
            iban = make_iban(country, bank, branch, acct2)
        return iban

    def random_name(self) -> str:
        return f"{self.rng.choice(FIRST_NAMES)} {self.rng.choice(LAST_NAMES)}"

    def random_bic(self, country: str) -> str:
        return self.rng.choice(BICS_BY_COUNTRY[country])

    def make_identity(self, country: Optional[str]=None) -> Identity:
        c = country or self.random_country()
        name = self.random_name()
        iban = self.make_iban_for_country(c)
        bic = self.random_bic(c)
        address = self.rng.choice(ADDRESSES)
        return Identity(name=name, country=c, iban=iban, bic=bic, address=address)

# ------------------------- Calendaring -----------------------------------

class Calendar:
    def __init__(self, start: dt.date, end: dt.date, rng: RNG):
        if end < start:
            raise ValueError('end before start')
        self.start = start
        self.end = end
        self.rng = rng
        self._all_days = [start + dt.timedelta(days=i) for i in range((end-start).days + 1)]

    def random_date(self) -> dt.date:
        return self.rng.choice(self._all_days)

    def random_business_date(self) -> dt.date:
        while True:
            d = self.random_date()
            if d.weekday() < 5 or self.rng.r.random() < 0.2:
                return d

    def random_time(self, business_bias: bool=True) -> dt.time:
        if business_bias:
            hourly_weights = [1,1,1,1,1,2,4,6,8,10,10,9,8,7,6,6,7,6,5,3,2,2,1,1]
        else:
            hourly_weights = [1,1,1,1,1,1,2,3,3,4,5,6,7,8,9,8,7,6,5,4,3,2,1,1]
        hour = self.rng.weighted(list(enumerate(hourly_weights)))
        minute = self.rng.randint(0,59)
        second = self.rng.randint(0,59)
        return dt.time(hour=hour, minute=minute, second=second)

    def random_timestamp(self, business_bias: bool=True) -> dt.datetime:
        d = self.random_business_date()
        t = self.random_time(business_bias)
        return dt.datetime.combine(d, t)

# ------------------------- Amount models ---------------------------------

class AmountModel:
    def __init__(self, rng: RNG):
        self.rng = rng

    def retail_amount(self) -> float:
        if self.rng.r.random() < 0.85:
            val = self.rng.lognormal(math.log(35), 0.7)
        else:
            val = self.rng.lognormal(math.log(120), 0.6)
        return max(1.0, round(val, 2))

    def bill_amount(self) -> float:
        val = self.rng.normal(120.0, 40.0)
        return max(10.0, round(val, 2))

    def salary_amount(self) -> float:
        val = self.rng.normal(3200.0, 900.0)
        return max(800.0, round(val, 2))

    def transfer_amount(self) -> float:
        if self.rng.r.random() < 0.7:
            val = self.rng.lognormal(math.log(250), 0.8)
        else:
            val = self.rng.lognormal(math.log(1200), 0.7)
        return max(5.0, round(val, 2))

    def structuring_amount(self, ceiling: float=1000.0) -> float:
        base = self.rng.normal(0.85*ceiling, 0.12*ceiling)
        val = min(ceiling - self.rng.r.random()*5, max(50.0, base))
        return round(val, 2)

# ------------------------ Transaction assembly ---------------------------

TX_COLUMNS = [
    'tx_id','e2e_id','scheme','msg_type','status','booking_ts','value_ts','channel',
    'amount','currency','purpose_code','mcc','case_label',
    'debtor_name','debtor_iban','debtor_bic','debtor_country','debtor_address','debtor_ip',
    'creditor_name','creditor_iban','creditor_bic','creditor_country','creditor_address','creditor_ip',
    'remittance_info','original_tx_id'
]

@dataclass
class Config:
    n: int
    start: dt.date
    end: dt.date
    seed: Optional[int]
    include_cases: List[str]

class IdGen:
    def __init__(self, rng: RNG):
        self.rng = rng

    def tx_id(self) -> str:
        return uuid.uuid4().hex[:24].upper()

    def e2e(self) -> str:
        return 'E2E' + uuid.uuid4().hex[:27].upper()

# ----------------------------- Emission ----------------------------------

class Emitter:
    def __init__(self, writer: csv.DictWriter):
        self.writer = writer

    def emit(self, row: Dict):
        self.writer.writerow(row)

# --------------------------- Core generator ------------------------------

class SepaGenerator:
    def __init__(self, cfg: Config):
        self.rng = RNG(cfg.seed)
        self.cfg = cfg
        self.idf = IdentityFactory(self.rng)
        self.amounts = AmountModel(self.rng)
        self.calendar = Calendar(cfg.start, cfg.end, self.rng)
        self.idg = IdGen(self.rng)

    # ---------- single generic transactions ----------
    def _mk_base(self, business_bias=True) -> Dict:
        debtor = self.idf.make_identity()
        creditor = self.idf.make_identity()
        ts = self.calendar.random_timestamp(business_bias)
        val_ts = ts + dt.timedelta(days=self.rng.randint(0,2))
        scheme = self.rng.weighted([('SCT', 0.65), ('SDD_CORE', 0.35)])
        msg_type = 'pacs.008.001.02' if scheme=='SCT' else 'pacs.003.001.02'
        status = 'BOOKED'
        purpose = self.rng.choice(PURPOSE_CODES)
        mcc = self.rng.choice(MCC_SAMPLE) if purpose not in ('SALA','RENT','TAXS','GOVT') else ''
        channel = self.rng.weighted([(c, w) for c,w in zip(CHANNELS, [3,3,1,4])])

        debtor_ip = random_ipv4(self.rng.r) if channel in ('ONLINE','MOBILE') else ''
        creditor_ip = random_ipv4(self.rng.r) if channel in ('ONLINE','MOBILE') else ''

        row = {
            'tx_id': self.idg.tx_id(),
            'e2e_id': self.idg.e2e(),
            'scheme': scheme,
            'msg_type': msg_type,
            'status': status,
            'booking_ts': ts.isoformat(sep=' '),
            'value_ts': val_ts.isoformat(sep=' '),
            'channel': channel,
            'amount': 0.0, # fill below
            'currency': 'EUR',
            'purpose_code': purpose,
            'mcc': mcc,
            'case_label': '',
            'debtor_name': debtor.name,
            'debtor_iban': debtor.iban,
            'debtor_bic': debtor.bic,
            'debtor_country': debtor.country,
            'debtor_address': debtor.address,
            'debtor_ip': debtor_ip,
            'creditor_name': creditor.name,
            'creditor_iban': creditor.iban,
            'creditor_bic': creditor.bic,
            'creditor_country': creditor.country,
            'creditor_address': creditor.address,
            'creditor_ip': creditor_ip,
            'remittance_info': '',
            'original_tx_id': '',
        }
        # Amount by purpose
        if row['purpose_code']=='SALA':
            row['amount'] = self.amounts.salary_amount()
            row['remittance_info'] = 'Salary'
        elif row['purpose_code'] in ('TELI','ELEC','WTER','RENT'):
            row['amount'] = self.amounts.bill_amount()
            row['remittance_info'] = 'Invoice payment'
        else:
            row['amount'] = self.amounts.transfer_amount()
            row['remittance_info'] = 'Transfer'
        return row

    def _apply_channel_ips(self, row: Dict):
        ch = row.get('channel', 'ONLINE')
        if ch in ('ONLINE','MOBILE'):
            # assign synthetic, if missing
            row['debtor_ip'] = row.get('debtor_ip') or random_ipv4(self.rng.r)
            row['creditor_ip'] = row.get('creditor_ip') or random_ipv4(self.rng.r)
        else:
            row['debtor_ip'] = ''
            row['creditor_ip'] = ''

    def generic(self, emit: Callable[[Dict], None]):
        row = self._mk_base(business_bias=True)
        self._apply_channel_ips(row)
        emit(row)

    # ------------------------ Cases / Scenarios ---------------------------

    def case_salary(self, emit: Callable[[Dict], None]):
        employer = self.idf.make_identity(country='DE')
        months = self._months_span(self.cfg.start, self.cfg.end)
        if not months:
            return
        months = self.rng.r.sample(months, k=max(1, min(8, len(months))))
        for y,m in months:
            payday = self._last_business_day(y, m)
            n_emp = self.rng.randint(30, 120)
            for _ in range(n_emp):
                emp = self.idf.make_identity(country=self.rng.weighted([('DE',5),('FR',3),('NL',2),('ES',3),('IT',3)]))
                ts = dt.datetime.combine(payday, dt.time(hour=self.rng.weighted([(9,2),(10,3),(11,5),(12,5),(13,3)])))
                row = {
                    **self._mk_base(business_bias=True),
                    'tx_id': self.idg.tx_id(),
                    'e2e_id': self.idg.e2e(),
                    'scheme': 'SCT',
                    'msg_type': 'pacs.008.001.02',
                    'booking_ts': ts.isoformat(sep=' '),
                    'value_ts': ts.isoformat(sep=' '),
                    'debtor_name': employer.name,
                    'debtor_iban': employer.iban,
                    'debtor_bic': employer.bic,
                    'debtor_country': employer.country,
                    'debtor_address': employer.address,
                    'creditor_name': emp.name,
                    'creditor_iban': emp.iban,
                    'creditor_bic': emp.bic,
                    'creditor_country': emp.country,
                    'creditor_address': emp.address,
                    'purpose_code': 'SALA',
                    'remittance_info': 'Salary',
                    'amount': self.amounts.salary_amount(),
                    'channel': 'ONLINE',
                    'case_label': 'salary_run',
                }
                self._apply_channel_ips(row)
                emit(row)

    def case_merchant_burst(self, emit: Callable[[Dict], None]):
        merchant_name = self.rng.choice(MERCHANTS)
        merchant = self.idf.make_identity(country=self.rng.weighted([('NL',4),('DE',4),('IE',2)]))
        d = self.calendar.random_date()
        while d.weekday() not in (5,6):
            d += dt.timedelta(days=1)
            if d > self.cfg.end: d = self.cfg.start
        mcc = self.rng.choice(MCC_SAMPLE)
        n = self.rng.randint(150, 450)
        for _ in range(n):
            cust = self.idf.make_identity()
            hour = self.rng.weighted([(10,2),(11,3),(12,4),(13,4),(18,5),(19,6),(20,6),(21,4)])
            ts = dt.datetime.combine(d, dt.time(hour=hour, minute=self.rng.randint(0,59), second=self.rng.randint(0,59)))
            row = {
                **self._mk_base(business_bias=False),
                'tx_id': self.idg.tx_id(),
                'e2e_id': self.idg.e2e(),
                'scheme': 'SCT',
                'msg_type': 'pacs.008.001.02',
                'booking_ts': ts.isoformat(sep=' '),
                'value_ts': ts.isoformat(sep=' '),
                'debtor_name': cust.name,
                'debtor_iban': cust.iban,
                'debtor_bic': cust.bic,
                'debtor_country': cust.country,
                'debtor_address': cust.address,
                'creditor_name': merchant_name,
                'creditor_iban': merchant.iban,
                'creditor_bic': merchant.bic,
                'creditor_country': merchant.country,
                'creditor_address': merchant.address,
                'purpose_code': 'TRAD',
                'mcc': mcc,
                'remittance_info': f'POS {merchant_name}',
                'amount': self.amounts.retail_amount(),
                'channel': 'POS',
                'case_label': 'merchant_burst',
            }
            self._apply_channel_ips(row)
            emit(row)

    def case_structuring(self, emit: Callable[[Dict], None]):
        target = self.idf.make_identity(country=self.rng.weighted([('ES',3),('IT',3),('FR',2),('DE',2)]))
        ceiling = self.rng.weighted([(1000,6),(2000,2),(5000,1)])
        window_days = self.rng.randint(1, 3)
        start_day = self.calendar.random_business_date()
        senders = [self.idf.make_identity() for _ in range(self.rng.randint(8, 30))]
        for s in senders:
            d = start_day + dt.timedelta(days=self.rng.randint(0, window_days))
            hour = self.rng.weighted([(9,2),(10,3),(11,4),(12,3),(13,2),(14,2),(15,2),(16,2)])
            ts = dt.datetime.combine(d, dt.time(hour=hour, minute=self.rng.randint(0,59), second=self.rng.randint(0,59)))
            row = {
                **self._mk_base(business_bias=True),
                'tx_id': self.idg.tx_id(),
                'e2e_id': self.idg.e2e(),
                'scheme': 'SCT',
                'msg_type': 'pacs.008.001.02',
                'booking_ts': ts.isoformat(sep=' '),
                'value_ts': ts.isoformat(sep=' '),
                'debtor_name': s.name,
                'debtor_iban': s.iban,
                'debtor_bic': s.bic,
                'debtor_country': s.country,
                'debtor_address': s.address,
                'creditor_name': target.name,
                'creditor_iban': target.iban,
                'creditor_bic': target.bic,
                'creditor_country': target.country,
                'creditor_address': target.address,
                'purpose_code': 'OTHR',
                'remittance_info': 'Payment',
                'amount': self.amounts.structuring_amount(ceiling=float(ceiling)),
                'channel': 'ONLINE',
                'case_label': f'structuring_u{int(ceiling)}',
            }
            self._apply_channel_ips(row)
            emit(row)

    def case_returns(self, emit: Callable[[Dict], None]):
        debtor = self.idf.make_identity()
        creditor = self.idf.make_identity()
        n_debits = self.rng.randint(10, 25)
        for _ in range(n_debits):
            ts = self.calendar.random_timestamp(business_bias=True)
            amt = self.amounts.bill_amount()
            base_row = {
                **self._mk_base(business_bias=True),
                'tx_id': self.idg.tx_id(),
                'e2e_id': self.idg.e2e(),
                'scheme': 'SDD_CORE',
                'msg_type': 'pacs.003.001.02',
                'booking_ts': ts.isoformat(sep=' '),
                'value_ts': ts.isoformat(sep=' '),
                'debtor_name': debtor.name,
                'debtor_iban': debtor.iban,
                'debtor_bic': debtor.bic,
                'debtor_country': debtor.country,
                'debtor_address': debtor.address,
                'creditor_name': creditor.name,
                'creditor_iban': creditor.iban,
                'creditor_bic': creditor.bic,
                'creditor_country': creditor.country,
                'creditor_address': creditor.address,
                'purpose_code': self.rng.weighted([('TELI',2),('ELEC',2),('WTER',1),('OTHR',1)]),
                'remittance_info': f'{self.rng.choice(BILLERS)} invoice',
                'amount': amt,
                'channel': 'ONLINE',
                'case_label': 'sdd_bill',
                'status': 'BOOKED',
            }
            self._apply_channel_ips(base_row)
            emit(base_row)
            if self.rng.r.random() < 0.18:
                reason = self.rng.weighted([('AM04',5),('AC04',3),('MD06',2),('MS03',2)])
                r_ts = dt.datetime.fromisoformat(base_row['booking_ts']) + dt.timedelta(days=self.rng.randint(1, 30))
                ret = {**base_row}
                ret.update({
                    'tx_id': self.idg.tx_id(),
                    'e2e_id': self.idg.e2e(),
                    'status': f'RRTN_{reason}',
                    'booking_ts': r_ts.isoformat(sep=' '),
                    'value_ts': r_ts.isoformat(sep=' '),
                    'case_label': 'sdd_return',
                    'original_tx_id': base_row['tx_id'],
                })
                self._apply_channel_ips(ret)
                emit(ret)

    def case_mule_fanout(self, emit: Callable[[Dict], None]):
        hub = self.idf.make_identity(country=self.rng.weighted([('NL',3),('BE',2),('DE',2),('FR',2)]))
        n_in = self.rng.randint(5, 15)
        t0 = self.calendar.random_business_date()
        in_rows = []
        for _ in range(n_in):
            src = self.idf.make_identity()
            ts = dt.datetime.combine(t0, self.calendar.random_time(business_bias=True))
            row = {
                **self._mk_base(business_bias=True),
                'tx_id': self.idg.tx_id(),
                'e2e_id': self.idg.e2e(),
                'scheme': 'SCT',
                'msg_type': 'pacs.008.001.02',
                'booking_ts': ts.isoformat(sep=' '),
                'value_ts': ts.isoformat(sep=' '),
                'debtor_name': src.name,
                'debtor_iban': src.iban,
                'debtor_bic': src.bic,
                'debtor_country': src.country,
                'debtor_address': src.address,
                'creditor_name': hub.name,
                'creditor_iban': hub.iban,
                'creditor_bic': hub.bic,
                'creditor_country': hub.country,
                'creditor_address': hub.address,
                'amount': self.amounts.transfer_amount(),
                'purpose_code': 'OTHR',
                'channel': 'ONLINE',
                'case_label': 'mule_in',
            }
            self._apply_channel_ips(row)
            in_rows.append(row)
            emit(row)
        total_in = sum(r['amount'] for r in in_rows)
        n_out = self.rng.randint(5, 12)
        remain = total_in * self.rng.r.uniform(0.78, 0.98)
        for i in range(n_out):
            dst = self.idf.make_identity()
            ts = dt.datetime.combine(t0, dt.time(hour=min(23, 10 + i)))
            amt = min(remain, self.amounts.transfer_amount())
            remain -= amt
            row = {
                **self._mk_base(business_bias=True),
                'tx_id': self.idg.tx_id(),
                'e2e_id': self.idg.e2e(),
                'scheme': 'SCT',
                'msg_type': 'pacs.008.001.02',
                'booking_ts': ts.isoformat(sep=' '),
                'value_ts': ts.isoformat(sep=' '),
                'debtor_name': hub.name,
                'debtor_iban': hub.iban,
                'debtor_bic': hub.bic,
                'debtor_country': hub.country,
                'debtor_address': hub.address,
                'creditor_name': dst.name,
                'creditor_iban': dst.iban,
                'creditor_bic': dst.bic,
                'creditor_country': dst.country,
                'creditor_address': dst.address,
                'amount': round(amt, 2),
                'purpose_code': 'OTHR',
                'channel': 'ONLINE',
                'case_label': 'mule_out',
            }
            self._apply_channel_ips(row)
            if row['amount'] >= 5.0:
                emit(row)

    # ----------------------- Orchestration --------------------------------

    def generate(self, emit: Callable[[Dict], None]):
        n_generic = int(self.cfg.n * 0.7)
        for _ in range(n_generic):
            self.generic(emit)
        for case in self.cfg.include_cases:
            if case == 'salary':
                self.case_salary(emit)
            elif case == 'merchant_burst':
                self.case_merchant_burst(emit)
            elif case == 'structuring':
                self.case_structuring(emit)
            elif case == 'returns':
                self.case_returns(emit)
            elif case == 'mule':
                self.case_mule_fanout(emit)

    # --------------------- Helpers ---------------------------------------

    @staticmethod
    def _months_span(start: dt.date, end: dt.date) -> List[Tuple[int,int]]:
        months = []
        y, m = start.year, start.month
        while (y < end.year) or (y == end.year and m <= end.month):
            months.append((y, m))
            m += 1
            if m > 12:
                m = 1
                y += 1
        return months

    def _last_business_day(self, year: int, month: int) -> dt.date:
        if month == 12:
            last = dt.date(year, month, 31)
        else:
            last = dt.date(year, month+1, 1) - dt.timedelta(days=1)
        while last.weekday() >= 5:
            last -= dt.timedelta(days=1)
        return last

# ----------------------------- CLI ---------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='SEPA synthetic transaction generator')
    p.add_argument('--n', type=int, default=10000, help='approx number of generic transactions (cases add on top)')
    p.add_argument('--start', type=str, default='2024-01-01')
    p.add_argument('--end', type=str, default='2024-12-31')
    p.add_argument('--out', type=str, default='sepa_synth.csv')
    p.add_argument('--seed', type=int, default=None)
    p.add_argument('--cases', type=str, default='salary,merchant_burst,structuring,returns,mule',
                   help='comma-separated cases to include')
    return p.parse_args()

def main():
    args = parse_args()
    start = dt.datetime.strptime(args.start, '%Y-%m-%d').date()
    end = dt.datetime.strptime(args.end, '%Y-%m-%d').date()
    cfg = Config(n=args.n, start=start, end=end, seed=args.seed,
                 include_cases=[c.strip() for c in args.cases.split(',') if c.strip()])
    gen = SepaGenerator(cfg)

    with open(args.out, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=TX_COLUMNS)
        writer.writeheader()
        count = 0
        def emit(row: Dict):
            nonlocal count
            count += 1
            writer.writerow(row)
        gen.generate(emit)
    print(f"Wrote {count} rows to {args.out}")

if __name__ == '__main__':
    main()

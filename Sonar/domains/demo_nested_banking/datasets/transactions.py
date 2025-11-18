from typing import List
from thetaray.api.solution import DataSet, Field, DataType, IngestionMode


def transactions_dataset():
    return DataSet(
        identifier='demo_nested_banking_transactions',
        display_name='Nested Accounts/Correspondent Banking SWIFT MX Transactions',
        ingestion_mode=IngestionMode.APPEND,
        publish=True,
        primary_key=['transaction_id'],
        num_of_partitions=1,
        num_of_buckets=1,
        data_permission="dpv:demo_nested_banking",
        occurred_on_field='transaction_timestamp',
        field_list=[
            # Core identifiers & timing
            Field(identifier='transaction_id', display_name='Transaction ID', data_type=DataType.STRING, comment='Unique identifier for the transaction'),
            Field(identifier='biz_msg_idr', display_name='Business Message Identifier', data_type=DataType.STRING, comment='ISO 20022 BAH BusinessMessageIdentifier'),
            Field(identifier='msg_def_id', display_name='Message Definition ID', data_type=DataType.STRING, comment='ISO 20022 message e.g. pacs.008.001.10 / pacs.009.001.10'),
            Field(identifier='purpose', display_name='Payment Category', data_type=DataType.STRING, comment='CustomerCreditTransfer or FItoFITransfer'),
            Field(identifier='uetr', display_name='UETR', data_type=DataType.STRING, comment='Unique End-to-End Transaction Reference (gpi)'),
            Field(identifier='end_to_end_id', display_name='EndToEndId', data_type=DataType.STRING, comment='End-to-end identifier'),
            Field(identifier='tx_id', display_name='Transaction Identification', data_type=DataType.STRING, comment='Interbank transaction identification'),
            Field(identifier='instr_id', display_name='Instruction Identification', data_type=DataType.STRING, comment='Instruction identifier'),
            Field(identifier='transaction_timestamp', display_name='Transaction Timestamp', data_type=DataType.TIMESTAMP, comment='Date and time when the transaction occurred'),
            Field(identifier='transaction_date', display_name='Transaction Date', data_type=DataType.TIMESTAMP, comment='Date when the transaction occurred'),
            Field(identifier='year_month', display_name='Year-Month', data_type=DataType.TIMESTAMP, comment='Transaction year-month (YYYY-MM)'),

            # Customer / nested-account context (internal enrichment)
            Field(identifier='nested_account_id', display_name='Nested Account ID', data_type=DataType.STRING, comment='Internal account identifier for respondent at the correspondent (enrichment)'),
            Field(identifier='customer_id', display_name='Customer ID', data_type=DataType.STRING, comment='Respondent bank identifier'),
            Field(identifier='customer_name', display_name='Customer Name', data_type=DataType.STRING, comment='Respondent bank legal name'),
            Field(identifier='customer_size', display_name='Customer Size Bucket', data_type=DataType.STRING, comment='Small / Medium / Large'),

            # Amounts, currency, charges, channel
            Field(identifier='instd_amt', display_name='Instructed Amount', data_type=DataType.DOUBLE, comment='Instructed amount'),
            Field(identifier='intr_bk_sttlm_amt', display_name='Interbank Settlement Amount', data_type=DataType.DOUBLE, comment='Interbank settlement amount'),
            Field(identifier='ccy', display_name='Currency Code', data_type=DataType.STRING, comment='ISO-3 currency'),
            Field(identifier='intr_bk_sttlm_dt', display_name='Interbank Settlement Date', data_type=DataType.TIMESTAMP, comment='Interbank settlement date'),
            Field(identifier='value_date', display_name='Value Date', data_type=DataType.TIMESTAMP, comment='Value date at agent level'),
            Field(identifier='chrg_br', display_name='Charge Bearer', data_type=DataType.STRING, comment='ISO 20022 charge bearer (SLEV, SHAR, DEBT, CRED)'),
            Field(identifier='channel', display_name='Channel', data_type=DataType.STRING, comment='Transfer rail (e.g., SWIFT-CBPR+)'),
            Field(identifier='direction', display_name='Direction', data_type=DataType.STRING, comment='IN (credit) or OUT (debit) relative to the correspondent'),

            # Jurisdiction & agent BICs (BIC8 normalized)
            Field(identifier='dbtr_country_code', display_name='Debtor Country Code', data_type=DataType.STRING, comment='ISO-2 debtor country'),
            Field(identifier='dbtr_country_name', display_name='Debtor Country Name', data_type=DataType.STRING, comment='Debtor country name'),
            Field(identifier='cdtr_country_code', display_name='Creditor Country Code', data_type=DataType.STRING, comment='ISO-2 creditor country'),
            Field(identifier='cdtr_country_name', display_name='Creditor Country Name', data_type=DataType.STRING, comment='Creditor country name'),
            Field(identifier='dbtr_agt_bic8', display_name='Debtor Agent BIC8', data_type=DataType.STRING, comment='DebtorAgent.BIC (8-char)'),
            Field(identifier='cdtr_agt_bic8', display_name='Creditor Agent BIC8', data_type=DataType.STRING, comment='CreditorAgent.BIC (8-char)'),

            # Scalar evidence for routing novelty (no arrays)
            Field(identifier='txn_has_new_intr_bic', display_name='Txn Has New Intermediary BIC', data_type=DataType.BOOLEAN, comment='True if this transaction uses any intermediary BIC newly introduced this month for the customer'),
            Field(identifier='num_new_intr_bics_in_trx', display_name='Num New Intermediary BICs in Txn', data_type=DataType.LONG, comment='Count of “new this month” intermediary BICs present in this transaction'),
            Field(identifier='first_new_intr_bic8', display_name='First-Seen Intermediary BIC8', data_type=DataType.STRING, comment='BIC8 marked on the first transaction where each new intermediary appears this month (else NULL)'),

            # Parties (for many-to-one / pipe analyses)
            Field(identifier='dbtr_id', display_name='Debtor Party ID', data_type=DataType.STRING, comment='Originator (customer) identifier'),
            Field(identifier='dbtr_name', display_name='Debtor Party Name', data_type=DataType.STRING, comment='Originator (customer) name'),
            Field(identifier='cdtr_id', display_name='Creditor Party ID', data_type=DataType.STRING, comment='Beneficiary (customer) identifier'),
            Field(identifier='cdtr_name', display_name='Creditor Party Name', data_type=DataType.STRING, comment='Beneficiary (customer) name'),
            Field(identifier='originator_is_corporate', display_name='Originator Is Corporate', data_type=DataType.BOOLEAN, comment='True if originator is corporate'),
            Field(identifier='beneficiary_is_corporate', display_name='Beneficiary Is Corporate', data_type=DataType.BOOLEAN, comment='True if beneficiary is corporate'),

            # Flags supporting triggers
            Field(identifier='is_round_amount', display_name='Is Round Amount', data_type=DataType.BOOLEAN, comment='Amount is a round thousand (corporate bias)'),
            Field(identifier='is_new_currency', display_name='Is Rare Currency', data_type=DataType.BOOLEAN, comment='Currency from rare set; aggregator computes “new currency” via 12m lookback'),
            Field(identifier='touches_high_risk_jurisdiction', display_name='Touches High-Risk Jurisdiction', data_type=DataType.BOOLEAN, comment='True if creditor country is in the high-risk list'),
        ]
    )


def entities() -> List[DataSet]:
    return [transactions_dataset()]

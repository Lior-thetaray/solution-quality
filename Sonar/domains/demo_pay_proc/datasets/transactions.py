from typing import List

from thetaray.api.solution import DataSet, Field, DataType, IngestionMode


def transactions_dataset():
    return DataSet(
        identifier='demo_pay_proc_transactions',
        display_name='Payment Processor Transactions',
        ingestion_mode=IngestionMode.APPEND,
        publish=True,
        primary_key=['transaction_id'],
        num_of_partitions=1,
        num_of_buckets=1,
        data_permission="dpv:demo_pay_proc",
        occurred_on_field='transaction_timestamp',
        field_list=[
            Field(identifier='transaction_id', display_name='Transaction ID', data_type=DataType.STRING, comment='Unique identifier for the transaction'),
            Field(identifier='account_id', display_name='Account ID', data_type=DataType.STRING, comment='Unique account ID associated with the merchant'),
            Field(identifier='customer_id', display_name='Customer ID', data_type=DataType.STRING, comment='Unique merchant/customer identifier'),
            Field(identifier='customer_name', display_name='Customer Name', data_type=DataType.STRING, comment='Legal name of the merchant'),
            Field(identifier='merchant_category', display_name='Merchant Category', data_type=DataType.STRING, comment='Type of business activity (Retail, Hospitality, etc.)'),
            Field(identifier='transaction_timestamp', display_name='Transaction Timestamp', data_type=DataType.TIMESTAMP, comment='Date and time when the transaction occurred'),
            Field(identifier='transaction_date', display_name='Transaction Date', data_type=DataType.TIMESTAMP, comment='Date when the transaction occurred'),
            Field(identifier='year_month', display_name='Year-Month', data_type=DataType.TIMESTAMP, comment='Transaction year-month format (YYYY-MM)'),
            Field(identifier='amount_domestic_currency', display_name='Amount in Domestic Currency', data_type=DataType.DOUBLE, comment='Transaction amount converted to local (USD)'),
            Field(identifier='amount_original_currency', display_name='Amount in Foreign Currency', data_type=DataType.DOUBLE, comment='Original amount if currency differs from domestic'),
            Field(identifier='currency', display_name='Currency Code', data_type=DataType.STRING, comment='Currency used for the transaction (ISO-3 or synthetic rare)'),
            Field(identifier='direction', display_name='Direction', data_type=DataType.STRING, comment='Transaction flow: IN (credit) or OUT (debit)'),
            Field(identifier='terminal_id', display_name='Terminal ID', data_type=DataType.STRING, comment='Identifier for the POS terminal or acceptance device'),
            Field(identifier='transaction_type', display_name='Transaction Type', data_type=DataType.STRING, comment='Type of transaction: payment or refund'),
            Field(identifier='transaction_description', display_name='Transaction Description', data_type=DataType.STRING, comment='Short description: Sale transaction or Refund'),
            Field(identifier='transaction_channel', display_name='Transaction Channel', data_type=DataType.STRING, comment='Channel where the transaction occurred (POS, E-commerce, Mobile)'),
            Field(identifier='ip_address', display_name='IP Address', data_type=DataType.STRING, comment='IP address associated with the transaction'),
            Field(identifier='counterparty_id', display_name='Counterparty ID', data_type=DataType.STRING, comment='Unique ID of the counterparty involved in the transaction'),
            Field(identifier='counterparty_name', display_name='Counterparty Name', data_type=DataType.STRING, comment='Name of the counterparty'),
            Field(identifier='counterparty_country_code', display_name='Counterparty Country Code', data_type=DataType.STRING, comment='ISO-2 code of counterparty country'),
            Field(identifier='counterparty_country_name', display_name='Counterparty Country Name', data_type=DataType.STRING, comment='Full name of counterparty country'),
            Field(identifier='counterparty_country_risk', display_name='Counterparty Country Risk', data_type=DataType.STRING, comment='AML risk classification: Low, Moderate, High'),
            Field(identifier='is_domestic', display_name='Is Domestic', data_type=DataType.BOOLEAN, comment='True if transaction occurs within merchant’s country'),
            Field(identifier='is_reversal', display_name='Is Reversal', data_type=DataType.BOOLEAN, comment='True if transaction is a reversal/refund'),
            Field(identifier='is_rare_currency', display_name='Is Rare Currency', data_type=DataType.BOOLEAN, comment='True if currency is outside top-20 most common set'),
        ]
    )


def entities() -> List[DataSet]:
    return [transactions_dataset()]

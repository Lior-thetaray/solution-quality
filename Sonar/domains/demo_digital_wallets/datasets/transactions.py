from thetaray.api.solution import DataSet, Field, DataType, IngestionMode

def transactions_dataset():
    """
    Schema EXACTLY matching the generator output:

    Columns:
      transaction_id (STRING)
      client_id (STRING)
      client_name (STRING)
      counterparty_id (STRING)
      counterparty_name (STRING)
      transaction_datetime (TIMESTAMP)
      amount (DOUBLE)
      currency (STRING)
      transaction_type (STRING)
      direction (STRING)
      payment_method (STRING)
      country_origin (STRING)
      country_destination (STRING)
      is_reversal (BOOLEAN)
      free_text (STRING)
      merchant_id (STRING)      # allows None/NULL at ingestion
      merchant_category (STRING)
    """
    return DataSet(
        identifier='demo_digital_wallets_transactions',
        display_name='Digital Wallets Individual Transactions',
        ingestion_mode=IngestionMode.APPEND,
        publish=True,
        primary_key=['transaction_id'],
        occurred_on_field='transaction_datetime',   
        num_of_partitions=1,
        num_of_buckets=1,
        data_permission="dpv:demo_digital_wallets",
        field_list=[
            Field(
                identifier='transaction_id',
                display_name='Transaction ID',
                data_type=DataType.STRING,
                comment='Primary key'
            ),
            Field(
                identifier='client_id',
                display_name='Client ID',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='client_name',
                display_name='Client Name',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='counterparty_id',
                display_name='Counterparty ID',
                data_type=DataType.STRING,
                comment='Customer or external entity ID'
            ),
            Field(
                identifier='counterparty_name',
                display_name='Counterparty Name',
                data_type=DataType.STRING,
                comment='Name or phone if external'
            ),
            Field(
                identifier='transaction_datetime',
                display_name='Transaction Datetime',
                data_type=DataType.TIMESTAMP,
                comment='Format: yyyy-MM-dd HH:mm:ss'
            ),
            Field(
                identifier='amount',
                display_name='Transaction Amount',
                data_type=DataType.DOUBLE,
                comment='Amount in original currency'
            ),
            Field(
                identifier='currency',
                display_name='Currency',
                data_type=DataType.STRING,
                comment='ISO-4217 (3-letter code)'
            ),
            Field(
                identifier='transaction_type',
                display_name='Transaction Type',
                data_type=DataType.STRING,
                comment='payment, transfer_in, transfer_out, crypto_purchase, crypto_sale'
            ),
            Field(
                identifier='direction',
                display_name='Direction',
                data_type=DataType.STRING,
                comment='inflow or outflow from client perspective'
            ),
            Field(
                identifier='payment_method',
                display_name='Payment Method',
                data_type=DataType.STRING,
                comment='wallet_balance, credit_card, bank_transfer, pix, crypto_wallet'
            ),
            Field(
                identifier='country_origin',
                display_name='Country Origin',
                data_type=DataType.STRING,
                comment='ISO-3166 (2-letter code)'
            ),
            Field(
                identifier='country_destination',
                display_name='Country Destination',
                data_type=DataType.STRING,
                comment='ISO-3166 (2-letter code)'
            ),
            Field(
                identifier='is_reversal',
                display_name='Is Reversal',
                data_type=DataType.BOOLEAN,
                comment='True if refund/reversal'
            ),
            Field(
                identifier='free_text',
                display_name='Free Text',
                data_type=DataType.STRING,
                comment='Optional user description (e.g., Dinner, Gift)'
            ),
            Field(
                identifier='merchant_id',
                display_name='Merchant ID',
                data_type=DataType.STRING,
                comment='If applicable (nullable)'
            ),
            Field(
                identifier='merchant_category',
                display_name='Merchant Category',
                data_type=DataType.STRING,
                comment='e.g., Grocery, Electronics, Crypto Exchange'
            ),
        ],
    )

def entities():
    return [transactions_dataset()]

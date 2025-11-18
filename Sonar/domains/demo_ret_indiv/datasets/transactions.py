from thetaray.api.solution import DataSet, Field, DataType, IngestionMode


def transactions_dataset():
    return DataSet(
        identifier='demo_ret_indiv_transactions',
        display_name='Retail Individual Transactions',
        ingestion_mode=IngestionMode.APPEND,
        publish=True,
        primary_key=['transaction_id'],
        occurred_on_field='transaction_timestamp',
        num_of_partitions=1,
        num_of_buckets=1,
        data_permission="dpv:demo_ret_indiv",
        field_list=[
            Field(
                identifier='transaction_id',
                display_name='Transaction ID',
                data_type=DataType.STRING,
                comment='Primary key'
            ),
            Field(
                identifier='customer_id',
                display_name='Customer ID',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='customer_name',
                display_name='Customer Name',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='account_id',
                display_name='Account ID',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='transaction_timestamp',
                display_name='Transaction Timestamp',
                data_type=DataType.TIMESTAMP,
                comment='Format: yyyy-MM-dd HH:mm:ss'
            ),
            Field(
                identifier='transaction_type_code',
                display_name='Transaction Type Code',
                data_type=DataType.STRING,
                comment='Code'
            ),
            Field(
                identifier='transaction_type_description',
                display_name='Transaction Type Description',
                data_type=DataType.STRING,
                comment='e.g., Cash, Check, ATM, Wire Transfer, FX, etc.'
            ),
            Field(
                identifier='channel',
                display_name='Channel',
                data_type=DataType.STRING,
                comment='e.g., teller, internet, e-wallet, app'
            ),
            Field(
                identifier='original_trx_amount',
                display_name='Original Transaction Amount',
                data_type=DataType.DOUBLE,
                comment='Amount in original currency'
            ),
            Field(
                identifier='original_trx_currency',
                display_name='Original Transaction Currency',
                data_type=DataType.STRING,
                comment='ISO-4217 (3-letter code)'
            ),
            Field(
                identifier='reference_trx_amount',
                display_name='Reference Transaction Amount',
                data_type=DataType.DOUBLE,
                comment='Amount converted to reference currency'
            ),
            Field(
                identifier='normalized_country_amount',
                display_name='Normalized Country Amount',
                data_type=DataType.DOUBLE,
                comment='Normalized to local currency'
            ),
            Field(
                identifier='counterparty_customer_name',
                display_name='Counterparty Customer Name',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='counterparty_account',
                display_name='Counterparty Account',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='counterparty_contract',
                display_name='Counterparty Contract',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='counterparty_country',
                display_name='Counterparty Country',
                data_type=DataType.STRING,
                comment='ISO-3166 (2-letter code)'
            ),
            Field(
                identifier='counterparty_country_risk',
                display_name='Counterparty Country Risk',
                data_type=DataType.STRING,
                comment='Risk mapping from DH countries'
            ),
            Field(
                identifier='internal',
                display_name='Internal Transaction',
                data_type=DataType.BOOLEAN,
                comment='1 if between bank customers, 0 if external'
            ),
            Field(
                identifier='in_out',
                display_name='Direction',
                data_type=DataType.STRING,
                comment='IN if incoming, OUT if outgoing'
            ),
            Field(
                identifier='atm_id',
                display_name='ATM ID',
                data_type=DataType.STRING,
                comment='If ATM transaction'
            ),
            Field(
                identifier='branch_id',
                display_name='Branch ID',
                data_type=DataType.STRING,
                comment='If in-branch transaction'
            ),
            Field(
                identifier='transaction_description',
                display_name='Transaction Description',
                data_type=DataType.STRING,
                comment='Free-text description'
            ),
            Field(
                identifier='banker_id',
                display_name='Banker ID',
                data_type=DataType.STRING,
                comment='If available'
            ),
        ],
    )


def entities():
    return [transactions_dataset()]

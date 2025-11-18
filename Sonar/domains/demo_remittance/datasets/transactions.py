from thetaray.api.solution import DataSet, Field, DataType, IngestionMode


def transactions_dataset():
    return DataSet(
        identifier='demo_remittance_transactions',
        display_name='Retail Individual Transactions',
        ingestion_mode=IngestionMode.APPEND,
        publish=True,
        primary_key=['transaction_id'],
        occurred_on_field='transaction_timestamp',
        num_of_partitions=1,
        num_of_buckets=1,
        data_permission="dpv:demo_remittance",
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
                identifier='counterparty_id',
                display_name='Counterparty ID',
                data_type=DataType.STRING,
                comment=None
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
                identifier='transaction_timestamp',
                display_name='Transaction Timestamp',
                data_type=DataType.TIMESTAMP,
                comment='Format: yyyy-MM-dd HH:mm:ss'
            ),
            Field(
                identifier='channel',
                display_name='Channel',
                data_type=DataType.STRING,
                comment='e.g., teller, internet, e-wallet, app'
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
                identifier='destination_country_code',
                display_name='Destination Country Code',
                data_type=DataType.STRING,
                comment='ISO-3166 (2-letter code)'
            ),
            Field(
                identifier='origin_country_code',
                display_name='Origin Country Code',
                data_type=DataType.STRING,
                comment='ISO-3166 (2-letter code)'
            ),
            Field(
                identifier='in_out',
                display_name='Direction',
                data_type=DataType.STRING,
                comment='IN if incoming, OUT if outgoing'
            )


        ],
    )


def entities():
    return [transactions_dataset()]

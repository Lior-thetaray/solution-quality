from thetaray.api.solution import DataSet, Field, DataType, IngestionMode

def transactions_dataset():

    return DataSet(
        identifier='demo_merchant_transactions',
        display_name='Merchant Acquiring - Transactions',
        ingestion_mode=IngestionMode.APPEND,
        publish=True,
        primary_key=['transaction_id'],
        occurred_on_field='transaction_datetime',   
        num_of_partitions=1,
        num_of_buckets=1,
        data_permission="dpv:demo_merchant",
        field_list=[
            Field(
                identifier='transaction_id',
                display_name='Transaction ID',
                data_type=DataType.STRING,
                comment='Primary key'
            ),
            Field(
                identifier='merchant_id',
                display_name='Merchant ID',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='merchant_name',
                display_name='Merchant Name',
                data_type=DataType.STRING,
                comment=None
            ),
            Field(
                identifier='mcc',
                display_name='MCC',
                data_type=DataType.STRING,
                comment='Merchant Category Code'
            ),
            Field(
                identifier='mcc_description',
                display_name='MCC Description',
                data_type=DataType.STRING,
                comment='Category description'
            ),
            Field(
                identifier='state',
                display_name='State',
                data_type=DataType.STRING,
                comment='State or region of transaction'
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
                identifier='channel',
                display_name='Channel',
                data_type=DataType.STRING,
                comment='POS, E-commerce, Mobile, etc.'
            ),
            Field(
                identifier='card_brand',
                display_name='Card Brand',
                data_type=DataType.STRING,
                comment='e.g., Visa, Mastercard, Amex'
            ),
            Field(
                identifier='is_refund',
                display_name='Is Refund',
                data_type=DataType.BOOLEAN,
                comment='True if refund'
            ),
            Field(
                identifier='is_chargeback',
                display_name='Is Chargeback',
                data_type=DataType.BOOLEAN,
                comment='True if chargeback'
            ),
            Field(
                identifier='customer_id',
                display_name='Customer ID',
                data_type=DataType.STRING,
                comment='Customer identifier'
            ),
        ],
    )

def entities():
    return [transactions_dataset()]

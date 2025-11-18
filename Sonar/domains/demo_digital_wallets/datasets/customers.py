from thetaray.api.solution import DataSet, Field, DataType, IngestionMode

def customers_dataset():
    return DataSet(
        identifier='demo_digital_wallets_customers',
        display_name='Digital Wallets Individual Customers',
        ingestion_mode=IngestionMode.UPDATE,
        publish=True,
        primary_key=['client_id'],  
        num_of_partitions=1,
        num_of_buckets=1,
        data_permission="dpv:demo_digital_wallets",
        field_list=[
           
            Field(identifier='client_id',  display_name='Client ID',  
                  data_type=DataType.STRING),
            Field(identifier='client_name',display_name='Client Name',
                  data_type=DataType.STRING),

            
            Field(identifier='date_of_birth',           
                  display_name='Date of Birth',             
                  data_type=DataType.TIMESTAMP, 
                  comment='Format: yyyy-MM-dd'),
            Field(identifier='country_of_birth',
                  display_name='Country of Birth',
                  data_type=DataType.STRING),
            Field(identifier='citizenship_countries',
                  display_name='Citizenship Countries',
                  data_type=DataType.STRING),

           
            Field(identifier='country_of_residence_code',
                  display_name='Country of Residence Code',
                  data_type=DataType.STRING, 
                  comment='ISO-3166 (2-letter code)'),
            Field(identifier='country_of_residence',
                  display_name='Country of Residence',
                  data_type=DataType.STRING),
            Field(identifier='address',
                  display_name='Address',
                  data_type=DataType.STRING),
            Field(identifier='phone_number',
                  display_name='Phone Number',
                  data_type=DataType.STRING),
            Field(identifier='email',
                  display_name='Email',
                  data_type=DataType.STRING),

            
            Field(identifier='occupation',
                  display_name='Occupation',
                  data_type=DataType.STRING),
            Field(identifier='primary_source_of_income',
                  display_name='Primary Source Of Income',
                  data_type=DataType.STRING),
            Field(identifier='estimated_annual_income_eur',
                  display_name='Estimated Annual Income (EUR)',
                  data_type=DataType.DOUBLE),

            
            Field(identifier='risk_rating',
                  display_name='Risk Rating',
                  data_type=DataType.LONG),
            Field(identifier='is_pep',
                  display_name='PEP',
                  data_type=DataType.BOOLEAN, 
                  comment='Politically exposed person flag'),
            Field(identifier='is_sanctioned',
                  display_name='Sanctioned',
                  data_type=DataType.BOOLEAN, 
                  comment='If the person is sanctioned'),
            Field(identifier='high_risk_country_exposure',  
                  display_name='High Risk Country Exposure',  
                  data_type=DataType.BOOLEAN),

            
            Field(identifier='daily_wallet_topup_limit_eur',  
                  display_name='Daily Wallet Top-up Limit (EUR)',
                  data_type=DataType.DOUBLE),
            Field(identifier='monthly_wallet_limit_eur',       
                  display_name='Monthly Wallet Limit (EUR)',   
                  data_type=DataType.DOUBLE),

           
            Field(identifier='crypto_affinity',            
                  display_name='Crypto Affinity',            
                  data_type=DataType.BOOLEAN),
            Field(identifier='intl_transfer_tolerance',    
                  display_name='International Transfer Tolerance', 
                  data_type=DataType.BOOLEAN),
            Field(identifier='rapid_spend_tolerance',     
                  display_name='Rapid Spend Tolerance',    
                  data_type=DataType.BOOLEAN),

           
            Field(identifier='customer_effective_date', 
                  display_name='Customer Effective Date', 
                  data_type=DataType.TIMESTAMP, 
                  comment='Format: yyyy-MM-dd'),
            Field(identifier='kyc_last_review_date',  
                  display_name='KYC Last Review Date',  
                  data_type=DataType.TIMESTAMP, 
                  comment='Format: yyyy-MM-dd'),
            Field(identifier='segment_type',         
                  display_name='Segment Type',      
                  data_type=DataType.STRING, comment='Code'),
            Field(identifier='segment_type_description',
                  display_name='Segment Type Description', 
                  data_type=DataType.STRING, 
                  comment='e.g., Personal – Digital Wallet'),
            Field(identifier='sars_flag',
                  display_name='Sars Flag',      
                  data_type=DataType.BOOLEAN),
        ],
    )

def entities():
    return [customers_dataset()]

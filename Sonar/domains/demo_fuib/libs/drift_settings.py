from datetime import datetime

from thetaray.common.data_environment import DataEnvironment

# General parameters
# **Define the following parameters:**

# 0. <u>General</u>: data environment + execution date. Using for reading the data with the provided execution dates. 
# 1. <u>Datasets</u>: parameters for data reading.
#   Fill the relevant dataset names of: Transactions DF, Final DF (before analysis), Anomalies DF.
# 2. <u>Relevant Columns</u>: parameters for columns definitions.
# 3. <u>Static parameters</u>: define different parameters that will be used in different functions.
# 4. <u>Analysis settings</u>: define the historical period and the current period.


# 0. General Settings
# -----------
data_evn = 
from_job_ts = datetime(1970, 1, 1)
to_job_ts = datetime(1970, 1, 1)

# 1. Datasets
# -----------
EVALUATION_FLOW = ""
LAST_DF_NAME = ""
TRANSACTIONS_DF_NAME = ""

# 2. Relevant Columns
# -------------------
DATE_ANALYSIS_COL = ""  # analysis dataframe
DATE_COL = ""  # transaction dataframe
ENTITIES_TRXDF_COLS = []
ENTITIES_AGGDF_COLS = []
ALGO_STEP = ""
AMOUNT_COL = ""

# 3. Static parameters
# --------------------
FUSION_THRESHOLD = 0.5
LIST_ADDITIONAL_FEATURE = []  # features that were not use for the analysis
NUM_OF_BINS = 10
SAMPLE_SIZE = 0  # 0 - for using all data, else - using the SAMPLE_SIZE for CSI calculation
AGG_TYPE = "month"

# 4. Analysis settings
# -----------------
start_period_train = 
end_period_train = 

# 5. Tests Settings
# -----------------
# ### Tests Selection Parameters
# - In the first part please select the tests you want to present in the notebook. (True/False)
# - In the second part please select the failing tests out of the following list:
#   **['ANOMALY_PERCENTAGE', 'IQR', 'CSI_FEATURES_TEST','TRIGGER_FEATURES','CSI_ANOMALY_PERCENT']**
# Raw data
RAW_DATA_DISTRIBUTION = True
RAW_DATA_AMOUNT_DISTRIBUTION = True
# features
GENERAL_FEATURES_DISTRIBUTION = True
FEATURES_DISTRIBUTION_VISUALIZATION = True
CSI_FEATURES_TEST = True
# anomalies
ANOMALY_PERCENTAGE = True
IQR_ALGO_SCORE = True
TRIGGER_FEATURES_TEST = True
CSI_ANOMALY_PERCENT_TEST = True

# ## PART 2 ###

# tests threshold
tests_thresholds = {
    "ANOMALY_PERCENTAGE": 5,  # The threshold sets the maximum zscore of the current period anomaly percentage
                              # compared to the training period
    "IQR_ALGO_SCORE": 0.1,  # The threshold sets the maximum gap between the difference |Q3-Q1| in the training period
                            # compared to the current period.
    "CSI_FEATURES_TEST": 0.25,  # The threshold sets the maximum percentage of significantly changed features
                                # (above the CSI threshold)
    "MAX_CSI_FEATURE_CHANGE_TEST": 0.5,  # The threshold sets the maximum CSI score
    "TRIGGER_FEATURES": 0.25,  # The threshold sets the maximum percentage of significantly changed features occurrence
                               # (according to zscore test)
    "CSI_ANOMALY_PERCENT": None  # If the CSI anomaly score distribution test failed
}

FAILING_TESTS = tests_thresholds.keys() #TODO - CHANGE

CSI_THRESHOLD = 0.25  # used for csi features test + csi anomaly percentage test
ALPHA = 0.05

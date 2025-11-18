import mlflow
import numpy as np
from scipy.stats import norm
from thetaray.api.dataset import dataset_functions
from thetaray.api.drift import send_drift_notification
from thetaray.api.evaluation import load_evaluated_activities
from thetaray.api.evaluation import evaluate_step
from thetaray.api.mlflow.adapter import get_run_id
from thetaray.api.metric import DriftMetricPublisher
import pyspark.sql.functions as f
from thetaray.common.data_environment import DataEnvironment
from pyspark.sql.functions import udf
from pyspark.sql.types import *
import pandas as pd
import datetime
import matplotlib.pyplot as plt; plt.rcdefaults()
from matplotlib.ticker import MultipleLocator, MaxNLocator
from collections import OrderedDict

from pyspark.ml.feature import Bucketizer, QuantileDiscretizer

from domestic.libs.drift_settings import *

# failing tests
FAILING_TESTS_RESULTS = {}
DATE_AGG_LEVEL = 'date_agg_level'
metrics = {'Test': [], 'Result': [], 'Value': [], 'Threshold':[]}
metrics_output = {}
### Perperation Functions
def split_train_current(context,dataset_name,date_col,AGG_TYPE, entities_columns):
    reference_data = dataset_functions.read(context, dataset_name,data_environment = data_evn, from_job_ts=from_job_ts)
    reference_data = create_agg_level(reference_data, date_col,AGG_TYPE)
    reference_data = reference_data.where((f.col(date_col)>=start_period_train) & (f.col(date_col)<=end_period_train))
    reference_data = reference_data.sort([date_col] + entities_columns)

    new_batch_data = dataset_functions.read(context, dataset_name, data_environment=data_evn) 
    new_batch_data = create_agg_level(new_batch_data, date_col,AGG_TYPE)

    return reference_data, new_batch_data

def cast_bulk_list(df, col_list,type):
    for column_name in col_list:
        if column_name in df.columns:
            df = df.withColumn(column_name,f.col(column_name).cast(type))
    return df

def date_agg(df,date_col,agg_level):
    '''format date aggregaition column to dataframe from existing date column.
    input:  spark Dataframe,
            name of column to convert to date column
            agg_level - 'month', 'week' or 'day' for monthly, weekly or daily aggregation
    return: New spark DataFrame
    '''
    if agg_level == "month":
        if 'year_month' not in df.columns:
            df = df.withColumn('year_month', f.concat(f.year(f.col(date_col)), f.lit('_'), f.lpad(f.month(f.col(date_col)), 2, '0')))
        return df, 'year_month'
    elif agg_level == "week":
        if 'week_date' not in df.columns:
            df = df.withColumn("week", f.date_trunc('week', f.col(date_col))).withColumn("week_date",f.concat(f.year(f.col("week")), f.lit('-'), f.lpad(f.month(f.col("week")),2,'0'), f.lit('-'), f.lpad(f.dayofmonth(f.col("week")),2,'0')))
            return df, "week_date"
    elif agg_level == "day":
        return df, date_col
    return df, ""

def create_agg_level(df,date_col,AGG_TYPE):
    const_date = f.lit(datetime(1970,1,1))
    if AGG_TYPE == "month":
        df = df.withColumn('date_agg_level', f.round(f.months_between(f.trunc(f.col(date_col), "month"), const_date)))
    elif AGG_TYPE == "week":
        df = df.withColumn('date_agg_level', f.floor((f.datediff(f.col(date_col), const_date)) / 7).cast(DoubleType()))
    else:
        df = df.withColumn('date_agg_level', f.datediff(f.col(date_col), const_date))
    df = df.withColumn('diff_in_days', f.datediff(f.col(date_col), const_date))
    return df
### Features Tests Functions

def agg_dist(df,column_name,group_by_list):
    """
    ### Calculate statistics of a column
    ### return df with one row
    """
    df = df.withColumn(column_name,f.col(column_name).cast(DoubleType()))
    percentile_10 = f.round(f.expr('percentile_approx('+column_name+',0.1)'),2)
    percentile_20 = f.round(f.expr('percentile_approx('+column_name+',0.2)'),2)
    percentile_25 = f.round(f.expr('percentile_approx('+column_name+',0.25)'),2)
    percentile_30 = f.round(f.expr('percentile_approx('+column_name+',0.3)'),2)
    percentile_40 = f.round(f.expr('percentile_approx('+column_name+',0.4)'),2)
    percentile_50 = f.round(f.expr('percentile_approx('+column_name+',0.5)'),2)
    percentile_60 = f.round(f.expr('percentile_approx('+column_name+',0.6)'),2)
    percentile_70 = f.round(f.expr('percentile_approx('+column_name+',0.7)'),2)
    percentile_75 = f.round(f.expr('percentile_approx('+column_name+',0.75)'),2)
    percentile_80 = f.round(f.expr('percentile_approx('+column_name+',0.8)'),2)
    percentile_90 = f.round(f.expr('percentile_approx('+column_name+',0.9)'),2)
    percentile_95 = f.round(f.expr('percentile_approx('+column_name+',0.95)'),2)
    percentile_99 = f.round(f.expr('percentile_approx('+column_name+',0.99)'),2)
    df = df.withColumn("positive_ind",f.when(f.col(column_name)>0,1).otherwise(0))
    agg_df = df.groupBy(group_by_list).agg(f.count("*").alias("count_all"),
                                           f.sum("positive_ind").alias("count_positive"),
                                           f.min(column_name).alias("min"), percentile_10.alias("perc_10"), percentile_20.alias("perc_20"),
    									   percentile_25.alias("perc_25"), percentile_30.alias("perc_30"), percentile_40.alias("perc_40"),
    									   percentile_50.alias("perc_50"), percentile_60.alias("perc_60"), percentile_70.alias("perc_70"),
    									   percentile_75.alias("perc_75"), percentile_80.alias("perc_80"), percentile_90.alias("perc_90"),
    									   percentile_95.alias("perc_95"), percentile_99.alias("perc_99"), f.round(f.max(column_name),2).alias("max"),
    									   f.round(f.avg(column_name),2).alias("avg"),
    									   f.round(f.stddev(column_name),2).alias("stddev"))
    agg_df = agg_df.withColumn("positive_prop",f.round(f.col("count_positive")/f.col("count_all"),2))
    agg_df = agg_df.withColumn("IQR",f.round(f.col("perc_75")-f.col("perc_25"),2))
    agg_df = agg_df.withColumn("range",f.col("max")-f.col("min"))
    agg_df = agg_df.withColumn("feature_name",f.lit(column_name))
    
    select_cols = ["feature_name"] + group_by_list+\
                   ["count_positive","count_all","positive_prop","min","perc_10","perc_20",
                   "perc_25","perc_30","perc_40","perc_50","perc_60","perc_70","perc_75","perc_80",
                   "perc_90","perc_95","perc_99","max","avg","stddev","IQR","range"]
    
    return agg_df.select(select_cols) 

def barchart_compare(df_train, df_test, buckColumn, num_of_bins = 20):
    """
    ### Draw histograms of the distributions of the feature
    """
    try:
        df = df_train.union(df_test)
        max_value = df.agg(f.max(f.col(buckColumn))).collect()[0][0]
        min_value = df.agg(f.min(f.col(buckColumn))).collect()[0][0]
        splits = [i for i in np.arange(min_value, max_value, (max_value-min_value)/num_of_bins)]   + [float("inf")]

        splits_dict = {i:splits[i] for i in range(len(splits))}
        bucketizer = Bucketizer(splits=splits, inputCol=buckColumn, outputCol="buck_" + buckColumn)

        train_buck = bucketizer.transform(df_train)
        train_buck = train_buck.replace(to_replace=splits_dict, subset=["buck_" + buckColumn])
        test_buck = bucketizer.transform(df_test)
        test_buck = test_buck.replace(to_replace=splits_dict, subset=["buck_" + buckColumn])

        # create histogram for these buckets values
        train_buck_gr = train_buck.groupBy("buck_" + buckColumn).count().withColumn("rate_train", f.col("count")/train_buck.count() )\
                                   .select("buck_" + buckColumn,"rate_train" )
        test_buck_gr = test_buck.groupBy("buck_" + buckColumn).count().withColumn("rate_test", f.col("count")/test_buck.count() )\
                                    .select("buck_" + buckColumn,"rate_test" )

        # join the 2 dataframes
        train_buck_gr = train_buck_gr.join(test_buck_gr, on = "buck_" + buckColumn, how = "left" ).fillna(0).sort("buck_" + buckColumn)

        # create the plot
        hist_data = train_buck_gr.toPandas()
        x_pos = hist_data["buck_" + buckColumn].round(3)
        y_train = hist_data["rate_train"]
        y_test = hist_data["rate_test"]
        x = np.arange(len(x_pos))
        fig, ax = plt.subplots(figsize=(8,4))
        plt.bar(x-0.2, y_train, width= 0.3, label = "Train",  alpha = 0.5, color='royalblue')
        plt.bar(x+0.2, y_test, width= 0.3, label = "Current", alpha = 0.5, color='orange')
        plt.xticks(x, x_pos)
        plt.legend(loc="upper right")
        ax.xaxis.set_major_locator(MaxNLocator(5))

        plt.title(buckColumn.replace("_"," ").title())
        plt.show()
        return fig

    except ZeroDivisionError:
        print(f"Feature {buckColumn} has no values")
    except:
        print(f"Feature {buckColumn} is not shown due to problematic distribution - check feature values in simple statistics values")
    return None

def CSI_feature(spark, df_train, df_test,analysis_features, threshhold_PSI = 0.2, num_of_bins = 10,sample_size = 0):
    """
    Calculate CSI(Characteristic Stability Index) for every analysis feature for test period and 
    compare it to setup period
    
    Input:
          df - dataframe with data
          threshhold_PSI - threshold above which test considered failed
          num_of_bins - number of bins on which feture is divided
          sample_size - if > 0 for every feature df will be sampled tocalculate CSI

    Output:
           res_df - df where for every analisys feature there are mark whether there are significant change in it at test period 
    """
    feature_report_list = analysis_features + LIST_ADDITIONAL_FEATURE
    # create feature specific bins

    feature_no_bin = []
    first = True
    for TF in feature_report_list:
    # ignore 0 values
        if sample_size > 0:
            df_compare = df_train.filter(f.col(TF) != 0).sample(False, sample_size/df_train.count())
            df_actual = df_test.filter(f.col(TF) != 0).sample(False, sample_size/df_test.count())
        else:
            df_compare = df_train 
            df_actual = df_test
        df_compare_remove_zero = df_train.filter(f.col(TF) != 0)
        decile_list = df_compare_remove_zero.approxQuantile(TF,[i/(num_of_bins * 1.0) for i in range(1,num_of_bins)] ,0.0005)

        decile_list = list(OrderedDict.fromkeys(decile_list))
    
        decile_list = [float('-Inf')] + decile_list + [float('Inf')]  # create bins for bucketing
    
        output_col_name = "Buck_" + TF
        if len(decile_list) == 2:
           
            feature_no_bin.append(TF)
            continue
            
        # bucketizer creation according to the specific bins
        bucketizer = Bucketizer(splits=decile_list, inputCol=TF, outputCol=output_col_name)
        
        # if this is the first feature - create the df_buck dataframes
        if first:
            df_actual_buck = bucketizer.setHandleInvalid("keep").transform(df_actual)
            df_compare_buck = bucketizer.setHandleInvalid("keep").transform(df_compare)
            first = False
        else:
            df_actual_buck = bucketizer.setHandleInvalid("keep").transform(df_actual_buck)
            df_compare_buck = bucketizer.setHandleInvalid("keep").transform(df_compare_buck)

    actual_cnt = df_actual_buck.count()
    compare_cnt = df_compare_buck.count()

    res_dict = {}
    feature_report_list_with_bins = [i for i in feature_report_list if i not in feature_no_bin]

    # For every trigger feature with bins
    for TF in feature_report_list_with_bins:
        buck_TF = "Buck_" + TF

        # distribution of the feature in the train data
        actual_group = df_actual_buck.groupBy(buck_TF).count()
        actual_group = actual_group.withColumn("actual_distri", f.col("count")/actual_cnt)
        actual_group = actual_group.drop("count")

        # distribution of the feature in the test data
        compare_group = df_compare_buck.groupBy(buck_TF).count()
        compare_group = compare_group.withColumn("compare_distri", f.col("count")/compare_cnt)
        compare_group = compare_group.drop("count")

        # calculate the CSI value - (%Actual-%Expected)*ln(%Actual/%Expected)
        df_compare = actual_group.join(compare_group, buck_TF, "full")
        df_compare = df_compare.withColumn("differece_Acc_Compare", f.col("actual_distri") - f.col("compare_distri"))
        df_compare = df_compare.withColumn("ln_Acc_Compare", f.log(f.col("actual_distri")/f.col("compare_distri")))
        df_compare = df_compare.withColumn("PSI_temp", f.col('differece_Acc_Compare')* f.col('ln_Acc_Compare'))

        res_dict[TF]=df_compare.agg(f.sum("PSI_temp")).collect()[0][0]

    res_pd = pd.DataFrame(list(res_dict.items()),columns=['Feature','CSI'])
    res_df = spark.createDataFrame(res_pd)
    res_df = res_df.withColumn("Result", f.when(f.col("CSI") >= threshhold_PSI, "FAIL").otherwise("PASS"))

    return res_df

### Anomalies Tests Functions
def anomaly_percentage(data):
    data_anomaly_percent = data.groupBy(DATE_ANALYSIS_COL).agg(f.count("*").alias("total"), f.sum(f.when(f.col(ALGO_STEP + '_score')> FUSION_THRESHOLD, 1).otherwise(0)).alias("anom"))
    data_anomaly_percent = data_anomaly_percent.withColumn("ratio", f.col("anom")/f.col("total"))
    data_anomaly_percent = data_anomaly_percent.select(DATE_ANALYSIS_COL, "ratio").toPandas().set_index(DATE_ANALYSIS_COL, drop=True)
    return data_anomaly_percent

def add_trigger_features_columns(anomalies):
    """
    ###   Create dedicated columns for the top 5 trigger features 
    ###
    ### Input:
    ###       anomalies - dataframe with anomalies
    ###       
    """
    len_eval_col = len(ALGO_STEP)+1
    tf_prefix = "trigger_feature_"
    nums = range(1,6)
    for num in nums:
        anomalies = anomalies.withColumn(tf_prefix+str(num),f.lit(None))
        anomalies = anomalies.withColumn(tf_prefix+str(num)+"_rating",f.lit(None))

    for cols in anomalies.columns:
        if "rank" in cols:
            for num in nums:
                anomalies = anomalies.withColumn(tf_prefix+str(num),f.when(f.col(cols) == num,f.lit(cols[len_eval_col:-5])).otherwise(f.col(tf_prefix+str(num))))
                anomalies = anomalies.withColumn(tf_prefix+str(num)+"_rating",f.when(f.col(cols) == num,f.col(ALGO_STEP+"_"+cols[len_eval_col:-4]+"rating")/10000).otherwise(f.col(tf_prefix+str(num)+"_rating")))
    return anomalies

def tf_drift_by_month_help(anomalies,date_col_func, analysis_features, alpha = 0.025):
    # convert the anomalies dataframe - add columns of top 5 trigger features
    anomalies = add_trigger_features_columns(anomalies)

    df_month = anomalies.groupBy(DATE_AGG_LEVEL).agg(f.count(DATE_AGG_LEVEL).alias("Num_Anomalies"))

    # for each trigger feature calculate the number of appearences in every dateAggLevel-YearMonth-TriggerFeature
    df = anomalies
    TF1_month = df.groupBy(DATE_AGG_LEVEL,date_col_func, "trigger_feature_1").agg(f.count("*").alias("trigger_feature_1_cnt")).withColumnRenamed("trigger_feature_1", "trigger_feature")
    TF2_month = df.groupBy(DATE_AGG_LEVEL,date_col_func, "trigger_feature_2").agg(f.count("*").alias("trigger_feature_2_cnt")).withColumnRenamed("trigger_feature_2", "trigger_feature")
    TF3_month = df.groupBy(DATE_AGG_LEVEL,date_col_func, "trigger_feature_3").agg(f.count("*").alias("trigger_feature_3_cnt")).withColumnRenamed("trigger_feature_3", "trigger_feature")
    
    
    join_col = [DATE_AGG_LEVEL,date_col_func, "trigger_feature"]
    TF123_month = TF1_month.join(TF2_month, join_col, "full").join(TF3_month, join_col, "full")
    TF123_month = TF123_month.fillna(0, subset = ["trigger_feature_1_cnt", "trigger_feature_2_cnt", "trigger_feature_3_cnt"])
    
    #calculate the total number of appearences for all top 3 trigger features
    TF123_month = TF123_month.withColumn("trigger_feature_123_cnt", f.col('trigger_feature_1_cnt') + f.col('trigger_feature_2_cnt') + f.col('trigger_feature_3_cnt'))
    TF123_month = TF123_month.join(df_month.select(DATE_AGG_LEVEL, "Num_Anomalies"), DATE_AGG_LEVEL , "left")

    TF123_month = TF123_month.withColumn("trigger_feature_123_pct", f.col("trigger_feature_123_cnt")/f.col('Num_Anomalies'))
    # ,f.to_date(DATE_ANALYSIS_COL).alias(DATE_ANALYSIS_COL)
    TF123_month = TF123_month.select("trigger_feature", f.col(DATE_AGG_LEVEL).cast(IntegerType()),date_col_func, "Num_Anomalies", "trigger_feature_123_pct").orderBy("trigger_feature", f.desc(DATE_AGG_LEVEL)).fillna(0)
    return TF123_month

def tf_drift_by_month(reference_evaluated_activities,new_batch_evaluated_activities,date_col_func, analysis_features, alpha = 0.025):
    """
    This test computes the frequency of occurrence per period of every feature across the top 3 trigger features (most significant) for all anomalies.
    And check if there are significant change in frequency
    
    Input:
           df - dataframe with data
           analysis_features - list of anlaysis features
           alpha - significance level
    Output:
           df_res - dataframe with zscore of each trigger feature (for the number of occurrence) 
    """ 
    # calculate the average "trigger_feature_123_pct" score for each trigger feature in the train data
    tf_train = tf_drift_by_month_help(reference_evaluated_activities,date_col_func, analysis_features, alpha)
    tf_test = tf_drift_by_month_help(new_batch_evaluated_activities,date_col_func, analysis_features, alpha)
 
    tf_stat = tf_train.groupBy("trigger_feature").agg(f.avg("trigger_feature_123_pct").alias("avg"), f.stddev("trigger_feature_123_pct").alias("stddev"))
    
    tf_test_piv =  tf_test.groupBy("trigger_feature").pivot(date_col_func).agg(f.max("trigger_feature_123_pct").alias("percentage"))
    dateAgg_columns = [ c for c in tf_test_piv.columns if c!="trigger_feature"]
    
    # calculate the zscore for every feature in the test data
    tf_test_piv = tf_test_piv.join(tf_stat, ["trigger_feature"]).select("trigger_feature", *[f.round((f.col(c) - f.col("avg"))/f.col("stddev"), 2).alias("Zscore") for c in dateAgg_columns])
    # calculate the critical value and check if the critical value is smaller than the zscore.
    critical_value = norm.ppf(1 - alpha)
    
    df_res = tf_test_piv.select("*", *[f.when(f.abs(f.col("Zscore")) >= critical_value, "FAIL").otherwise("PASS").alias("Result") for c in dateAgg_columns]).fillna(0)
    
    tf_with_anomalies = tf_test.select("trigger_feature").distinct().rdd.flatMap(lambda x: x).collect()
    tf_no_anomalies = [i for i in analysis_features if i not in tf_with_anomalies]
    # if len(tf_no_anomalies) >0:
    #     print("There are no anomalies generated for the following Analysis Feature:")
    #     print(tf_no_anomalies)
    sort_columns =df_res.columns[1:]
    
    sort_columns.sort()
    
    return df_res.select("trigger_feature", *sort_columns),tf_no_anomalies 
def calculate_PSI(reference_evaluated_activities,new_batch_evaluated_activities, threshhold_PSI, num_of_bins = 10, score_col = "tr_score"):
    """
    ###   Calculate PSI for anomaly score 
    ###
    ### Input:
    ###       df - dataframe with data
    ###       threshhold_PSI - threshold above which test considered failed
    ###       num_of_bins - number of bins on which feture is divided
    ###       score_col - name of column with anomaly score
    """
    an_train, an_test  =  reference_evaluated_activities,new_batch_evaluated_activities

    # create feature specific bins
    decile_list = an_train.approxQuantile(score_col,[i/(num_of_bins * 1.0) for i in range(1,num_of_bins)] ,0.0005)
    
    decile_list = list(OrderedDict.fromkeys(decile_list))
    
    decile_list = [float('-Inf')] + decile_list + [float('Inf')]  # create bins for bucketing
    
    output_col = score_col + "_Buck"
    bucketizer = Bucketizer(splits=decile_list, inputCol=score_col, outputCol= output_col)
    an_train_buck = bucketizer.setHandleInvalid("keep").transform(an_train)
    an_test_buck = bucketizer.setHandleInvalid("keep").transform(an_test)

    train_cnt = an_train_buck.count()
    test_cnt = an_test_buck.count()
    
    # create the compare and actual values
    train_group = an_train_buck.groupBy(output_col).count().withColumn("compare_distri", f.col("count")/train_cnt)

    test_group = an_test_buck.groupBy(output_col).count().withColumn("actual_distri", f.col("count")/test_cnt)
    
    # calculate CSI
    df_compare = train_group.join(test_group, output_col, "full")
    df_compare = df_compare.withColumn("differece_Acc_Compare", f.col("actual_distri") - f.col("compare_distri"))
    df_compare = df_compare.withColumn("ln_Acc_Compare", f.log(f.col("actual_distri")/f.col("compare_distri")))
    df_compare = df_compare.withColumn("PSI_temp", f.col('differece_Acc_Compare')* f.col('ln_Acc_Compare'))

    curr_psi = df_compare.agg(f.sum("PSI_temp")).collect()[0][0]


    if curr_psi > threshhold_PSI:
        res = "FAIL"
    elif curr_psi is None:
        res = ""
    else:
        res = "PASS"
    

    return res, curr_psi, df_compare, train_group
